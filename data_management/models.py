import hashlib
from uuid import uuid4, UUID

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from dynamic_validator import ModelFieldRequiredMixin
from django.contrib.auth import get_user_model

from . import validators


PATH_FIELD_LENGTH = 1024 * 8
CHAR_FIELD_LENGTH = 1024
TEXT_FIELD_LENGTH = 1024**2


class BaseModel(ModelFieldRequiredMixin, models.Model):
    """
    Base model for all objects in the database. Used to defined common fields and functionality.
    """
    _field_names = None
    updated_by = models.ForeignKey(
            get_user_model(),
            on_delete=models.PROTECT,
            related_name='%(app_label)s_%(class)s_updated',
            editable=False,
            verbose_name='last updated by',
            )
    last_updated = models.DateTimeField(auto_now=True)

    EXTRA_DISPLAY_FIELDS = ()
    REQUIRED_FIELDS = ()
    FILTERSET_FIELDS = '__all__'
    ADMIN_LIST_FIELDS = ()

    def reverse_name(self):
        return self.__class__.__name__.lower()

    @classmethod
    def field_names(cls):
        if cls._field_names is None:
            cls._field_names = tuple(field.name for field in cls._meta.get_fields() if field.name != 'id')
        return cls._field_names

    class Meta:
        abstract = True
        ordering = ['-last_updated']


###############################################################################
# Custom Fields

class URIField(models.CharField):
    """
    A field type used to specify that a field holds a URI.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        super().__init__(*args, **kwargs)


class NameField(models.CharField):
    """
    A field type used to specify that a field holds a simple name, one that we can apply a glob filter to
    when filtering the query.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        kwargs['validators'] = (validators.NameValidator(),)
        super().__init__(*args, **kwargs)


class VersionField(models.CharField):
    """
    A field type used to specify that a field holds a semantic version.
    """
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 1024
        kwargs['validators'] = (validators.VersionValidator(),)
        super().__init__(*args, **kwargs)


###############################################################################
# Traceablity objects

class FileType(BaseModel):
    """
    ***The file type of an object.***

    ### Writable Fields:
    `name`: Name of the file type. Examples:

    * Hierarchical Data Format version 5
    * Comma-separated values file
    * Microsoft Excel Open XML Spreadsheet

    `extension`: Filename extension. Examples:

    * h5
    * csv
    * xlsx

    The combination of `name` and `extension` are enforced to be unique.

    ### Read-only Fields:
    `url`: Reference to the instance of the `FileType`, final integer is the `FileType` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    """
    name = models.TextField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    extension = models.TextField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'extension'),
                name='unique_file_type_name_extension'),
        ]


class Issue(BaseModel):
    """
    ***A quality issue that can be attached to any `Object` or `ObjectComponent`.***

    ### Writable Fields:
    `severity`: Severity of this `Issue` as an integer, the larger the value the more severe the `Issue`

    `description`: Free text description of the `Issue`

    `component_issues`: List of `ObjectComponent` URLs which the `Issue` is associated with

    `uuid` (*optional*): UUID of the `Issue`. If not specified a UUID is generated automatically.

    ### Read-only Fields:
    `url`: Reference to the instance of the `Issue`, final integer is the `Issue` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """

    EXTRA_DISPLAY_FIELDS = ('component_issues',)
    SHORT_DESC_LENGTH = 40

    severity = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=False, blank=False)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)

    def short_desc(self):
        if self.description is None:
            return ''
        elif len(self.description) <= self.SHORT_DESC_LENGTH:
            return self.description
        else:
            return self.description[:self.SHORT_DESC_LENGTH - 3] + '...'

    def __str__(self):
        return '%s [Severity %s]' % (self.short_desc(), self.severity)


