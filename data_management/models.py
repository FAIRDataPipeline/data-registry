from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from dynamic_validator import ModelFieldRequiredMixin


class BaseModel(ModelFieldRequiredMixin, models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    updated_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_updated',
            editable=False,
            verbose_name='last updated by',
            )
    last_updated = models.DateTimeField(auto_now=True)

    EXTRA_DISPLAY_FIELDS = ()
    REQUIRED_FIELDS = ['name']
    FILTERSET_FIELDS = ['name']

    def reverse_name(self):
        return self.__class__.__name__.lower()

    class Meta:
        abstract = True
        ordering = ['name', '-last_updated']

    def __str__(self):
        return self.name


class DataObject(BaseModel):
    # object_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    responsible_person = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_responsible_for',
            )
    issues = GenericRelation('Issue')

    class Meta(BaseModel.Meta):
        abstract = True


class DataObjectVersion(DataObject):
    VERSIONED_OBJECT = ''
    version_identifier = models.CharField(max_length=255)
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='superseded_by')

    REQUIRED_FIELDS = []
    
    @property
    def name(self):
        return '%s (version %s)' % (getattr(self, self.VERSIONED_OBJECT).name, self.version_identifier)

    class Meta(DataObject.Meta):
        abstract = True
        ordering = ['-version_identifier']


