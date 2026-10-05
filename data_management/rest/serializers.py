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
        fields = ["url", "username", "full_name", "email", "orgs"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    """
    Class for serializing the Group model.
    """

    class Meta:
        model = Group
        fields = ["url", "name"]


class BaseSerializer(serializers.HyperlinkedModelSerializer):
    """
    Base class for serializing the data management objects.

    Serializes all the defined fields on the model as well as any non-database field or method specified in the models
    EXTRA_DISPLAY_FIELDS.
    """

    class Meta:
        model = models.BaseModel
        fields = "__all__"

    def get_field_names(self, declared_fields, info):
        expanded_fields = super().get_field_names(declared_fields, info)
        return expanded_fields + list(self.Meta.model.EXTRA_DISPLAY_FIELDS)


class BaseSerializerUUID(BaseSerializer):
    uuid = serializers.UUIDField(initial=uuid4, default=uuid4)


class IssueSerializer(BaseSerializerUUID):

    class Meta(BaseSerializer.Meta):
        model = models.Issue


class CodeRunSerializer(BaseSerializer):
    ro_crate = serializers.SerializerMethodField()

    class Meta(BaseSerializer.Meta):
        model = models.CodeRun

    uuid = serializers.UUIDField(initial=uuid4, default=uuid4)

    def get_ro_crate(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.ro_crate())
        return obj.ro_crate()


class DataProductSerializer(BaseSerializer):
    internal_format = serializers.SerializerMethodField()
    prov_report = serializers.SerializerMethodField()
    ro_crate = serializers.SerializerMethodField()

    class Meta(BaseSerializer.Meta):
        model = models.DataProduct
        fields = "__all__"
        read_only_fields = model.EXTRA_DISPLAY_FIELDS

    def get_internal_format(self, obj):
        internal_format = serializers.BooleanField()
        internal_format = any(
            [
                component.whole_object == False
                for component in obj.object.components.all()
            ]
        )
        return internal_format

    def get_prov_report(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.prov_report())
        return obj.prov_report()

    def get_ro_crate(self, obj):
        request = self.context.get("request")
        if request:
            return request.build_absolute_uri(obj.ro_crate())
        return obj.ro_crate()


class ExternalObjectSerializer(BaseSerializer):
    """
    One ExternalObject per source, shared by the DataProducts registered from it.

    A POST of an identity that exists returns the existing row, filling an empty
    original_store or description from the request. `data_product`, written, links
    that DataProduct to the row; read, it is the first linked DataProduct - both for
    clients written when an ExternalObject belonged to one DataProduct.
    """

    data_product = serializers.HyperlinkedRelatedField(
        view_name="dataproduct-detail",
        queryset=models.DataProduct.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(BaseSerializer.Meta):
        model = models.ExternalObject
        read_only_fields = model.EXTRA_DISPLAY_FIELDS
        # the uniqueness validators DRF derives from the model's constraints would
        # refuse an existing identity before create() can return it
        validators = []

    IDENTITY = (
        "identifier",
        "alternate_identifier",
        "alternate_identifier_type",
        "title",
        "version",
    )
    MERGED = ("original_store", "description")

    def create(self, validated_data):
        data_product = validated_data.pop("data_product", None)
        identity = {field: validated_data.get(field) for field in self.IDENTITY}
        if not identity["version"]:
            field = models.ExternalObject._meta.get_field("version")
            identity["version"] = field.default
        external_object = models.ExternalObject.objects.filter(**identity).first()
        if external_object is None:
            external_object = super().create(validated_data)
        else:
            # the first registration's values stand; a later one fills what it left
            # empty
            for field in self.MERGED:
                if not getattr(external_object, field) and validated_data.get(field):
                    setattr(external_object, field, validated_data[field])
            external_object.save()
        if data_product is not None:
            data_product.external_object = external_object
            data_product.save()
        return external_object

    def to_representation(self, instance):
        data = super().to_representation(instance)
        linked = data["data_products"]
        data["data_product"] = linked[0] if linked else None
        return data


for name, cls in models.all_models.items():
    if name in ("Issue", "DataProduct", "CodeRun", "ExternalObject"):
        continue

    if name in ("Author", "Organisation", "Object"):
        serializer = BaseSerializerUUID
    else:
        serializer = BaseSerializer

    meta_cls = type(
        "Meta",
        (serializer.Meta,),
        {"model": cls, "read_only_fields": cls.EXTRA_DISPLAY_FIELDS},
    )
    data = {"Meta": meta_cls}
    globals()[name + "Serializer"] = type(name + "Serializer", (serializer,), data)