class Author(BaseModel):
    """
    ***Authors that can be associated with an `Object` usually for use with `ExternalObject`s to record paper authors,
    etc.***

    ### Writable Fields:
    `name` (*optional*): Full name or organisation name of the `Author`. Note that at least one of `name` or `identifier` must be specified.

    `identifier` (*optional*): Full URL of identifier (e.g. ORCiD or ROR ID) of the `Author`

    `uuid` (*optional*): UUID of the `Author`. If not specified a UUID is generated automatically.

    ### Read-only Fields:
    `url`: Reference to the instance of the `Author`, final integer is the `Author` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('name', 'identifier')

    name = NameField(null=True, blank=False)
    identifier = models.URLField(max_length=TEXT_FIELD_LENGTH, null=True, blank=False, unique=True)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_identifier_and_or_name",
                check=(
                    models.Q(identifier__isnull=True, name__isnull=False)
                    | models.Q(identifier__isnull=False, name__isnull=True)
                    | models.Q(identifier__isnull=False, name__isnull=False)
                ),
            )
        ]

    def save(self, *args, **kwargs):
        if self.identifier:
            self.uuid = UUID(hashlib.sha256(self.identifier.encode('utf-8')).hexdigest()[::2])
        super().save(*args, **kwargs)

    def __str__(self):
        if self.identifier:
            return self.identifier
        elif self.name:
            return self.name


class Object(BaseModel):
    """
    ***Core traceability object used to represent any data object such `DataProduct`, `CodeRepoRelease`, etc. ***

    ### Writable Fields:
    `description` (*optional*): Free text description of the `Object`

    `storage_location` (*optional*): The URL of the `StorageLocation` which is the location of the physical data of
     this object, if applicable

    `authors` (*optional*): List of `Author` URLs associated with this `Object`

    `uuid` (*optional*): UUID of the `Object`. If not specified a UUID is generated automatically.
    
    `file_type` (*optional*): `FileType` of this `Object`

    ### Read-only Fields:
    `url`: Reference to the instance of the `Object`, final integer is the `Object` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `components`: List of `ObjectComponents` API URLs associated with this `Object`

    `data_products`: List of `DataProduct` API URLs if one or more is associated with this `Object`

    `code_repo_release`: The `CodeRepoRelease` API URL if one is associated with this `Object`

    `quality_control`: The `QualityControl` API URL if one is associated with this `Object`

    `licences`: List of `Licence` API URLs associated with this `Object`

    `keywords`: List of `Keyword` API URLs associated with this `Object`
    """
    EXTRA_DISPLAY_FIELDS = (
        'components',
        'data_products',
        'code_repo_release',
        'quality_control',
        'licences',
        'keywords',
    )
    ADMIN_LIST_FIELDS = ('name', 'is_orphan')

    storage_location = models.ForeignKey('StorageLocation', on_delete=models.PROTECT, null=True, blank=True,
                                         related_name='location_for_object')
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    file_type = models.ForeignKey(FileType, on_delete=models.PROTECT, null=True, blank=True)
    authors = models.ManyToManyField(Author, blank=True)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Create ObjectComponent representing the whole object
        myself = Object.objects.get(id=self.id)
        ObjectComponent.objects.create(name='whole_object', object=myself, whole_object=True, updated_by=myself.updated_by)

    def name(self):
        if self.storage_location:
            return str(self.storage_location)
        else:
            return super().__str__()

    def is_orphan(self):
        """
        Test is this object is connected to anything else.
        """
        if self.storage_location:
            return False
        try:
            if self.data_products:
                return False
        except DataProduct.DoesNotExist:
            pass
        try:
            if self.code_repo_release:
                return False
        except CodeRepoRelease.DoesNotExist:
            pass
        return True

    def __str__(self):
        return self.name()


class UserAuthor(BaseModel):
    """
    ***A combination of an `Author` associated with a particular user.***

    ### Writable Fields:
    `user`: The API URL of the `User` to associate with this `UserAuthor`

    `author`: The API URL of the `Author` to associate with this `UserAuthor`

    ### Read-only Fields:
    `url`: Reference to the instance of the `UserAuthor`, final integer is the `UserAuthor` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT, related_name='users', null=False, unique=True)
    author = models.ForeignKey(Author, on_delete=models.PROTECT, null=False, blank=False)


class ObjectComponent(BaseModel):
    """
    ***A component of a `Object` being used as the input to a `CodeRun` or produced as an output from a
    `CodeRun`.***

    ### Writable Fields:
    `object`: The API URL of the `Object` to associate this `ObjectComponent` with

    `name`: Name of the `ObjectComponent`, unique in the context of `ObjectComponent` and its `Object` reference

    `description` (*optional*): Free text description of the `ObjectComponent`

    `issues` (*optional*): List of `Issues` URLs to associate with this `ObjectComponent`

    `whole_object` (*optional*): Specifies if this `ObjectComponent` refers to the whole object or not (by default this is `False`)

    ### Read-only Fields:
    `url`: Reference to the instance of the `ObjectComponent`, final integer is the `ObjectComponent` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `input_of`: List of `CodeRun` that the `ObjectComponent` is being used as an input to

    `output_of`: List of `CodeRun` that the `ObjectComponent` was created as an output of
    """
    ADMIN_LIST_FIELDS = ('object', 'name')
    EXTRA_DISPLAY_FIELDS = ('inputs_of', 'outputs_of')

    object = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='components', null=False)
    name = NameField(null=False, blank=False)
    issues = models.ManyToManyField(Issue, related_name='component_issues', blank=True)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    whole_object = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'name'),
                name='unique_object_component'),
        ]

    def __str__(self):
        return self.name


