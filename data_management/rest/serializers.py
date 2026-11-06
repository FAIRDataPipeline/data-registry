from uuid import uuid4

from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from rest_framework import exceptions, serializers
from rest_framework.reverse import reverse

from data_management import models


class ProvenanceRefused(exceptions.APIException):
    """
    A write refused because it would break a rule the provenance rests on: an
    object has one producing run, no run reads anything downstream of its own
    outputs, and a data product's identity does not change.
    """

    status_code = 400
    default_code = "provenance_refused"


# The ids of the objects of some ObjectComponents
def _object_ids(components):
    return {component.object_id for component in components}


# A name for an object in a refusal: its data products, else its id
def _describe(object_id):
    products = models.DataProduct.objects.filter(object_id=object_id)
    names = [f"{p.namespace.name}:{p.name}@{p.version}" for p in products]
    return ", ".join(names) if names else f"object {object_id}"


# The ids of the given objects and of every object downstream of them: each object
# is followed to the runs that read a component of it, other than `run`, and on to
# the objects those runs wrote
def _downstream(object_ids, run):
    found = set(object_ids)
    frontier = set(object_ids)
    while frontier:
        readers = models.CodeRun.objects.filter(inputs__object__in=frontier)
        if run is not None:
            readers = readers.exclude(pk=run.pk)
        written = models.ObjectComponent.objects.filter(outputs_of__in=readers)
        frontier = set(written.values_list("object_id", flat=True)) - found
        found |= frontier
    return found


def check_code_run_links(run, inputs, outputs):
    """
    Refuse a code run's inputs and outputs if the links they add break a rule.

    `run` is the CodeRun being changed, or None for one being created; `inputs` and
    `outputs` are its ObjectComponents after the write. Each object an added output
    belongs to must be no other run's output, and no added link may close a loop:
    none of the run's inputs downstream of an added output, and no added input
    downstream of its outputs. Links the run has already are not checked again, so a
    breach stored before these rules does not block another change.
    """
    inputs, outputs = _object_ids(inputs), _object_ids(outputs)
    if run is None:
        added_inputs, added_outputs = inputs, outputs
    else:
        added_inputs = inputs - _object_ids(run.inputs.all())
        added_outputs = outputs - _object_ids(run.outputs.all())

    producers = models.CodeRun.objects.filter(outputs__object__in=added_outputs)
    if run is not None:
        producers = producers.exclude(pk=run.pk)
    for producer in producers.distinct():
        produced = _object_ids(producer.outputs.all()) & added_outputs
        raise ProvenanceRefused(
            f"{_describe(min(produced))} is an output of code run {producer.uuid} "
            "already, and an object has one producing run."
        )

    looped = (_downstream(added_outputs, run) & inputs) | (
        _downstream(outputs, run) & added_inputs
    )
    if looped:
        raise ProvenanceRefused(
            f"{_describe(min(looped))} would be both an input of this code run and "
            "downstream of its outputs, which would make a loop in the provenance."
        )


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

    def validate(self, attrs):
        attrs = super().validate(attrs)
        run = self.instance
        inputs = attrs.get("inputs", run.inputs.all() if run else [])
        outputs = attrs.get("outputs", run.outputs.all() if run else [])
        check_code_run_links(run, inputs, outputs)
        return attrs

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

    # What makes a data product the one it is; its source may change
    IDENTITY = ("object", "namespace", "name", "version")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance is not None:
            changed = [
                field
                for field in self.IDENTITY
                if field in attrs and attrs[field] != getattr(self.instance, field)
            ]
            if changed:
                raise ProvenanceRefused(
                    f"A data product's {', '.join(changed)} cannot be changed once it "
                    "is registered; register a new version instead."
                )
        return attrs

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
