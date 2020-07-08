from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.decorators import renderer_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import viewsets, permissions, views, renderers, mixins
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from . import models, serializers
from .prov import generate_prov_document, serialize_prov_document


class JPEGRenderer(renderers.BaseRenderer):
    media_type = 'image/jpeg'
    format = 'jpg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class SVGRenderer(renderers.BaseRenderer):
    media_type = 'image/svg+xml'
    format = 'svg'
    charset = None
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class XMLRenderer(renderers.BaseRenderer):
    media_type = 'text/xml'
    format = 'xml'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


class ProvnRenderer(renderers.BaseRenderer):
    media_type = 'text/plain'
    format = 'provn'
    charset = 'utf8'
    render_style = 'text'

    def render(self, data, media_type=None, renderer_context=None):
        return data


@renderer_classes([renderers.BrowsableAPIRenderer, renderers.JSONRenderer, JPEGRenderer, SVGRenderer, XMLRenderer, ProvnRenderer])
class ProvReportView(views.APIView):

    def get(self, request, pk, format=None):
        model_output = get_object_or_404(models.ModelOutput, pk=pk)
        doc = generate_prov_document(model_output)
        value = serialize_prov_document(doc, request.accepted_renderer.format)
        return Response(value)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ***List of users that have authenticated against the data registry, only users listed here are valid for the
    `responsible_person` field of other tables.***

    ### Read-only Fields:
    `url`: Reference to the instance of the `User`, final integer is the `User` id

    `username`: github username of the `User`

    `full_name`: full name as read from github

    `email`: email address as read from github

    `orgs`: organisations as read from github
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    queryset = get_user_model().objects.all().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username']


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    *TODO: update this with more information, not clear what the use is*
    ***List of groups that users can belong to?***
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, TokenAuthentication]
    queryset = Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


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
    filter_backends = [DjangoFilterBackend]
    # lookup_field = 'name'

    def get_queryset(self):
        return self.model.objects.all()

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


for name, cls in models.all_models.items():
    data = {
        'model': cls,
        'serializer_class': getattr(serializers, name + 'Serializer'),
        'filterset_fields': cls.FILTERSET_FIELDS,
        '__doc__': cls.__doc__
    }
    globals()[name + "ViewSet"] = type(name + "ViewSet", (BaseViewSet,), data)

