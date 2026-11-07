from configparser import ConfigParser
import datetime
import os

from django.http import HttpResponseNotFound, FileResponse
from django.shortcuts import render, HttpResponse, redirect
from django.urls import reverse
from django.views import generic
from django.utils.formats import localize
from django.utils.text import camel_case_to_spaces, capfirst
from django.contrib.auth import get_user_model
from django.contrib.auth import logout as auth_logout
from django.db.models import Q
from django.contrib.sites.models import Site
from django.views.decorators.http import require_safe
from rest_framework import status
from rest_framework.authtoken.models import Token

from collections import namedtuple

from . import models
from . import object_storage
from . import settings
from . import version
from . import vocab


def index(request):
    """
    Default view showing tables of the database objects, divided into Data Products, External Objects and Code Repo
    Releases.
    """
    data_products = models.Object.objects.filter(data_products__isnull=False)
    external_objects = models.DataProduct.objects.filter(external_object__isnull=False)
    code_repo_release = models.Object.objects.filter(code_repo_release__isnull=False)

    ObjectData = namedtuple("object", "name display_name count doc")
    object_data = [
        ObjectData(
            "objects", "Object", models.Object.objects.count(), models.Object.__doc__
        )
    ]
    issues = models.Issue.objects.all()
    ctx = {
        "objects": object_data,
        "issues": issues,
        "data_products": data_products,
        "external_objects": external_objects,
        "code_repo_release": code_repo_release,
        "remote_registry": settings.REMOTE_REGISTRY,
        "registry_version": version.get_version(),
    }
    return render(request, os.path.join("data_management", "index.html"), ctx)


def get_token(request):
    """
    Generate a new API access token for the User.
    """
    user_model = get_user_model()
    user_name = request.user.username
    user = user_model.objects.get_by_natural_key(user_name)
    Token.objects.filter(user=user).delete()
    token = Token.objects.get_or_create(user=user)
    return HttpResponse(
        '<input id="accesstoken" size=40 type="text" readonly value="%s" />' % token[0]
    )


def revoke_token(request):
    """
    Revoke an existing API access token for the User.
    """
    user_model = get_user_model()
    user_name = request.user.username
    user = user_model.objects.get_by_natural_key(user_name)
    Token.objects.filter(user=user).delete()
    return HttpResponse("Your token has been deleted")


class BaseListView(generic.ListView):
    """
    Base class for views for displaying a table of the database objects.
    """

    context_object_name = "objects"
    template_name = os.path.join("data_management", "object_list.html")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["model_name"] = self.model_name.lower()
        context["display_name"] = camel_case_to_spaces(self.model_name) + "s"
        return context


# The records a page lists besides its own fields, by model: (heading, relation)
RELATED_ROWS = {
    "Namespace": (("Data products", "data_products"),),
}


# A value on a record's page as (text, link) pairs, the link None where there is none:
# a record by its own page, an object component by the data products of its object
# (the name a reader knows it by), a web address by itself
def _shown(value):
    if isinstance(value, models.ObjectComponent):
        part = "" if value.whole_object else f" ({value.name})"
        products = value.object.data_products.all()
        if products:
            return [
                (
                    f"{p.namespace.name}:{p.name}@{p.version}{part}",
                    reverse("dataproduct", args=[p.pk]),
                )
                for p in products
            ]
    if type(value).__name__ in models.all_models:
        return [(str(value), reverse(type(value).__name__.lower(), args=[value.pk]))]
    if isinstance(value, datetime.datetime):
        return [(localize(value), None)]
    text = str(value)
    if text.startswith(("http://", "https://")):
        return [(text, text)]
    return [(text, None)]


# The rows of a record's page: each field that has a value, by its name, with the
# values shown, then the related records its model lists
def _rows(record):
    rows = []
    for field in record._meta.get_fields():
        if field.auto_created:
            continue
        if field.many_to_many:
            items = getattr(record, field.name).all()
        else:
            value = getattr(record, field.name)
            items = [] if value is None or value == "" else [value]
        values = [shown for item in items for shown in _shown(item)]
        if values:
            rows.append((capfirst(field.verbose_name), values))
    for heading, relation in RELATED_ROWS.get(type(record).__name__, ()):
        items = getattr(record, relation).all()
        values = [shown for item in items for shown in _shown(item)]
        if values:
            rows.append((heading, values))
    return rows