class CodeRun(BaseModel):
    """
    ***A code run along with its associated, code repo, configuration, input and outputs.***

    ### Writable Fields:
    `run_date`: datetime of the `CodeRun`

    `description` (*optional*): Free text description of the `CodeRun`

    `code_repo` (*optional*):  Reference to the `Object` associated with the `StorageLocation` where the code repository is stored

    `model_config`: Reference to the `Object` for the YAML configuration used for the `CodeRun`

    `submission_script`: Reference to the `Object` for the submission script used for the `CodeRun`

    `inputs`: List of `ObjectComponent` that the `CodeRun` used as inputs

    `outputs`: List of `ObjectComponent` that the `CodeRun` produced as outputs

    `uuid` (*optional*): UUID of the `CodeRun`. If not specified a UUID is generated automatically.

    ### Read-only Fields:
    `url`: Reference to the instance of the `ModelRun`, final integer is the `ModelRun` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('description',)

    code_repo = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='code_repo_of', null=True, blank=True)
    model_config = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='config_of', null=True, blank=True)
    submission_script = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='submission_script_of', null=False, blank=False)
    run_date = models.DateTimeField(null=False, blank=False)
    description = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    inputs = models.ManyToManyField(ObjectComponent, related_name='inputs_of', blank=True)
    outputs = models.ManyToManyField(ObjectComponent, related_name='outputs_of', blank=True)
    uuid = models.UUIDField(default=uuid4, editable=True, unique=True)


    def __str__(self):
        if self.code_repo:
            return '%s run %s' % (self.code_repo, self.description)
        return str(self.uuid)


###############################################################################
# Metadata objects

class StorageRoot(BaseModel):
    """
    ***The root location of a storage cache where model files are stored.***

    ### Writable Fields:

    `root`: URI (including protocol) to the root of a `StorageLocation`, which when prepended to a `StorageLocation`
    `path` produces a complete URI to a file. Examples:

    * https://somewebsite.com/
    * ftp://host/ (ftp://username:password@host:port/)
    * ssh://host/
    * file:///someroot/ (file://C:\)
    * github://org:repo@sha/ (github://org:repo/ (master))

    `local` (*optional*): Boolean indicating whether the `StorageRoot` is local or not (by default this is `False`)

    ### Read-only Fields:
    `url`: Reference to the instance of the `StorageRoot`, final integer is the `StorageRoot` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    EXTRA_DISPLAY_FIELDS = ('locations',)

    root = URIField(null=False, blank=False, unique=True)
    local = models.BooleanField(default=False)

    def __str__(self):
        return self.root


class StorageLocation(BaseModel):
    """
    ***The location of an item relative to a `StorageRoot`.***

    ### Writable Fields:
    `path`: Path from a `StorageRoot` `uri` to the item location, when appended to a `StorageRoot` `uri`
    produces a complete URI.

    `hash`: If `StorageLocation` references a file, this is the calculated SHA1 hash of the file. If `StorageLocation`
    references a directory *TODO: can't be git sha for validation (doesn't care about local changes), could be recursive
    sha1 of all files in the directory (excluding .git and things referenced in .gitignore), but needs to be OS independent
    (order matters) and things like logging output might affect it...*

    `public` (*optional*): Boolean indicating whether the `StorageLocation` is public or not (default is `True`)

    `storage_root`: Reference to the `StorageRoot` to append the `path` to.

    ### Read-only Fields:
    `url`: Reference to the instance of the `StorageLocation`, final integer is the `StorageLocation` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('storage_root', 'path')

    path = models.CharField(max_length=PATH_FIELD_LENGTH, null=False, blank=False)
    hash = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    public = models.BooleanField(default=True)
    storage_root = models.ForeignKey(StorageRoot, on_delete=models.PROTECT, related_name='locations')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('storage_root', 'hash', 'public'),
                name='unique_storage_location'),
        ]

    def full_uri(self):
        return self.storage_root.root + self.path

    def __str__(self):
        return self.full_uri()


class Namespace(BaseModel):
    """
    ***A namespace that can be used to group `DataProduct`s.***

    ### Writable Fields:
    `name`: The `Namespace` name

    `full_name` (*optional*): The full name of the `Namespace`

    `website` (*optional*): Website URL associated with the `Namespace`

    ### Read-only Fields:
    `url`: Reference to the instance of the `Namespace`, final integer is the `Namespace` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('name', 'full_name', 'website')

    name = NameField(null=False, blank=False)
    full_name = models.CharField(max_length=CHAR_FIELD_LENGTH, null=True, blank=True)
    website = models.URLField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name',),
                name='unique_name'),
            models.UniqueConstraint(
                fields=('full_name',),
                name='unique_full_name'),
        ]

    def __str__(self):
        return self.name


