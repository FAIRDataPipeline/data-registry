from copy import deepcopy
import fnmatch

from django import forms, db
from rest_framework.authentication import (
    SessionAuthentication,
    BasicAuthentication,
    TokenAuthentication,
)
from rest_framework.decorators import renderer_classes
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import (
    viewsets,
    permissions,
    views,
    renderers,
    mixins,
    exceptions,
    status,
    filters as rest_filters,
)
from rest_framework.response import Response
from pydot import Dot
from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend, filterset
from django_filters import constants, filters
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings as conf_settings

from data_management import models, object_storage
from data_management import object_storage
from data_management.rest import serializers
from data_management.prov import generate_prov_document, serialize_prov_document
from data_management.rocrate import (
    generate_ro_crate_from_dp,
    generate_ro_crate_from_cr,
    serialize_ro_crate,
)


class BadQuery(APIException):
    status_code = 400
    default_code = "bad_query"


class JPEGRenderer(renderers.BaseRenderer):
    """
    Custom rendered for returning JPEG images.
    """

    media_type = "image/jpeg"
    format = "jpg"
    charset = None
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class SVGRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning SVG images.
    """

    media_type = "image/svg+xml"
    format = "svg"
    charset = None
    render_style = "text"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class XMLRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning XML data.
    """

    media_type = "text/xml"
    format = "xml"
    charset = "utf8"
    render_style = "text"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class JSONLDRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning JSON-LD data.
    """

    media_type = "application/ld+json"
    format = "json-ld"
    charset = "utf8"
    render_style = "text"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ProvnRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning PROV-N data (as defined in https://www.w3.org/TR/2013/REC-prov-n-20130430/).
    """

    media_type = "text/provenance-notation"
    format = "provn"
    charset = "utf8"
    render_style = "text"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class TextRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning plain text data.
    """

    media_type = "text/plain"
    format = "text"
    charset = "utf8"
    render_style = "text"

    def render(self, data, media_type=None, renderer_context=None):
        return data["text"]


class ZipRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning zip data.
    """

    media_type = "application/zip"
    format = "zip"
    charset = None
    render_style = "binary"

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ProvReportView(views.APIView):
    """
    ***The provenance report for a `DataProduct`.***

    The provenance report can be generated as `JSON`, `JSON-LD`, `XML` or `PROV-N`.
    Optionally `JPEG` and `SVG` versions of the provenance may be available.

    ### Query parameters:

    `attributes` (optional): A boolean, when `True` (default) show additional
    attributes of the objects on the image

    `aspect_ratio` (optional): A float used to define the ratio for the `JPEG` and
    `SVG` images. The default is 0.71, which is equivalent to A4 landscape.

    `dpi` (optional): A float used to define the dpi for the `JPEG` and `SVG` images

    `depth` (optional): An integer used to determine how many code runs to include,
    the default is 1
    """

    try:
        Dot(prog="dot").create()
        # GraphViz is installed so the JPEG and SVG renderers are made available.
        renderer_classes = [
            renderers.BrowsableAPIRenderer,
            renderers.JSONRenderer,
            JSONLDRenderer,
            JPEGRenderer,
            SVGRenderer,
            XMLRenderer,
            ProvnRenderer,
        ]
    except FileNotFoundError:
        # GraphViz is not installed so the JPEG and SVG renderers are NOT available.
        renderer_classes = [
            renderers.BrowsableAPIRenderer,
            renderers.JSONRenderer,
            JSONLDRenderer,
            XMLRenderer,
            ProvnRenderer,
        ]

    def get(self, request, pk):
        data_product = get_object_or_404(models.DataProduct, pk=pk)

        show_attributes = request.query_params.get("attributes", True)
        if show_attributes == "False":
            show_attributes = False

        default_aspect_ratio = 0.71
        aspect_ratio = request.query_params.get("aspect_ratio", default_aspect_ratio)
        try:
            aspect_ratio = float(aspect_ratio)
        except ValueError:
            aspect_ratio = default_aspect_ratio

        default_depth = 1
        depth = request.query_params.get("depth", default_depth)
        try:
            depth = int(depth)
        except ValueError:
            depth = default_depth
        if depth < 1:
            depth = 1

        dpi = request.query_params.get("dpi", None)
        try:
            dpi = float(dpi)
        except (TypeError, ValueError):
            dpi = None

        doc = generate_prov_document(data_product, depth, request)

        value = serialize_prov_document(
            doc,
            request.accepted_renderer.format,
            aspect_ratio,
            dpi,
            show_attributes=bool(show_attributes),
        )
        return Response(value)


