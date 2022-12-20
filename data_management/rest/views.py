from copy import deepcopy
import fnmatch

from django import forms, db
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import renderer_classes
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets, permissions, views, renderers, mixins, exceptions, status, filters as rest_filters
from rest_framework.response import Response
from pydot import Dot
from django.db import IntegrityError
from django_filters.rest_framework import DjangoFilterBackend, filterset
from django_filters import constants, filters
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.db.models import Q

from data_management import models, object_storage, settings
from data_management import object_storage
from data_management.rest import serializers
from data_management.prov import generate_prov_document, serialize_prov_document
from data_management.rocrate import generate_ro_crate_from_dp, generate_ro_crate_from_cr, serialize_ro_crate


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


class JSONLDRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning JSON-LD data.
    """
    media_type = 'application/ld+json'
    format = 'json-ld'
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


class ZipRenderer(renderers.BaseRenderer):
    """
    Custom renderer for returning zip data.
    """
    media_type = 'application/zip'
    format = 'zip'
    charset = None
    render_style = 'binary'

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
        Dot(prog='dot').create()
        # GraphViz is installed so the JPEG and SVG renderers are made available.
        renderer_classes = [renderers.BrowsableAPIRenderer, renderers.JSONRenderer,
                            JSONLDRenderer, JPEGRenderer, SVGRenderer, XMLRenderer,
                            ProvnRenderer]
    except FileNotFoundError:
        # GraphViz is not installed so the JPEG and SVG renderers are NOT available.
        renderer_classes = [renderers.BrowsableAPIRenderer, renderers.JSONRenderer,
                            JSONLDRenderer, XMLRenderer, ProvnRenderer]

    def get(self, request, pk):
        data_product = get_object_or_404(models.DataProduct, pk=pk)

        show_attributes = request.query_params.get('attributes', True)
        if show_attributes == "False":
            show_attributes = False

        default_aspect_ratio = 0.71
        aspect_ratio = request.query_params.get('aspect_ratio', default_aspect_ratio)
        try:
            aspect_ratio = float(aspect_ratio)
        except ValueError:
            aspect_ratio = default_aspect_ratio

        default_depth = 1
        depth = request.query_params.get('depth', default_depth)
        try:
            depth = int(depth)
        except ValueError:
            depth = default_depth
        if depth < 1:
            depth = 1

        dpi = request.query_params.get('dpi', None)
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
            show_attributes=bool(show_attributes)
        )
        return Response(value)


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

External files may point directly to data, in which case they will be used directly as
inputs to a `CodeRun`. External files will have a link to them in the metadata file, but
will not be packaged in the zip file. However, it maybe that data has had to be
extracted from an external file before it can be used by a `CodeRun`, i.e. from a
journal article, In which case there will be an associated `DataProduct` that would have
been made to contain the data so that it can be used in a `CodeRun`. If this is the case
the relationship between the external file and `DataProduct` is modelled as a RO Crate
`ContextEntity` of type `CreateAction`.

The `CodeRun` has been modelled as a RO Crate `ContextEntity` of type `CreateAction`,
see
[software-used-to-create-files](https://www.researchobject.org/ro-crate/1.1/provenance.html#software-used-to-create-files).

A `CreateAction` has `instrument` property, which represents the software used to
generate the product. For our purposes `instrument` is the link to the repo.

`CreateAction` (`CodeRun`) properties:

* `instrument`: the software used to generate the output
* `object`: the input files
* `result`: the output file
* `agent`: the `Author`

The RO Crate is available as a `zip` file.

The contents of the ro-crate-metadata file can be viewed as `JSON` or `JSON-LD`.

### Query parameters:

`depth` (optional): An integer used to determine how many code runs to include,
the default is 1.

    """
    renderer_classes = [renderers.BrowsableAPIRenderer, renderers.JSONRenderer,
                        JSONLDRenderer, ZipRenderer]

    def get(self, request, pk):
        code_run = get_object_or_404(models.CodeRun, pk=pk)

        default_depth = 1
        depth = request.query_params.get('depth', default_depth)
        try:
            depth = int(depth)
        except ValueError:
            depth = default_depth
        if depth < 1:
            depth = 1

        crate = generate_ro_crate_from_cr(code_run, depth, request)

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

External files may point directly to data, in which case they will be used directly as
inputs to a `CodeRun`. External files will have a link to them in the metadata file, but
will not be packaged in the zip file. However, it maybe that data has had to be
extracted from an external file before it can be used by a `CodeRun`, i.e. from a
journal article, In which case there will be an associated `DataProduct` that would have
been made to contain the data so that it can be used in a `CodeRun`. If this is the case
the relationship between the external file and `DataProduct` is modelled as a RO Crate
`ContextEntity` of type `CreateAction`.

The `CodeRun` has been modelled as a RO Crate `ContextEntity` of type `CreateAction`,
see
[software-used-to-create-files](https://www.researchobject.org/ro-crate/1.1/provenance.html#software-used-to-create-files).

A `CreateAction` has `instrument` property, which represents the software used to
generate the product. For our purposes `instrument` is the link to the repo.

`CreateAction` (`CodeRun`) properties:

* `instrument`: the software used to generate the output
* `object`: the input files
* `result`: the output file
* `agent`: the `Author`

The RO Crate is available as a `zip` file.

The contents of the ro-crate-metadata file can be viewed as `JSON` or `JSON-LD`.

### Query parameters:

`depth` (optional): An integer used to determine how many code runs to include,
the default is 1.

    """

    renderer_classes = [renderers.BrowsableAPIRenderer, renderers.JSONRenderer,
                        JSONLDRenderer, ZipRenderer]

    def get(self, request, pk):
        data_product = get_object_or_404(models.DataProduct, pk=pk)

        default_depth = 1
        depth = request.query_params.get('depth', default_depth)
        try:
            depth = int(depth)
        except ValueError:
            depth = default_depth
        if depth < 1:
            depth = 1

        crate = generate_ro_crate_from_dp(data_product, depth, request)

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

        context = {"id": f"{request.build_absolute_uri('/')}api/data_extraction/{data_product.id}",
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
        if 'ro_crate' not in request.data:
            request.data['ro_crate'] = ""
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