class BaseDetailView(generic.DetailView):
    """
    Base class for views for displaying details about a specific database object.

    A model with a template of its own is shown by it; any other by
    `record_detail.html`, which lists the record's fields and related records.
    """

    context_object_name = "object"

    def get_template_names(self):
        return [
            *super().get_template_names(),
            os.path.join("data_management", "record_detail.html"),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_name"] = self.model_name.lower() + "s"
        context["list_display_name"] = camel_case_to_spaces(self.model_name) + "s"
        context["model_name"] = self.model_name.lower()
        context["title"] = str(self.object)
        context["rows"] = _rows(self.object)
        return context


# Generate ListView and DetailView classes for each model that subclasses DataObject
for name, cls in models.all_models.items():
    data = {"model": cls, "model_name": name}
    globals()[name + "ListView"] = type(name + "ListView", (BaseListView,), data)
    globals()[name + "DetailView"] = type(name + "DetailView", (BaseDetailView,), data)


class ExternalObjectListView(generic.ListView):
    """
    View for displaying all ExternalObjects.
    """

    model = models.ExternalObject
    context_object_name = "externalobjects"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_name"] = "externalobjects"
        context["list_display_name"] = "External Objects"
        return context


# The address the registry serves a data product's file from
def data_product_download(data_product):
    return reverse(
        "get_data_product",
        kwargs={
            "namespace": data_product.namespace.name,
            "data_product_name": data_product.name,
            "version": data_product.version,
        },
    )


class ExternalObjectDetailView(generic.DetailView):
    """
    View for displaying details about a specific ExternalObject.

    Its `download` is the registry's own copy, through the first data product
    registered from it that has a file (a source is one file), or None where the
    registry holds no file of it.
    """

    model = models.ExternalObject

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_name"] = "externalobjects"
        context["list_display_name"] = "External Objects"
        products = self.object.data_products.order_by("pk")
        context["data_products"] = products
        held = products.filter(object__storage_location__isnull=False).first()
        context["download"] = None if held is None else data_product_download(held)
        return context


class DataProductListView(generic.ListView):
    """
    View for displaying all DataProducts.
    """

    model = models.DataProduct
    context_object_name = "dataproducts"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_name"] = "dataproducts"
        context["list_display_name"] = "Data Products"
        return context


# The size of file above which a data product's page offers its crate without the
# file first: a zip packing it is built and sent through the registry
PACK_LIMIT = 100 * 1024 * 1024


def file_size(location):
    """
    Return the size in bytes of a storage location's file - from the object store
    for one in this registry's own store, from the disk for a local file - or None
    where it cannot be found.
    """
    uri = location.full_uri()
    if uri.startswith("file://"):
        path = uri[len("file://"):]
        return os.path.getsize(path) if os.path.isfile(path) else None
    if settings.REMOTE_REGISTRY:
        domain = Site.objects.get_current().domain
        if domain in location.storage_root.root:
            return object_storage.size(location.path)
    return None


class DataProductDetailView(generic.DetailView):
    """
    View for displaying details about a specific DataProduct: what it is, who made
    it, where it came from, the run that made it and from what, the runs that used
    it, its provenance drawn and its report and RO-Crate offered.

    `?depth=all` draws and offers the whole history rather than one step back. The
    crate's zip is offered with the product's file and without it, with it chosen
    unless the file is larger than PACK_LIMIT; a product with no public file is
    offered without.
    """

    model = models.DataProduct

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["list_name"] = "dataproducts"
        context["list_display_name"] = "Data Products"
        product = self.object
        obj = product.object
        made_by = models.CodeRun.objects.filter(outputs__object=obj).distinct()
        inputs = []
        for run in made_by:
            for component in run.inputs.all():
                for shown in _shown(component):
                    if shown not in inputs:
                        inputs.append(shown)
        location = obj.storage_location
        size = None if location is None else file_size(location)
        whole = self.request.GET.get("depth") == "all"
        context.update(
            {
                "authors": obj.authors.all(),
                "licences": obj.licences.all(),
                "issues": models.Issue.objects.filter(
                    component_issues__object=obj
                ).distinct(),
                "made_by": made_by,
                "inputs": inputs,
                "used_by": models.CodeRun.objects.filter(inputs__object=obj).distinct(),
                "download": None if location is None else data_product_download(product),
                "size": size,
                "packable": location is not None and location.public,
                "pack_file": size is None or size <= PACK_LIMIT,
                "whole_history": whole,
                "depth": 100 if whole else 1,
                "report": reverse("prov_report", args=[product.pk]),
                "crate": reverse("data_product_ro_crate", args=[product.pk]),
            }
        )
        return context


class IssueListView(generic.ListView):
    """
    View for displaying all Issues.
    """

    model = models.Issue
    context_object_name = "issues"


class IssueDetailView(generic.DetailView):
    """
    View for displaying details about a specific Issue.
    """

    model = models.Issue


def docs(request, name):
    with open(os.path.join("docs", name)) as file:
        text = file.read()
    ctx = {"text": text}
    return render(request, os.path.join("data_management", "docs.html"), ctx)


def doc_index(request):
    with open(os.path.join("docs", "index.md")) as file:
        text = file.read()
    ctx = {"text": text}
    return render(request, os.path.join("data_management", "docs.html"), ctx)


@require_safe
def vocab_page(request):
    """
    The registry's own vocabulary: the terms its provenance reports and RO Crates use,
    each anchored by its name, so that the central registry's vocab/#<term> addresses
    resolve to their definitions.
    """
    ctx = {
        "classes": [term for term in vocab.TERMS if term.kind == vocab.CLASS],
        "properties": [term for term in vocab.TERMS if term.kind == vocab.PROPERTY],
    }
    return render(request, os.path.join("data_management", "vocab.html"), ctx)


def get_data(request, name):
    """
    Redirect to a temporary URL for accessing a file from object storage
    """
    try:
        storage_root = models.StorageRoot.objects.get(
            Q(root__contains=Site.objects.get_current().domain)
        )
        location = models.StorageLocation.objects.get(
            Q(storage_root=storage_root) & Q(path=name)
        )
    except (models.StorageRoot.DoesNotExist, models.StorageLocation.DoesNotExist):
        return HttpResponseNotFound()

    # identical bytes under several objects are one location; the file is served if
    # any object holds it, and withheld if any marks it private
    objects = list(models.Object.objects.filter(storage_location=location))
    if not objects:
        return HttpResponseNotFound()
    if not request.user.is_authenticated:
        for obj in objects:
            private = obj.metadata.filter(key="accessibility", value="private")
            if private.exists():
                return HttpResponse(status=403)

    filename = None
    for obj in objects:
        if obj.file_type:
            filename = "%s.%s" % (name, obj.file_type.extension)
            break

    return redirect(object_storage.create_url(name, "GET", filename))


def serve_file(full_uri):
    """
    Provide ability to view or download files stored on the local filesystem
    """
    if settings.REMOTE_REGISTRY:
        return HttpResponse(status=status.HTTP_503_SERVICE_UNAVAILABLE)

    full_uri = full_uri.replace("file://", "")

    if os.path.isfile(full_uri):
        return FileResponse(open(full_uri, "rb"))

    return HttpResponseNotFound()


def get_data_product(data_product):
    """
    Generate a link for accessing a data product
    """
    full_uri = data_product.object.storage_location.full_uri()

    if full_uri.startswith("/") or full_uri.startswith("file://"):
        return serve_file(full_uri)

    return redirect(full_uri)


def data_product(request, namespace, data_product_name, version):
    """
    Redirect to the URL of a file given the namespace, data product name and version
    """
    try:
        namespace = models.Namespace.objects.get(Q(name=namespace))
        data_product = models.DataProduct.objects.get(
            Q(name=data_product_name) & Q(namespace=namespace) & Q(version=version)
        )
    except:
        return HttpResponseNotFound()

    if not data_product.object.storage_location:
        return HttpResponseNotFound()

    if "root" in request.GET:
        return HttpResponse(data_product.object.storage_location.storage_root.root)

    return get_data_product(data_product)


def external_object(request, alternate_identifier, title, version):
    """
    Redirect to the URL of a file given the alternate identifier, title and version
    """
    # Find the external object
    try:
        external_object = models.ExternalObject.objects.get(
            Q(alternate_identifier=alternate_identifier)
            & Q(title=title)
            & Q(version=version)
        )
    except:
        return HttpResponseNotFound()

    # Use the storage location of the first data product registered from it, if there
    # is one and the user has not requested the original_store
    data_product = external_object.data_products.first()
    if (
        data_product is not None
        and data_product.object.storage_location
        and "original" not in request.GET
    ):
        if "root" in request.GET:
            return HttpResponse(
                data_product.object.storage_location.storage_root.root
            )
        return get_data_product(data_product)

    # Use original_store if it exists
    if external_object.original_store:
        if "root" in request.GET:
            return HttpResponse(external_object.original_store.storage_root.root)
        return redirect(external_object.original_store.full_uri())

    # External object exists but there is no StorageLocation or original_store
    return HttpResponse(status=204)


def logout(request):
    """Logs out user"""
    auth_logout(request)
    return redirect(request.META.get("HTTP_REFERER", "/"))
