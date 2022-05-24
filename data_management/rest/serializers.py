from uuid import uuid4

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.reverse import reverse

from data_management import models


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class for serializing the User model.
    """
    class Meta:
        model = get_user_model()
        fields = ['url', 'username', 'full_name', 'email', 'orgs']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class for serializing the Group model.
    """
    class Meta:
        model = Group
        fields = ['url', 'name']


class BaseSerializer(serializers.HyperlinkedModelSerializer):
    """
    Base class for serializing the data management objects.

    Serializes all the defined fields on the model as well as any non-database field or method specified in the models
    EXTRA_DISPLAY_FIELDS.
    """
    class Meta:
        model = models.BaseModel
        fields = '__all__'

    def get_field_names(self, declared_fields, info):
        expanded_fields = super().get_field_names(declared_fields, info)
        return expanded_fields + list(self.Meta.model.EXTRA_DISPLAY_FIELDS)

class BaseSerializerUUID(BaseSerializer):
    uuid = serializers.UUIDField(initial=uuid4, default=uuid4)

class IssueSerializer(BaseSerializerUUID):

    class Meta(BaseSerializer.Meta):
        model = models.Issue


class CodeRunSerializer(BaseSerializer):

    class Meta(BaseSerializer.Meta):
        model = models.CodeRun

    uuid = serializers.UUIDField(initial=uuid4, default=uuid4)


class DataProductSerializer(BaseSerializer):
    internal_format = serializers.SerializerMethodField()
    prov_report = serializers.SerializerMethodField()
    ro_crate = serializers.SerializerMethodField()

    class Meta(BaseSerializer.Meta):
        model = models.DataProduct
        fields = '__all__'
        read_only_fields = model.EXTRA_DISPLAY_FIELDS

    def get_internal_format(self, obj):
        internal_format = serializers.BooleanField()
        internal_format = any([component.whole_object == False for component in obj.object.components.all()])
        return internal_format

    def get_prov_report(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.prov_report())
        return obj.prov_report()

    def get_ro_crate(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.ro_crate())
        return obj.ro_crate()


for name, cls in models.all_models.items():
    if name in ('Issue', 'DataProduct', 'CodeRun'):
        continue

    if name in ('Author', 'Organisation', 'Object'):
        serializer = BaseSerializerUUID
    else:
        serializer = BaseSerializer

    meta_cls = type('Meta', (serializer.Meta,), {'model': cls, 'read_only_fields': cls.EXTRA_DISPLAY_FIELDS})
    data = {'Meta': meta_cls}
    globals()[name + "Serializer"] = type(name + "Serializer", (serializer,), data)