# The level of an RO Crate request, 1 to 4: what travels with each file, as the
# rocrate module explains. A zip defaults to 3, every other format to 1.
def _crate_level(request):
    default = 3 if request.accepted_renderer.format == "zip" else 1
    level = request.query_params.get("level", default)
    try:
        level = int(level)
    except ValueError:
        level = 0
    if not 1 <= level <= 4:
        raise BadQuery(detail="level must be an integer from 1 to 4")
    return level


class CodeRunROCrateView(views.APIView):
    """
    ***The RO Crate for a `CodeRun`.***

    An RO Crate is research object (RO) that has been packaged up, in this case as a zip
    file. This research object is centred around a `CodeRun`. All output `DataProduct` files
    are packaged up along with any other local files that were used to produce them.
    Also included in the RO Crate is the metadata file `ro-crate-metadata.json`. The
    `ro-crate-metadata.json` file is made available under the
    [CC0 Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/).
    Please note individual files may have their own licenses.
    All of the packaged files are represented as `File` data entities in the metadata file.
    A data product's file is at `<namespace>/<name>/<version>.<extension>`, which is how a
    registry's data store lays out the files it pulls, whether or not its bytes are in the
    crate; the working config and the submission script are under `model_config/` and
    `submission_script/`. Every file carries the SHA-1 of its bytes (`sha1`) and the `uuid`
    of its object in the registry (`identifier`).
    Authors are identified by their ORCID, GitHub or other identifier where the
    registry has one, else by their `uuid`, and an author with a ROR id is an `Organization`; a user with no author linked by a local id;
    a licence by its URL, else by the file it applies to. Nothing is named by its row in
    the registry.
    An issue raised against a file is a line on the file's entity, under the registry's
    own term `issue`: the issue's uuid, its severity and its description, in that order.

    What travels with each file is chosen by the request's `level`, each level including the
    one before: 1, the hash and any persistent identifier, with the source's metadata; 2,
    the address the registry's copy can be downloaded from (`contentUrl`); 3, the bytes of
    every public file that no primary source stands for; 4, the bytes of every public file.
    A zip defaults to level 3 and the JSON-LD to level 1. The JSON-LD never holds a file, so
    the working config and the submission script, which every zip packs, are metadata alone
    there. A run's outputs outside the crate's provenance are described at level 1 whatever
    was asked, and a file that is not public is named by its storage location, as before.

    A data product registered from an external source is in the crate as itself, and the
    source is a `File` named by its identifier (a DOI, or else its alternate identifier),
    linked but not packaged. Where the registered bytes are the identified item, or one of
    its files (a primary source), the data product's `sameAs` points at the source; where
    the data was extracted from the source before it could be used (a supplementary source,
    e.g. a journal article), the extraction is modelled as a RO Crate `ContextEntity` of
    type `CreateAction` with the source as its `object` and the data product as its
    `result`.

    The `CodeRun` has been modelled as a RO Crate `ContextEntity` of type `CreateAction`,
    see
    [software-used-to-create-files](https://www.researchobject.org/ro-crate/1.1/provenance.html#software-used-to-create-files).

    A `CreateAction` has `instrument` property, which represents the software used to
    generate the product. For our purposes `instrument` is the link to the repo, at
    the commit that was run: the commit is its `softwareVersion`, and its `url` is the
    repo.

    A `DataProduct` file has the `name` and `version` of the `DataProduct`, and its
    `namespace` is an entity of type `Namespace`, whose `name` is the name of the
    `Namespace`, `alternateName` its full name and `url` its website.

    `CreateAction` (`CodeRun`) properties:

    * `identifier`: the `uuid` of the `CodeRun`, which is also in its `@id`
    * `instrument`: the code repo at the commit that was run, or the submission script for a
      run without a repo
    * `object`: the input files, the working config and the submission script
    * `model_configuration`, `submission_script`: which of those files is which
    * `result`: every output of the run; those outside the crate's provenance are described
      but not packaged
    * `agent`: the `Author`

    The crate conforms to Process Run Crate 0.6 (https://w3id.org/ro/wfrun/process/0.6).

    The RO Crate is available as a `zip` file.

    The contents of the ro-crate-metadata file can be viewed as `JSON` or `JSON-LD`.

    ### Query parameters:

    `depth` (optional): An integer used to determine how many code runs to include,
    the default is 1.

    `level` (optional): An integer from 1 to 4 choosing what travels with each file (see
    above); the default is 3 for a zip and 1 otherwise.

    """

    renderer_classes = [
        renderers.BrowsableAPIRenderer,
        renderers.JSONRenderer,
        JSONLDRenderer,
        ZipRenderer,
    ]

    def get(self, request, pk):
        code_run = get_object_or_404(models.CodeRun, pk=pk)

        default_depth = 1
        depth = request.query_params.get("depth", default_depth)
        try:
            depth = int(depth)
        except ValueError:
            depth = default_depth
        if depth < 1:
            depth = 1

        crate = generate_ro_crate_from_cr(
            code_run, depth, request, _crate_level(request)
        )

        return Response(serialize_ro_crate(crate, request.accepted_renderer.format))


