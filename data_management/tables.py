from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.utils.html import escape, format_html

from . import models


# A table's cells are rendered as HTML, so every one is escaped text or a link built
# by format_html, which escapes what it is given
def _link(url, text):
    return format_html('<a href="{}">{}</a>', url, text) if url else ""


def data_product_table_data(request):
    size = int(request.GET.get("limit", 25))
    offset = int(request.GET.get("offset", 25))
    search = request.GET.get("search", None)
    sort = request.GET.get("sort", "") or "name"
    order = request.GET.get("order", "") or "asc"
    sign = "-" if order == "desc" else ""
    all_objects = models.DataProduct.objects.all().order_by(sign + sort)
    if search:
        filtered_objects = all_objects.filter(
            Q(namespace__name__icontains=search)
            | Q(name__icontains=search)
            | Q(version__icontains=search)
        )
    else:
        filtered_objects = all_objects
    paginator = Paginator(filtered_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse(
        {
            "total": filtered_objects.count(),
            "totalNotFiltered": all_objects.count(),
            "rows": [
                {
                    "namespace": escape(str(obj.namespace)),
                    "name": _link(f"/data_product/{obj.id}", obj.name),
                    "version": escape(obj.version),
                }
                for obj in page_objects
            ],
        }
    )


def external_objects_table_data(request):
    size = int(request.GET.get("limit", 25))
    offset = int(request.GET.get("offset", 25))
    search = request.GET.get("search", None)
    sort = request.GET.get("sort", "") or "title"
    order = request.GET.get("order", "") or "asc"
    sign = "-" if order == "desc" else ""
    all_objects = models.ExternalObject.objects.all().order_by(sign + sort)
    if search:
        filtered_objects = all_objects.filter(
            Q(alternate_identifier__icontains=search)
            | Q(identifier__icontains=search)
            | Q(release_date__icontains=search)
            | Q(title__icontains=search)
            | Q(version__icontains=search)
        )
    else:
        filtered_objects = all_objects
    paginator = Paginator(filtered_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse(
        {
            "total": filtered_objects.count(),
            "totalNotFiltered": all_objects.count(),
            "rows": [
                {
                    "identifier": _link(obj.identifier, obj.identifier),
                    "alternate_identifier": escape(obj.alternate_identifier or ""),
                    "release_date": obj.release_date.date().isoformat(),
                    "title": _link(f"/external_object/{obj.id}", obj.title),
                    "version": escape(obj.version),
                }
                for obj in page_objects
            ],
        }
    )


def code_repo_release_table_data(request):
    size = int(request.GET.get("limit", 25))
    offset = int(request.GET.get("offset", 25))
    search = request.GET.get("search", None)
    sort = request.GET.get("sort", "") or "name"
    order = request.GET.get("order", "") or "asc"
    sign = "-" if order == "desc" else ""
    all_objects = models.CodeRepoRelease.objects.all().order_by(sign + sort)
    if search:
        filtered_objects = all_objects.filter(
            Q(name__icontains=search)
            | Q(version__icontains=search)
            | Q(website__icontains=search)
        )
    else:
        filtered_objects = all_objects
    paginator = Paginator(filtered_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse(
        {
            "total": filtered_objects.count(),
            "totalNotFiltered": all_objects.count(),
            "rows": [
                {
                    "name": _link(f"/object/{obj.object.id}", obj.name),
                    "version": escape(obj.version),
                    "website": _link(obj.website, obj.website),
                }
                for obj in page_objects
            ],
        }
    )