class Issue(BaseModel):
    """
    ***A quality issue that can be attached to any data object in the registry.***

    ### Writable Fields:
    `name`: Name of the `Issue`, unique in the context of `Issue`

    `description`: Free text description of the `Issue`

    `content_type`: Reference to a another type in the registry, e.g. `Source` or `DataProductVersion`

    `object_id`: Reference to the item this `Issue` relates to

    `severity`: Severity of this `Issue` as an integer, the larger the value the more severe the `Issue`
    `
    ### Read-only Fields:
    `url`: Reference to the instance of the `Issue`, final integer is the `Issue` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    data_object = GenericForeignKey('content_type', 'object_id')
    severity = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(max_length=1024, null=False, blank=False, verbose_name='description')

    def __str__(self):
        return '%s [Severity %s]' % (self.name, self.severity)


class DataProductType(BaseModel):
    """
    *TODO: remove?*
    """
    description = models.TextField(max_length=1024, null=False, blank=False)


class StorageType(BaseModel):
    """
    *TODO: remove?*
    """
    description = models.TextField(max_length=1024, null=True, blank=True)


class URIField(models.URLField):
    default_validators = []


class StorageRoot(BaseModel):
    """
    ***The root location of a storage cache where model files are stored.***

    ### Writable Fields:
    `name`: Name of the `StorageRoot`, unique in the context of `StorageRoot`

    `description`: Free text description of the `StorageRoot`

    `uri`: URI (including protocol) to the root of a `StorageLocation`, when prepended to a `StorageLocation` `path`
    produces a complete URI to a file. Examples:

    * https://somewebsite.com/
    * ftp://host/ (ftp://username:password@host:port/)
    * ssh://host/
    * file:///someroot/ (file://C:\)
    * github://org:repo@sha/ (github://org:repo/ (master))

    `type`: Reference to the `StorageType` of the `StorageRoot`

    ### Read-only Fields:
    `url`: Reference to the instance of the `StorageRoot`, final integer is the `StorageRoot` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    type = models.ForeignKey(StorageType, on_delete=models.CASCADE, null=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    uri = models.CharField(max_length=1024, null=False, blank=False)
    # uri = URIField(max_length=1024, null=False, blank=False)


class StorageLocation(DataObject):
    """
    ***The `StorageLocation` of an item relative to a `StorageRoot`.***

    ### Writable Fields:
    `name`: Name of the `StorageLocation`, unique in the context of `StorageLocation`

    `description`: Free text description of the `StorageLocation`

    `path`: Path from a `StorageRoot` `uri` to the item location, when appended to a `StorageRoot` `uri`
    produces a complete URI.

    `hash`: If `StorageLocation` references a file, this is the calculated SHA1 hash of the file. If `StorageLocation`
    references a directory *TODO: can't be git sha for validation (doesn't care about local changes), could be recursive
    sha1 of all files in the directory (excluding .git and things referenced in .gitignore), but needs to be OS independent
    (order matters) and things like logging output might affect it...*

    `valid_storage`: boolean true/false. If True use the `path` provided here with its `store_root` to locate the item, else
    use the `cached_storage_location` `path` and its `store_root` to locate the item.

    `responsible_person`: Reference to the user that is responsible for the `StorageLocation`

    `store_root`: Reference to the `StorageRoot` to append the `path` to.

    `cached_storage_location`: Reference to a secondary `StorageLocation` that contains a cache of the item, used if the
    true storage location is outside of our control or might change from the time that we accessed it (e.g. it's a website)

    ### Read-only Fields:
    `url`: Reference to the instance of the `StorageLocation`, final integer is the `StorageLocation` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    store_root = models.ForeignKey(StorageRoot, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=True, blank=True)
    path = models.CharField(max_length=1024, null=True, blank=True)
    hash = models.CharField(max_length=1024, null=True, blank=True)
    valid_storage = models.BooleanField(default=True)
    cached_storage_location = models.ForeignKey(StorageRoot, null=True, on_delete=models.CASCADE, related_name='cached_locations')


class Accessibility(BaseModel):
    """
    ***The accessibility level of data.***

    ### Writable Fields:
    `name`: Name of the `Accessibility`, unique in the context of `Accessibility`

    `description`: Free text description of the `Accessibility`

    `access_info`: *TODO: What is this field?*

    ### Read-only Fields:
    `url`: Reference to the instance of the `Accessibility`, final integer is the `Accessibility` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    description = models.TextField(max_length=1024, null=True, blank=True)
    access_info = models.CharField(max_length=1024, null=True, blank=True)


class SourceType(BaseModel):
    """
    Type of primary data source.
    """
    description = models.CharField(max_length=255, null=False, blank=False)


class Source(DataObject):
    """
    ***Primary source of data being using by models. For example a paper or government website.***

    ### Writable Fields:
    `name`: Name of the `Source`, unique in the context of `Source`

    `description`: Free text description of the `Source`

    `responsible_person`: Reference to the user that is responsible for the `Source`

    `store`: Reference to the `StorageLocation` of the `Source`. *TODO: not clear what this is referencing vs `SourceVersion`, c.f. `DataProduct` where it's not present*

    `source_type`: Reference to the `SourceType` of the `Source`

    ### Read-only Fields:
    `url`: Reference to the instance of the `Source`, final integer is the `Source` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `versions`: List of references to `SourceVersion` that reference the `Source`
    """
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    source_type = models.ForeignKey(SourceType, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)


class SourceVersion(DataObjectVersion):
    """
    ***Version of primary source data that was used to populate a given `DataProductVersion`.***

    ### Writable Fields:

    `description`: Free text description of the `SourceVersion`

    `responsible_person`: Reference to the user that is responsible for the `SourceVersion`

    `store`: Reference to the `StorageLocation` of the `SourceVersion`

    `source`: Reference to the `Source` that the `SourceVersion` versions

    `accessibility`: Reference to the `Accessibility` of the `SourceVersion`

    `version_identifier`: [SemVer](https://semver.org/spec/v2.0.0.html) version of the `SourceVersion`

    `supersedes`: Reference to the `SourceVersion` that this supersedes *TODO: not clear this is required given semver versioning?*

    ### Read-only Fields:
    `url`: Reference to the instance of the `SourceVersion`, final integer is the `SourceVersion` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    VERSIONED_OBJECT = 'source'
    FILTERSET_FIELDS = ['version_identifier', VERSIONED_OBJECT]

    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['source', 'version_identifier'], name='source_version_unique_identifier')
        ]


class DataProduct(DataObject):
    """
    ***A data product that is used by or generated by a model.***

    ### Writable Fields:
    `name`: Name of the `DataProduct`, unique in the context of `DataProduct`

    `description`: Free text description of the `DataProduct`

    `responsible_person`: Reference to the user that is responsible for the `DataProduct`

    `type`: Reference to the `DataProductType` of the `DataProduct`

    ### Read-only Fields:
    `url`: Reference to the instance of the `DataProduct`, final integer is the `DataProduct` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `versions`: List of references to `DataProductVersion` that reference the `DataProduct`
    """
    EXTRA_DISPLAY_FIELDS = ('versions',)

    description = models.TextField(max_length=1024, null=False, blank=False)
    type = models.ForeignKey(DataProductType, on_delete=models.CASCADE)


# class DataProductDataType(BaseModel):
#     description = models.CharField(max_length=255)


class ProcessingScript(DataObject):
    """
    ***A processing script used to derive a `DataProductVersion`.***

    ### Writable Fields:
    `name`: Name of the `ProcessingScript`, unique in the context of `ProcessingScript`

    `responsible_person`: Reference to the user that is responsible for the `DataProduct`

    `store`: Reference to the `StorageLocation` of the `ProcessingScript`. *TODO: not clear what this is referencing vs `ProcessingScriptVersion`, c.f. `DataProduct` where it's not present*

    *TODO: seems odd that `ProcessingScript` has no `description` given `Source` and `DataProduct` do*

    ### Read-only Fields:
    `url`: Reference to the instance of the `ProcessingScript`, final integer is the `ProcessingScript` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `versions`: List of references to `ProcessingScriptVersion` that reference the `ProcessingScript`
    """
    EXTRA_DISPLAY_FIELDS = ('versions',)
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)


class ProcessingScriptVersion(DataObjectVersion):
    """
    ***A specific version of `ProcessingScript` which was used in the generation of a `DataProductVersion`.***

    ### Writable Fields:
    `responsible_person`: Reference to the user that is responsible for the `ProcessingScriptVersion`

    `store`: Reference to the `StorageLocation` of the `ProcessingScriptVersion`

    `processing_script`: Reference to the `ProcessingScript` that the `ProcessingScriptVersion` versions

    `accessibility`: Reference to the `Accessibility` of the `ProcessingScriptVersion`

    `version_identifier`: [SemVer](https://semver.org/spec/v2.0.0.html) version of the `ProcessingScriptVersion`

    `supersedes`: Reference to the `ProcessingScriptVersion` that this supersedes *TODO: not clear this is required given semver versioning?*

    ### Read-only Fields:
    `url`: Reference to the instance of the `ProcessingScriptVersion`, final integer is the `ProcessingScriptVersion` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `data_product_versions`: List of `DataProductVersion` that the `ProcessingScriptVersion` created
    """
    VERSIONED_OBJECT = 'processing_script'
    EXTRA_DISPLAY_FIELDS = ('data_product_versions',)
    FILTERSET_FIELDS = ['version_identifier', VERSIONED_OBJECT]

    processing_script = models.ForeignKey(ProcessingScript, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['processing_script', 'version_identifier'],
                                    name='processing_script_version_unique_identifier')
        ]


class DataProductVersion(DataObjectVersion):
    """
    ***Specific version of a `DataProduct` that is associated with a `ModelRun`, either as an input or output via its
    `DataProductVersionComponent`***

    ### Writable Fields:
    `description`: Free text description of the `DataProductVersion`

    `responsible_person`: Reference to the user that is responsible for the `DataProductVersion`

    `store`: Reference to the `StorageLocation` of the `DataProductVersion`

    `data_product`: Reference to the `DataProduct` that the `DataProductVersion` versions

    `accessibility`: Reference to the `Accessibility` of the `DataProductVersion`

    `version_identifier`: [SemVer](https://semver.org/spec/v2.0.0.html) version of the `DataProductVersion`

    `supersedes`: Reference to the `DataProductVersion` that this supersedes *TODO: not clear this is required given semver versioning?*

    `processing_script_version`: Reference to the `ProcessingScriptVersion` that generated this `DataProductVersion`

    `source_versions`: List of `SourceVersion` that were used to create this `DataProductVersion`. *TODO: not clear that this relationship will be known? Seems like this relationship is like inputs to outputs of ModelRun but encoded differently`

    ### Read-only Fields:
    `url`: Reference to the instance of the `ProcessingScriptVersion`, final integer is the `ProcessingScriptVersion` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `components`: List of `DataProductVersionComponent` that the `DataProductVersion` contains
    """
    VERSIONED_OBJECT = 'data_product'
    EXTRA_DISPLAY_FIELDS = ('components',)
    FILTERSET_FIELDS = ['version_identifier', VERSIONED_OBJECT]

    data_product = models.ForeignKey(DataProduct, on_delete=models.CASCADE, related_name='versions')
    # data_type = models.ForeignKey(DataProductDataType, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)
    processing_script_version = models.ForeignKey(ProcessingScriptVersion, null=True, blank=True,
                                                  on_delete=models.CASCADE, related_name='data_product_versions')
    source_versions = models.ManyToManyField(SourceVersion, blank=True)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['data_product', 'version_identifier'],
                                    name='data_product_version_unique_identifier')
        ]


class DataProductVersionComponent(DataObject):
    """
    ***A component of a `DataProductVersion` being used as the input to a `ModelRun` or produced as an output from a
    `ModelRun`.***

    ### Writable Fields:
    `name`: Name of the `DataProductVersionComponent`, unique in the context of `DataProductVersionComponent` and its
    `DataProductVersion` reference

    `responsible_person`: Reference to the user that is responsible for the `DataProductVersionComponent`

    `data_product_version`: Reference to the `DataProductVersion` that contains the `DataProductVersionComponent`

    ### Read-only Fields:
    `url`: Reference to the instance of the `ProcessingScriptVersion`, final integer is the `ProcessingScriptVersion` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `input_to_model_runs`: List of `ModelRun` that the `DataProductVersionComponent` is being used as an input to

    `output_of_model_runs`: List of `ModelRun` that the `DataProductVersionComponent` was created as an output of
    """
    EXTRA_DISPLAY_FIELDS = ('input_to_model_runs', 'output_of_model_runs')
    FILTERSET_FIELDS = ['data_product_version', 'name']

    data_product_version = models.ForeignKey(DataProductVersion, on_delete=models.CASCADE, related_name='components')
    name = models.CharField(max_length=255, null=False, blank=False, unique=False)

    class Meta(DataObject.Meta):
        constraints = [
            models.UniqueConstraint(fields=['data_product_version', 'name'],
                                    name='data_product_version_component_unique_identifier')
        ]


class Model(DataObject):
    """
    ***An epidemiological model.***

    ### Writable Fields:
    `name`: Name of the `Model`, unique in the context of `Model`

    `description`: Free text description of the `Model`

    `responsible_person`: Reference to the user that is responsible for the `Model`

    `store`: Reference to the `StorageLocation` of the `Model`. *TODO: not clear what this is referencing vs `ModelVersion`*

    ### Read-only Fields:
    `url`: Reference to the instance of the `Model`, final integer is the `Model` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `versions`: List of references to `ModelVersion` that reference the `Model`
    """
    EXTRA_DISPLAY_FIELDS = ('versions',)

    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)


class ModelVersion(DataObjectVersion):
    """
    ***Version of a model that was used in a specific ModelRun.*** *TODO: is this right? it implies that it's created with a `ModelRun` rather than being an independent entity, but `model_runs` field implies it's more general*

    ### Writable Fields:

    `description`: Free text description of the `ModelVersion`

    `responsible_person`: Reference to the user that is responsible for the `ModelVersion`

    `store`: Reference to the `StorageLocation` of the `ModelVersion`

    `model`: Reference to the `Model` that the `ModelVersion` versions

    `accessibility`: Reference to the `Accessibility` of the `ModelVersion`

    `version_identifier`: [SemVer](https://semver.org/spec/v2.0.0.html) version of the `ModelVersion`

    `supersedes`: Reference to the `ModelVersion` that this supersedes *TODO: not clear this is required given semver versioning?*

    ### Read-only Fields:
    `url`: Reference to the instance of the `SourceVersion`, final integer is the `SourceVersion` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `model_runs`: List of `ModelRun` that use this `ModelVersion`
    """
    EXTRA_DISPLAY_FIELDS = ('model_runs',)
    VERSIONED_OBJECT = 'model'
    FILTERSET_FIELDS = ['version_identifier', VERSIONED_OBJECT]

    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(StorageLocation, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['model', 'version_identifier'], name='model_version_unique_identifier')
        ]


class ModelRun(DataObject):
    """
    ***Run of a `ModelVersion` along with its associated input and outputs.***

    ### Writable Fields:
    `description`: Free text description of the `ModelRun`

    `responsible_person`: Reference to the user that is responsible for the `ModelRun`

    `run_id`: string id of the `ModelRun`, generated by the data pipeline API if used in that context

    `run_date`: datetime of the `ModelRun`

    `model_version`:  Reference to the `ModelVersion` that was run

    `supersedes`: Reference to the `ModelVersion` that this supersedes *TODO: not clear this is required given semver versioning?*

    `model_config`: YAML configuration used for the `ModelRun`, should be explicit about `DataProductVersionComponent` used

    `submission_script`: *TODO: is this a path to the script that ran the `ModelRun` or is it the script itself?*

    `inputs`: List of `DataProductVersionComponent` that the `ModelRun` used as inputs

    `outputs`: List of `DataProductVersionComponent` that the `ModelRun` produced as outputs

    ### Read-only Fields:
    `url`: Reference to the instance of the `ModelRun`, final integer is the `ModelRun` id

    `last_updated`: datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    FILTERSET_FIELDS = ['model_version', 'run_id', 'run_date']

    model_version = models.ForeignKey(ModelVersion, on_delete=models.CASCADE, related_name='model_runs')
    run_id = models.TextField(max_length=1024, null=False, blank=False)
    run_date = models.DateTimeField()
    description = models.TextField(max_length=1024, null=True, blank=True)
    model_config = models.TextField(max_length=1024, null=True, blank=True)
    submission_script = models.TextField(max_length=1024, null=True, blank=True)
    inputs = models.ManyToManyField(DataProductVersionComponent, blank=True, related_name='input_to_model_runs')
    outputs = models.ManyToManyField(DataProductVersionComponent, blank=True, related_name='output_of_model_runs')
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    class Meta(DataObjectVersion.Meta):
        constraints = [
            models.UniqueConstraint(fields=['model_version', 'run_id'], name='model_run_unique_identifier')
        ]
        ordering = ['-run_date']

    @property
    def name(self):
        return '%s (Run %s)' % (self.model_version.name, self.run_date)


def _is_data_object_subclass(name, cls):
    """
    Test if given class is a non-abstract subclasses of DataObject
    """
    return (
            isinstance(cls, type)
            and issubclass(cls, DataObject)
            and name not in ('DataObject', 'DataObjectVersion')
    )


def _is_base_model_subclass(name, cls):
    """
    Test if given class is a non-abstract subclasses of BaseModel
    """
    return (
            isinstance(cls, type)
            and issubclass(cls, BaseModel)
            and name not in ('BaseModel', 'DataObject', 'DataObjectVersion')
    )


all_object_models = dict(
    (name, cls) for (name, cls) in globals().items() if _is_data_object_subclass(name, cls)
)

all_models = dict(
    (name, cls) for (name, cls) in globals().items() if _is_base_model_subclass(name, cls)
)
