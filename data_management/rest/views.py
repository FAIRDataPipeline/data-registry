from copy import deepcopy
import fnmatch

from django import forms, db
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import renderer_classes
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets, permissions, views, renderers, mixins, exceptions, status, filters as rest_filters
from rest_framework.response import Response
from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend, filterset
from django_filters import constants, filters
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db.models import Q

from data_management import models, object_storage, settings
from data_management import object_storage
from data_management.rest import serializers
from data_management.prov import generate_prov_document, serialize_prov_document


class BadQuery(APIException):
    status_code = 400
    default_code = 'bad_query'


class JPEGRenderer(renderers.BaseRenderer):
    """
    Custom rendered for returning JPEG images.
    """
    media_type = 'image/jpeg'
    format = 'jpg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class SVGRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning SVG images.
    """
    media_type = 'image/svg+xml'
    format = 'svg'
    charset = None
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class XMLRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning XML data.
    """
    media_type = 'text/xml'
    format = 'xml'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ProvnRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning PROV-N data (as defined in https://www.w3.org/TR/2013/REC-prov-n-20130430/).
    """
    media_type = 'text/provenance-notation'
    format = 'provn'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class TextRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning plain text data.
    """
    media_type = 'text/plain'
    format = 'text'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data['text']


class ProvReportView(views.APIView):
    """
    API view for returning a PROV report for a DataProduct.

    This report can be returned as JSON (default) or JPEG, SVG, XML or PROV-N
    using the custom renderers.
    """
    renderer_classes = [renderers.BrowsableAPIRenderer, renderers.JSONRenderer,
                        JPEGRenderer, SVGRenderer, XMLRenderer, ProvnRenderer]

    def get(self, request, pk):
        data_product = get_object_or_404(models.DataProduct, pk=pk)
        doc = generate_prov_document(data_product)
        show_attributes = request.query_params.get('attributes', True)
        if show_attributes == "False":
            show_attributes = False
        value = serialize_prov_document(
            doc,
            request.accepted_renderer.format,
            show_attributes=bool(show_attributes)
        )
        return Response(value)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API views (GET only) for the User model.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username']

    def list(self, request, *args, **kwargs):
        if set(request.query_params.keys()) - {'username', 'cursor', 'format'}:
            raise BadQuery(detail='Invalid query arguments, only query arguments [username] are allowed')
        return super().list(request, *args, **kwargs)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API views (GET only) for the Group model.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        if set(request.query_params.keys()) - {'cursor', 'format'}:
            raise BadQuery(detail='Invalid query arguments, no query arguments are allowed')
        return super().list(request, *args, **kwargs)


class APIIntegrityError(exceptions.APIException):
    """
    API error to be returned if there is a database unique constraint failure, i.e. due to trying to add a duplicate
    entry.
    """
    status_code = status.HTTP_409_CONFLICT
    default_code = 'integrity_error'


class GlobFilter(filters.Filter):
    """
    Custom API filter which can be used to add Unix glob style pattern matching to a field.
    """
    def __init__(self, *args, **kwargs):
        kwargs['lookup_expr'] = 'glob'
        super().__init__(*args, **kwargs)

    def filter(self, qs, value):
        if value in constants.EMPTY_VALUES:
            return qs
        if self.distinct:
            qs = qs.distinct()
        # The regex generated by fnmatch is not compatible with PostgreSQL so we need to do remove the ?s: characters
        # and we also add a \A at the start so that it matches on the entire string.
        regex_value = '\\A' + fnmatch.translate(value).replace('?s:', '')
        lookup = '%s__regex' % (self.field_name,)
        qs = self.get_method(qs)(**{lookup: regex_value})
        return qs

    field_class = forms.CharField


class CustomFilterSet(filterset.FilterSet):
    """
    Custom filters which we use to add glob filtering to all NameField fields.
    """
    FILTER_DEFAULTS = deepcopy(filterset.FILTER_FOR_DBFIELD_DEFAULTS)
    FILTER_DEFAULTS.update({
        models.NameField: {'filter_class': GlobFilter},
        db.models.OneToOneField: {'filter_class': filters.NumberFilter},
        db.models.ForeignKey: {'filter_class': filters.NumberFilter},
    })


class CustomDjangoFilterBackend(DjangoFilterBackend):
    """
    Custom filtering backend which we use to add the CustomFilterSet filtering.
    """
    default_filter_set = CustomFilterSet


class BaseViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    """
    Base class for all model API views. Allows for GET to retrieve lists of objects and single object, and
    POST to create a new object.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [CustomDjangoFilterBackend, rest_filters.OrderingFilter]
    ordering = ['-id']

    def list(self, request, *args, **kwargs):
        if self.model.FILTERSET_FIELDS == '__all__':
            filterset_fields = self.model.field_names() + ('cursor', 'format', 'ordering', 'page_size')
        else:
            filterset_fields = self.model.FILTERSET_FIELDS + ('cursor', 'format', 'ordering', 'page_size')
        if set(request.query_params.keys()) - set(filterset_fields):
            args = ', '.join(filterset_fields)
            raise BadQuery(detail='Invalid query arguments, only query arguments [%s] are allowed' % args)
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
            if ex.detail[name][0].code == 'unique':
                raise APIIntegrityError('Field ' + name + ' must be unique')
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
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def post(self, request, checksum=None):
        if 'checksum' not in request.data and not checksum:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not checksum:
            checksum = request.data['checksum']

        if self.check_hash(checksum):
            return Response(status=status.HTTP_409_CONFLICT)

        data = {'url': object_storage.create_url(checksum, 'PUT')}
        return Response(data)

    def check_hash(self, checksum):
        try:
            storage_root = models.StorageRoot.objects.get(Q(name=settings.CONFIG.get('storage', 'storage_root')))
            locations = models.StorageLocation.objects.filter(Q(storage_root=storage_root) & Q(hash=checksum))
        except:
            return False
        else:
            if not locations:
                return False

        return True


class IssueViewSet(BaseViewSet, mixins.UpdateModelMixin):
    model = models.Issue
    serializer_class = serializers.IssueSerializer
    filterset_fields = models.Issue.FILTERSET_FIELDS
    __doc__ = models.Issue.__doc__

    def create(self, request, *args, **kwargs):
        if 'component_issues' not in request.data:
            request.data['component_issues'] = []
        return super().create(request, *args, **kwargs)


class DataProductViewSet(BaseViewSet, mixins.UpdateModelMixin):
    model = models.DataProduct
    serializer_class = serializers.DataProductSerializer
    filterset_fields = models.DataProduct.FILTERSET_FIELDS
    __doc__ = models.DataProduct.__doc__

    def create(self, request, *args, **kwargs):
        if 'prov_report' not in request.data:
            request.data['prov_report'] = []
        return super().create(request, *args, **kwargs)


class CodeRunViewSet(BaseViewSet, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    model = models.CodeRun
    serializer_class = serializers.CodeRunSerializer
    filterset_fields = models.CodeRun.FILTERSET_FIELDS
    __doc__ = models.CodeRun.__doc__


for name, cls in models.all_models.items():
    if name in ('Issue', 'DataProduct', 'CodeRun'):
        continue
    data = {
        'model': cls,
        'serializer_class': getattr(serializers, name + 'Serializer'),
        'filterset_fields': cls.FILTERSET_FIELDS,
        '__doc__': cls.__doc__,
    }
    if name == 'TextFile':
        data['renderer_classes'] = BaseViewSet.renderer_classes + [TextRenderer]
    globals()[name + "ViewSet"] = type(name + "ViewSet", (BaseViewSet,), data)