class DataProduct(BaseModel):
    """
    ***A data product that is used by or generated by a model.***

    ### Writable Fields:
    `name`: Name of the `DataProduct`, unique in the context of the triple (`name`, `version`, `namespace`)

    `version`: Version identifier of the `DataProduct`, must conform to semantic versioning syntax

    `object`: API URL of the associated `Object`

    `namespace`: API URL of the `Namespace` of the `DataProduct`

    ### Read-only Fields:
    `url`: Reference to the instance of the `DataProduct`, final integer is the `DataProduct` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `external_object`: `ExternalObject` API URL associated with this `DataProduct`
    """
    ADMIN_LIST_FIELDS = ('namespace', 'name', 'version')

    EXTRA_DISPLAY_FIELDS = (
        'external_object',
        'prov_report',
    )

    object = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='data_products')
    namespace = models.ForeignKey(Namespace, on_delete=models.PROTECT, related_name='data_products')
    name = NameField(null=False, blank=False)
    version = VersionField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('namespace', 'name', 'version'),
                name='unique_data_product'),
        ]

    def prov_report(self):
        url = reverse('prov_report', kwargs={'pk': self.id})
        return url

    def __str__(self):
        return '%s:%s version %s' % (self.namespace, self.name, self.version)


class ExternalObject(BaseModel):
    """
    *** An external data object, i.e. one that has comes from somewhere other than being generated as part of the
      modelling pipeline.***

    ### Writable Fields:
    `identifier`: Full URL of identifier (e.g. DataCite DOI) of the `ExternalObject`, unique in the context of the triple (`identifier`, `title`, `version`). At least one of `identifier` and `alternate_identifier` must be defined.

    `alternate_identifier`: Name of the `ExternalObject`, unique in the context of the quadruple (`alternate_identifier`, `alternate_identifier_type`, `title`, `version`). Unlike `identifier`, this is free text, not a url. For instance, it can be a locally unique name for a data resource within the domain of issue. It is associated with a `alternate_identifier_type` which describes its origin.

    `alternate_identifier_type`: Type of `alternate_identifier`, required if `alternate_identifier` is defined

    `primary_not_supplement` (*optional*): Boolean flag to indicate that the `ExternalObject` is a primary source

    `release_date`: Date-time the `ExternalObject` was released

    `title`: Title of the `ExternalObject`

    `description` (*optional*):  Free text description of the `ExternalObject`

    `data_product`: API URL of the associated `DataProduct`

    `original_store` (*optional*): `StorageLocation` that references the original location of this `ExternalObject`.
    For example, if the original data location could be transient and so the data has been copied to a more robust
    location, this would be the reference to the original data location.

    ### Read-only Fields:
    `url`: Reference to the instance of the `ExternalObject`, final integer is the `ExternalObject` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record

    `version`: Version identifier of the `DataProduct` associated with this `ExternalObject`
    """
    ADMIN_LIST_FIELDS = ('identifier', 'alternate_identifier', 'alternate_identifier_type', 'title', 'version')

    data_product = models.OneToOneField(DataProduct, on_delete=models.PROTECT, related_name='external_object')
    identifier = models.URLField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    alternate_identifier = models.CharField(max_length=CHAR_FIELD_LENGTH, null=True, blank=True)
    alternate_identifier_type = models.CharField(max_length=CHAR_FIELD_LENGTH, null=True, blank=True)
    primary_not_supplement = models.BooleanField(default=True)
    release_date = models.DateTimeField()
    title = models.CharField(max_length=CHAR_FIELD_LENGTH)
    description = models.TextField(max_length=TEXT_FIELD_LENGTH, null=True, blank=True)
    version = VersionField(editable=False)
    original_store = models.ForeignKey(StorageLocation, on_delete=models.PROTECT, related_name='original_store_of', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('identifier', 'alternate_identifier', 'alternate_identifier_type', 'title', 'version'),
                name='unique_external_object'),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_identifier_or_alternate_identifier",
                check=(
                    (models.Q(identifier__isnull=True) &
                     models.Q(alternate_identifier__isnull=False) &
                     models.Q(alternate_identifier_type__isnull=False)) | 
                    (models.Q(identifier__isnull=False) &
                     (models.Q(alternate_identifier__isnull=True) &
                      models.Q(alternate_identifier_type__isnull=True)) |
                     (models.Q(alternate_identifier__isnull=False) &
                      models.Q(alternate_identifier_type__isnull=False)))
                ),
            )
        ]

    def save(self, *args, **kwargs):
        # If version is not defined or is empty, use the version from the associated data product
        if not self.version or self.version == '':
            self.version = self.data_product.version
        super().save(*args, **kwargs)

    def __str__(self):
        if self.alternate_identifier:
            return '%s %s %s' % (self.alternate_identifier, self.title, self.version)
        else:
            return '%s %s %s' % (self.identifier, self.title, self.version)


