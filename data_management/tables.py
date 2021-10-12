from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse

from . import models


def data_product_table_data(request):
    size = int(request.GET.get('limit', 25))
    offset = int(request.GET.get('offset', 25))
    search = request.GET.get('search', None)
    sort = request.GET.get('sort', '') or 'name'
    order = request.GET.get('order', '') or 'asc'
    sign = '-' if order == 'desc' else ''
    all_objects = models.DataProduct.objects.all().order_by(sign + sort)
    if search:
        filtered_objects = all_objects.filter(
            Q(namespace__name__icontains=search) |
            Q(name__icontains=search) |
            Q(version__icontains=search)
        )
    else:
        filtered_objects = all_objects
    paginator = Paginator(filtered_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse({
        'total': filtered_objects.count(),
        'totalNotFiltered': all_objects.count(),
        'rows': [
            {
                'namespace': str(obj.namespace),
                'name': '<a href="/data_product/%d">%s</a>' % (obj.id, obj.name),
                'version': obj.version,
            } for obj in page_objects
        ],
    })


def external_objects_table_data(request):
    size = int(request.GET.get('limit', 25))
    offset = int(request.GET.get('offset', 25))
    search = request.GET.get('search', None)
    sort = request.GET.get('sort', '') or 'identifier'
    order = request.GET.get('order', '') or 'asc'
    sign = '-' if order == 'desc' else ''
    all_objects = models.ExternalObject.objects.all().order_by(sign + sort)
    if search:
        filtered_objects = all_objects.filter(
            Q(source__name__icontains=search) |
            Q(alternate_identifier__icontains=search) |
            Q(identifier__icontains=search) |
            Q(release_date__icontains=search) |
            Q(title__icontains=search) |
            Q(version__icontains=search)
        )
    else:
        filtered_objects = all_objects
    paginator = Paginator(filtered_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse({
        'total': filtered_objects.count(),
        'totalNotFiltered': all_objects.count(),
        'rows': [
            {
                'url': '<a href="/external_object/%d"><i class="far fa-file-alt"</i></a>' % obj.data_product.id,
                'identifier': '<a href="%s">%s</a>' % (obj.identifier, obj.identifier),
                'alternate_identifier': obj.alternate_identifier,
                'release_date': str(obj.release_date),
                'title': obj.title,
                'version': obj.data_product.version,
            } for obj in page_objects
        ],
    })


def code_repo_release_table_data(request):
    size = int(request.GET.get('limit', 25))
    offset = int(request.GET.get('offset', 25))
    search = request.GET.get('search', None)
    sort = request.GET.get('sort', '') or 'name'
    order = request.GET.get('order', '') or 'asc'
    sign = '-' if order == 'desc' else ''
    all_objects = models.CodeRepoRelease.objects.all().order_by(sign + sort)
    if search:
        filtered_objects = all_objects.filter(
            Q(name__icontains=search) |
            Q(version__icontains=search) |
            Q(website__icontains=search)
        )
    else:
        filtered_objects = all_objects
    paginator = Paginator(filtered_objects, size)
    page = (offset / size) + 1
    page_objects = paginator.get_page(page)
    return JsonResponse({
        'total': filtered_objects.count(),
        'totalNotFiltered': all_objects.count(),
        'rows': [
            {
                'name': '<a href="/object/%d">%s</a>' % (obj.object.id, obj.name),
                'version': obj.version,
                'website': obj.website,
            } for obj in page_objects
        ],
    })