class DataProductROCrateView(views.APIView):
    """
    ***The RO Crate for a `DataProduct`.***

    An RO Crate is research object (RO) that has been packaged up, in this case as a zip
    file. This research object is centred around the creation of a `DataProduct`. The
    `DataProduct` file is packaged up along with any other local files that were used to
    produce it. Also included in the RO Crate is the metadata file `ro-crate-metadata.json`.
    The `ro-crate-metadata.json` file is made available under the
    [CC0 Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/).
    Please note individual files may have their own licenses.
    All of the packaged files are represented as `File` data entities in the metadata file.
    A data product's file is at `<namespace>/<name>/<version>.<extension>`, which is how a
    registry's data store lays out the files it pulls, whether or not its bytes are in the
    crate; the working config and the submission script are under `model_config/` and
    `submission_script/`. Every file carries the SHA-1 of its bytes (`sha1`) and the `uuid`
    of its object in the registry (`identifier`).
    Authors are identified by their ORCID, GitHub or other identifier where the
    registry has one, else by their `uuid`, and an author with a ROR id is an `Organization`; a user with no author linked by a local id;
    a licence by its URL, else by the file it applies to. Nothing is named by its row in
    the registry.
    An issue raised against a file is a line on the file's entity, under the registry's
    own term `issue`: the issue's uuid, its severity and its description, in that order.

    What travels with each file is chosen by the request's `level`, each level including the
    one before: 1, the hash and any persistent identifier, with the source's metadata; 2,
    the address the registry's copy can be downloaded from (`contentUrl`); 3, the bytes of
    every public file that no primary source stands for; 4, the bytes of every public file.
    A zip defaults to level 3 and the JSON-LD to level 1. The JSON-LD never holds a file, so
    the working config and the submission script, which every zip packs, are metadata alone
    there. A run's outputs outside the crate's provenance are described at level 1 whatever
    was asked, and a file that is not public is named by its storage location, as before.

    A data product registered from an external source is in the crate as itself, and the
    source is a `File` named by its identifier (a DOI, or else its alternate identifier),
    linked but not packaged. Where the registered bytes are the identified item, or one of
    its files (a primary source), the data product's `sameAs` points at the source; where
    the data was extracted from the source before it could be used (a supplementary source,
    e.g. a journal article), the extraction is modelled as a RO Crate `ContextEntity` of
    type `CreateAction` with the source as its `object` and the data product as its
    `result`.

    The `CodeRun` has been modelled as a RO Crate `ContextEntity` of type `CreateAction`,
    see
    [software-used-to-create-files](https://www.researchobject.org/ro-crate/1.1/provenance.html#software-used-to-create-files).

    A `CreateAction` has `instrument` property, which represents the software used to
    generate the product. For our purposes `instrument` is the link to the repo, at
    the commit that was run: the commit is its `softwareVersion`, and its `url` is the
    repo.

    A `DataProduct` file has the `name` and `version` of the `DataProduct`, and its
    `namespace` is an entity of type `Namespace`, whose `name` is the name of the
    `Namespace`, `alternateName` its full name and `url` its website.

    `CreateAction` (`CodeRun`) properties:

    * `identifier`: the `uuid` of the `CodeRun`, which is also in its `@id`
    * `instrument`: the code repo at the commit that was run, or the submission script for a
      run without a repo
    * `object`: the input files, the working config and the submission script
    * `model_configuration`, `submission_script`: which of those files is which
    * `result`: every output of the run; those outside the crate's provenance are described
      but not packaged
    * `agent`: the `Author`

    The crate conforms to Process Run Crate 0.6 (https://w3id.org/ro/wfrun/process/0.6).

    The RO Crate is available as a `zip` file.

    The contents of the ro-crate-metadata file can be viewed as `JSON` or `JSON-LD`.

    ### Query parameters:

    `depth` (optional): An integer used to determine how many code runs to include,
    the default is 1.

    `level` (optional): An integer from 1 to 4 choosing what travels with each file (see
    above); the default is 3 for a zip and 1 otherwise.

    """

    renderer_classes = [
        renderers.BrowsableAPIRenderer,
        renderers.JSONRenderer,
        JSONLDRenderer,
        ZipRenderer,
    ]

    def get(self, request, pk):
        data_product = get_object_or_404(models.DataProduct, pk=pk)

        default_depth = 1
        depth = request.query_params.get("depth", default_depth)
        try:
            depth = int(depth)
        except ValueError:
            depth = default_depth
        if depth < 1:
            depth = 1

        crate = generate_ro_crate_from_dp(
            data_product, depth, request, _crate_level(request)
        )

        return Response(serialize_ro_crate(crate, request.accepted_renderer.format))