class QualityControlled(BaseModel):
    """
    ***Marks that the associated `Object` has been quality controlled.***

    ### Writable Fields:
    `object`: API URL of the associated `Object`

    `document`: API URL of the `Object` representing the quality control document

    ### Read-only Fields:
    `url`: Reference to the instance of the `QualityControlled`, final integer is the `QualityControlled` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('object', 'document')

    object = models.OneToOneField(Object, on_delete=models.PROTECT, related_name='quality_control')
    document = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='quality_control_document')


class Keyword(BaseModel):
    """
    ***Keywords that can be associated with an `Object` usually for use with `ExternalObject`s to record paper keywords,
    etc.***

    ### Writable Fields:
    `object`: API URL of the associated `Object`

    `keyphrase`: Free text field for the key phrase to associate with the `Object`

    `identifier` (*optional*): URL of ontology annotation to associate with this `Keyword`

    ### Read-only Fields:
    `url`: Reference to the instance of the `Keyword`, final integer is the `Keyword` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('object', 'keyphrase')

    object = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='keywords')
    keyphrase = NameField(null=False, blank=False)
    identifier = models.URLField(max_length=TEXT_FIELD_LENGTH, null=True, blank=False, unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'keyphrase'),
                name='unique_keyword'),
        ]

    def __str__(self):
        return self.keyphrase


class Licence(BaseModel):
    """
    ***Licence that can be associated with an `Object` in case the code or data source has a specific licence that needs
    to be recorded.***

    ### Writable Fields:
    `object`: API URL of the associated `Object`

    `licence_info`: Free text field to store the information about the `Licence`

    `identifier` (*optional*): URL of the `Licence`

    ### Read-only Fields:
    `url`: Reference to the instance of the `Licence`, final integer is the `Licence` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('object',)

    object = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='licences')
    licence_info = models.TextField()
    identifier = models.URLField(max_length=TEXT_FIELD_LENGTH, null=True, blank=False, unique=True)


class CodeRepoRelease(BaseModel):
    """
    ***Information marking that an `Object` is an official release of a model code.***

    ### Writable Fields:
    `name`: Name of the `CodeRepoRelease`, unique in the context of the `CodeRepoRelease.version`

    `version`: Version identifier of the `CodeRepoRelease`, must conform to semantic versioning syntax, unique in the
    context of the `CodeRepoRelease.name`

    `object`: API URL of the associated `Object`

    `website` (*optional*): URL of the website for this code release, if applicable

    ### Read-only Fields:
    `url`: Reference to the instance of the `CodeRepoRelease`, final integer is the `CodeRepoRelease` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('name', 'version')

    object = models.OneToOneField(Object, on_delete=models.PROTECT, related_name='code_repo_release')
    name = NameField(null=False, blank=False)
    version = VersionField()
    website = models.URLField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('name', 'version'),
                name='unique_code_repo_release'),
        ]

    def __str__(self):
        return '%s version %s' % (self.name, self.version)


class KeyValue(BaseModel):
    """
    ***Free meta-data key-values associated with an `Object`.***

    ### Writable Fields:
    `object`: API URL of the associated `Object`

    `key`: Meta-data name

    `value`: Meta-data value

    ### Read-only Fields:
    `url`: Reference to the instance of the `KeyValue`, final integer is the `KeyValue` id

    `last_updated`: Datetime that this record was last updated

    `updated_by`: Reference to the user that updated this record
    """
    ADMIN_LIST_FIELDS = ('object', 'key')

    object = models.ForeignKey(Object, on_delete=models.PROTECT, related_name='metadata')
    key = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)
    value = models.CharField(max_length=CHAR_FIELD_LENGTH, null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('object', 'key'),
                name='unique_key_value'),
        ]

    def __str__(self):
        return self.key


def _is_base_model_subclass(name, cls):
    """
    Test if given class is a non-abstract subclasses of BaseModel
    """
    return (
            isinstance(cls, type)
            and issubclass(cls, BaseModel)
            and name not in ('BaseModel',)
    )


all_models = dict(
    (name, cls) for (name, cls) in globals().items() if _is_base_model_subclass(name, cls)
)