class DataExtractionView(views.APIView):

    def get(self, request, pk):
        data_product = get_object_or_404(models.DataProduct, pk=pk)

        # check for external object linked to the data product
        try:
            external_object = data_product.external_object
        except (models.DataProduct.external_object.RelatedObjectDoesNotExist,):
            # no external object
            raise Http404("DataProduct was not derived from an external object")

        if external_object.primary_not_supplement is True:
            # the data_product was NOT derived from the external object
            raise Http404("DataProduct was not derived from an external object")

        context = {
            "id": f"{request.build_absolute_uri('/')}api/data_extraction/{data_product.id}",
            "name": f"data extraction {pk}",
            "startTime": data_product.last_updated.isoformat(),
            "description": "import/extract data from an external source",
            "data_product": f"{request.build_absolute_uri('/')}api/data_product/{data_product.id}",
            "external_product": f"{request.build_absolute_uri('/')}api/external_object/{external_object.id}",
        }
        return Response(context)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API views (GET only) for the User model.
    """

    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        TokenAuthentication,
    ]
    queryset = get_user_model().objects.all().order_by("-date_joined")
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["username"]

    def list(self, request, *args, **kwargs):
        if set(request.query_params.keys()) - {"username", "cursor", "format"}:
            raise BadQuery(
                detail="Invalid query arguments, only query arguments [username] are allowed"
            )
        return super().list(request, *args, **kwargs)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API views (GET only) for the Group model.
    """

    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        TokenAuthentication,
    ]
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if set(request.query_params.keys()) - {"cursor", "format"}:
            raise BadQuery(
                detail="Invalid query arguments, no query arguments are allowed"
            )
        return super().list(request, *args, **kwargs)


class APIIntegrityError(exceptions.APIException):
    """
    API error to be returned if there is a database unique constraint failure, i.e. due to trying to add a duplicate
    entry.
    """

    status_code = status.HTTP_409_CONFLICT
    default_code = "integrity_error"


class GlobFilter(filters.Filter):
    """
    Custom API filter which can be used to add Unix glob style pattern matching to a field.
    """

    def __init__(self, *args, **kwargs):
        kwargs["lookup_expr"] = "glob"
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value in constants.EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        # The regex generated by fnmatch is not compatible with PostgreSQL so we need to do remove the ?s: characters
        # and we also add a \A at the start so that it matches on the entire string.
        regex_value = "\\A" + fnmatch.translate(value).replace("?s:", "")
        lookup = "%s__regex" % (self.field_name,)
        qs = self.get_method(qs)(**{lookup: regex_value})
        return qs

    field_class = forms.CharField


class CustomFilterSet(filterset.FilterSet):
    """
    Custom filters which we use to add glob filtering to all NameField fields, and to
    filter by the id of a related object from either side of a one-to-one or
    one-to-many relation, and from the reverse side of a many-to-many relation.
    """

    FILTER_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
    FILTER_DEFAULTS.update(
        {
            models.NameField: {"filter_class": GlobFilter},
            db.models.OneToOneField: {"filter_class": filters.NumberFilter},
            db.models.ForeignKey: {"filter_class": filters.NumberFilter},
            db.models.OneToOneRel: {"filter_class": filters.NumberFilter},
            db.models.ManyToOneRel: {"filter_class": filters.NumberFilter},
            db.models.ManyToManyRel: {"filter_class": filters.NumberFilter},
        }
    )


class CustomDjangoFilterBackend(DjangoFilterBackend):
    """
    Custom filtering backend which we use to add the CustomFilterSet filtering.
    """

    filterset_base = CustomFilterSet


class BaseViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Base class for all model API views. Allows for GET to retrieve lists of objects and single object, and
    POST to create a new object.
    """

    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        TokenAuthentication,
    ]
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [CustomDjangoFilterBackend, rest_filters.OrderingFilter]
    ordering = ["-id"]

    def list(self, request, *args, **kwargs):
        filterset_fields = self.model.filter_field_names() + (
            "cursor",
            "format",
            "ordering",
            "page_size",
        )
        if set(request.query_params.keys()) - set(filterset_fields):
            args = ", ".join(filterset_fields)
            raise BadQuery(
                detail="Invalid query arguments, only query arguments [%s] are allowed"
                % args
            )
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all()

    def create(self, request, *args, **kwargs):
        """
        Customising the create method to raise a 409 on uniqueness validation failing.
        """
        try:
            return super().create(request, *args, **kwargs)
        except ValidationError as ex:
            name = list(ex.detail.keys())[0]
            if ex.detail[name][0].code == "unique":
                raise APIIntegrityError("Field " + name + " must be unique")
            else:
                raise ex

    def perform_create(self, serializer):
        """
        Customising the save method to add the current user as the models updated_by.
        """
        try:
            return serializer.save(updated_by=self.request.user)
        except IntegrityError as ex:
            raise APIIntegrityError(str(ex))


class ObjectStorageView(views.APIView):
    """
    API view allowing users to upload data to object storage
    """

    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        TokenAuthentication,
    ]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, checksum=None):
        if "checksum" not in request.data and not checksum:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not checksum:
            checksum = request.data["checksum"]

        # the store already holds the file: a client takes the 409 as "uploaded"
        if object_storage.holds(checksum):
            return Response(status=status.HTTP_409_CONFLICT)

        data = {"url": object_storage.create_url(checksum, "PUT")}
        return Response(data)


class IssueViewSet(BaseViewSet, mixins.UpdateModelMixin):
    model = models.Issue
    serializer_class = serializers.IssueSerializer
    filterset_fields = models.Issue.filter_field_names()
    __doc__ = models.Issue.__doc__

    def create(self, request, *args, **kwargs):
        if "component_issues" not in request.data:
            request.data["component_issues"] = []
        return super().create(request, *args, **kwargs)


class DataProductViewSet(BaseViewSet, mixins.UpdateModelMixin):
    model = models.DataProduct
    serializer_class = serializers.DataProductSerializer
    filterset_fields = models.DataProduct.filter_field_names()
    __doc__ = models.DataProduct.__doc__

    def create(self, request, *args, **kwargs):
        if "prov_report" not in request.data:
            request.data["prov_report"] = []
        if "ro_crate" not in request.data:
            request.data["ro_crate"] = ""
        return super().create(request, *args, **kwargs)


class CodeRunViewSet(BaseViewSet, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    model = models.CodeRun
    serializer_class = serializers.CodeRunSerializer
    filterset_fields = models.CodeRun.filter_field_names()
    __doc__ = models.CodeRun.__doc__


class ExternalObjectViewSet(BaseViewSet):
    model = models.ExternalObject
    serializer_class = serializers.ExternalObjectSerializer
    filterset_fields = models.ExternalObject.filter_field_names()
    __doc__ = models.ExternalObject.__doc__

    def list(self, request, *args, **kwargs):
        """
        Lists take `data_product=<id>` as "linked to this DataProduct", and with it
        `version=<v>` as that DataProduct's version rather than the source's: the
        lookup clients made when an ExternalObject belonged to one DataProduct.
        """
        params = request.query_params
        if "data_product" in params:
            params = params.copy()
            data_product_id = params.pop("data_product")[-1]
            if "version" in params:
                version = params.pop("version")[-1]
                if not models.DataProduct.objects.filter(
                    pk=data_product_id, version=version
                ).exists():
                    data_product_id = "0"
            params.setlist("data_products", [data_product_id])
            request._request.GET = params
        return super().list(request, *args, **kwargs)


for name, cls in models.all_models.items():
    if name in ("Issue", "DataProduct", "CodeRun", "ExternalObject"):
        continue
    data = {
        "model": cls,
        "serializer_class": getattr(serializers, name + "Serializer"),
        "filterset_fields": cls.filter_field_names(),
        "__doc__": cls.__doc__,
    }
    if name == "TextFile":
        data["renderer_classes"] = BaseViewSet.renderer_classes + [TextRenderer]
    globals()[name + "ViewSet"] = type(name + "ViewSet", (BaseViewSet,), data)


class UserView(views.APIView):
    """
    API view allowing users to upload data to object storage
    """

    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        TokenAuthentication,
    ]
    renderer_classes = [renderers.JSONRenderer, renderers.BrowsableAPIRenderer]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_name = request.user.username
        context = {"username": user_name}
        return Response(context)
