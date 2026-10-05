"""
Produce a RO Crate of a CodeRun or DataProduct.

An RO Crate is research object (RO) that has been packaged up, in this case as a zip
file. This research object is centred around a `CodeRun` or the creation of a
`DataProduct`.

For a `CodeRun` all output `DataProduct` files are packaged up along with any other
local files that were used to produce them.
For the `DataProduct` the `DataProduct` file is packaged up along with any other local
files that were used to produce it.

Also included in the RO Crate is the metadata file `ro-crate-metadata.json`. The
`ro-crate-metadata.json` file is made available under the
[CC0 Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/).
Please note individual files may have their own licenses.
All of the packaged files are represented as `File` data entities in the metadata file.
A data product's file is at `<namespace>/<name>/<version>.<extension>`, which is how a
registry's data store lays out the files it pulls, whether or not its bytes are in the
crate; the working config and the submission script are under `model_config/` and
`submission_script/`. Every file carries the SHA-1 of its bytes (`sha1`) and the `uuid`
of its object in the registry (`identifier`).
Authors are identified by their ORCID, GitHub or other identifier where the
registry has one, else by their `uuid`, and an author with a ROR id is an `Organization`; a user with no author linked by a local id;
a licence by its URL, else by the file it applies to. Nothing is named by its row in
the registry.
An issue raised against a file is a line on the file's entity, under the registry's
own term `issue`: the issue's uuid, its severity and its description, in that order.

What travels with each file is chosen by the request's `level`, each level including the
one before: 1, the hash and any persistent identifier, with the source's metadata; 2,
the address the registry's copy can be downloaded from (`contentUrl`); 3, the bytes of
every public file that no primary source stands for; 4, the bytes of every public file.
A zip defaults to level 3 and the JSON-LD to level 1. The JSON-LD never holds a file, so
the working config and the submission script, which every zip packs, are metadata alone
there. A run's outputs outside the crate's provenance are described at level 1 whatever
was asked, and a file that is not public is named by its storage location, as before.

A data product registered from an external source is in the crate as itself, and the
source is a `Dataset` entity, one per source the registry knows: its `identifier` is
the source's persistent identifier (a DOI) where it has one, its `name` the title that
tells the files registered under one identifier apart, with the source's own `version`,
`datePublished`, `description`, alternate identifier and, where the registry recorded
where the file was fetched from, `contentUrl`. Where the registered bytes are the
identified item, or one of its files (a primary source), the data product's `sameAs`
points at the source; where the data was requested or derived from the source, so that
no identifier yields the same bytes again (a supplementary source, e.g. an extract made
for a request), its `isBasedOn` does. A deposit registered as a whole, as the data
product with no file that a fetch run reads, is a source of its own, and the sources of
the files under its identifier are `isPartOf` it. The run that produced a sourced file
is the step between source and file; a file registered without one has a source and no
action.

The `CodeRun` has been modelled as a RO Crate `ContextEntity` of type `CreateAction`,
see
[software-used-to-create-files](https://www.researchobject.org/ro-crate/1.1/provenance.html#software-used-to-create-files).

A `CreateAction` has `instrument` property, which represents the software used to
generate the product. For our purposes `instrument` is the link to the repo, at
the commit that was run: the commit is its `softwareVersion`, and its `url` is the
repo.

A `DataProduct` file has the `name` and `version` of the `DataProduct`, and its
`namespace` is an entity of type `Namespace`, whose `name` is the name of the
`Namespace`, `alternateName` its full name and `url` its website.

`CreateAction` (`CodeRun`) properties:

* `identifier`: the `uuid` of the `CodeRun`, which is also in its `@id`
* `instrument`: the code repo at the commit that was run, or the submission script for a
  run without a repo
* `object`: the input files, the working config and the submission script
* `model_configuration`, `submission_script`: which of those files is which
* `result`: every output of the run; those outside the crate's provenance are described
  but not packaged
* `agent`: the `Author`

The crate conforms to Process Run Crate 0.6 (https://w3id.org/ro/wfrun/process/0.6).
The RO Crate is available as a `zip` file.

The contents of the ro-crate-metadata file can be viewed as `JSON` or `JSON-LD`.

"""

from datetime import datetime
import json
import mimetypes
import os
import tempfile
from urllib.parse import quote

from django.conf import settings as django_settings
from rocrate.model.person import Person
from rocrate.rocrate import ContextEntity
from rocrate.rocrate import ROCrate

from data_management.views import external_object

import requests

from . import models
from . import settings


RO_TYPE = "@type"
FILE = "file:"
SHA1 = {"sha1": "https://w3id.org/ro/terms/workflow-run#sha1"}
PROCESS_RUN_CRATE = "https://w3id.org/ro/wfrun/process/0.6"
REMOTE_STORAGE_ROOT = "https://data.fairdatapipeline.org/data/"


def _add_authors(authors, crate, entity):
    """
    Add the authors to the crate and associate them with the entity.

    @param authors: a list of authors from the Author table
    @param crate: the RO Crate object
    @param entity: the entity to attach the authors to

    """
    entity["author"] = [_add_author(crate, author) for author in authors]


# The agent for an author: an Organization when a ROR id identifies it, else a Person;
# identified by the author's identifier (an ORCID, a GitHub account, a ROR id) where
# there is one, and otherwise by the author's uuid
def _add_author(crate, author):
    if author.identifier is not None:
        author_id = author.identifier
        properties = {"name": author.name}
    else:
        author_id = f"urn:uuid:{author.uuid}"
        properties = {"name": author.name, "identifier": str(author.uuid)}
    if author.is_organisation():
        properties[RO_TYPE] = "Organization"
        return crate.add(ContextEntity(crate, author_id, properties=properties))
    return crate.add(Person(crate, author_id, properties=properties))


# A source's entity id: its identity in the registry, which is not a row of it
def _source_id(external_object):
    identifier = external_object.identifier or external_object.alternate_identifier
    return "#source-" + quote(
        f"{identifier}:{external_object.title}@{external_object.version}", safe=""
    )


# The deposit a source belongs to: the primary source under the same identifier that
# is registered as a data product with no file, as a fetch run reads one
def _deposit_of(external_object):
    if not external_object.identifier:
        return None
    if external_object.data_products.filter(object__storage_location=None).exists():
        return None
    return (
        models.ExternalObject.objects.filter(
            identifier=external_object.identifier,
            primary_not_supplement=True,
            data_products__object__storage_location=None,
        )
        .exclude(pk=external_object.pk)
        .first()
    )


def _add_external_object(crate, external_object):
    """
    Create an RO Crate entity representing the external object, or return it.

    A source is described once however many data products were registered from it.

    @param crate: the RO Crate object
    @param external_object: a external_object from the ExternalObject table

    @return an RO Crate entity representing the external object

    """
    source_id = _source_id(external_object)
    if source_id in crate:
        return crate.get(source_id)

    properties = {
        RO_TYPE: "Dataset",
        "name": external_object.title,
        "version": str(external_object.version),
        "datePublished": external_object.release_date.isoformat(),
    }

    if external_object.identifier:
        properties["identifier"] = external_object.identifier

    if external_object.alternate_identifier:
        properties[_fair_term(crate, "alternate_identifier")] = (
            external_object.alternate_identifier
        )
        properties[_fair_term(crate, "alternate_identifier_type")] = (
            external_object.alternate_identifier_type
        )

    if external_object.description:
        properties["description"] = external_object.description

    if external_object.original_store is not None:
        # where the registry fetched the file from, which outlives the registry
        properties["contentUrl"] = external_object.original_store.full_uri()

    crate_external_object = crate.add(
        ContextEntity(crate, source_id, properties=properties)
    )

    deposit = _deposit_of(external_object)
    if deposit is not None:
        crate_external_object["isPartOf"] = _add_external_object(crate, deposit)

    return crate_external_object


def _add_issues(crate, entity, obj):
    """
    List an object's issues on its entity, one line each.

    The lines are the registry's own term `issue`, and each gives the issue's uuid,
    then its severity, then its description, in that order so that a reader can
    parse them.

    @param crate: the RO Crate object
    @param entity: the RO Crate entity representing the object
    @param obj: an object from the Object table

    """
    lines = {}
    for component in obj.components.all():
        for issue in component.issues.all():
            lines[issue.uuid] = (
                f"{issue.uuid} severity {issue.severity}: {issue.description}"
            )
    if lines:
        entity[_fair_term(crate, "issue")] = list(lines.values())


def _add_licenses(crate, crate_entity, file_object):
    """
    Add licenses from the file_object to the crate_entity.

    A licence is identified by its URL, or, given as text alone, by the file it
    applies to.

    @param crate: the RO Crate object
    @param crate_entity: an entity to add the license to
    @param file_object: an "object" from the database representing a file

    """
    license_entities = []
    try:
        licenses = file_object.licences.all()
    except AttributeError:
        licenses = []

    unidentified = 0
    for license_ in licenses:
        properties = {RO_TYPE: "CreativeWork", "name": license_.licence_info}
        if license_.identifier is not None:
            license_id = license_.identifier
            properties["identifier"] = license_id
        else:
            unidentified += 1
            license_id = f"#licence-{file_object.uuid}"
            if unidentified > 1:
                license_id = f"{license_id}-{unidentified}"

        license_entity = ContextEntity(crate, license_id, properties=properties)

        crate.add(license_entity)
        license_entities.append(license_entity)

    # where the crate_entity is a crate we are adding the licenses from all the
    # data products in turn, so there may already be some there - one, or a list
    if isinstance(crate_entity, ROCrate) and crate_entity.license is not None:
        existing = crate_entity.license
        license_entities.extend(existing if isinstance(existing, list) else [existing])

    # a licence reached by several routes is listed once
    license_entities = list(
        {entity.id: entity for entity in license_entities}.values()
    )

    if len(license_entities) == 1:
        if isinstance(crate_entity, ROCrate):
            crate_entity.license = license_entities[0]
        else:
            crate_entity["license"] = license_entities[0]

    elif len(license_entities) > 1:
        if isinstance(crate_entity, ROCrate):
            crate_entity.license = license_entities
        else:
            crate_entity["license"] = license_entities


def _add_metadata_license(crate):
    """
    Add a licenses to the ro-crate-metadata.json file.

    @param crate: the RO Crate object

    """
    url = "https://creativecommons.org/publicdomain/zero/1.0/"
    metadata_license = ContextEntity(
        crate,
        url,
        properties={
            RO_TYPE: "CreativeWork",
            "description": "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
            "identifier": url,
            "name": "CC0 Public Domain Dedication",
        },
    )

    crate.add(metadata_license)
    crate.metadata["license"] = metadata_license


# A data product's path in the crate: its namespace, name and version, which is how
# a registry's data store lays out the files it pulls, plus the file's extension
def _data_product_path(data_product):
    path = (
        f"{quote(data_product.namespace.name, safe='')}/"
        f"{quote(data_product.name, safe='/')}/"
        f"{quote(data_product.version, safe='')}"
    )
    extension = _extension(data_product.object)
    return path if extension is None else f"{path}.{extension}"


# The extension of an object's file type, or None when it has neither
def _extension(obj):
    if obj.file_type is None:
        return None
    return obj.file_type.extension or None


# Declare the crate's conformance to Process Run Crate, whose terms its code runs use
def _declare_profile(crate):
    profile = crate.add(
        ContextEntity(
            crate,
            PROCESS_RUN_CRATE,
            properties={
                RO_TYPE: "CreativeWork",
                "name": "Process Run Crate",
                "version": "0.6",
            },
        )
    )
    crate.root_dataset["conformsTo"] = profile


# Define one of the registry's own terms in the crate's context, as in the provenance
# report (the central registry's vocab/ page defines them), and return it as the
# property name to use
def _fair_term(crate, name):
    central_registry_url = django_settings.CENTRAL_REGISTRY_URL
    if not central_registry_url.endswith("/"):
        central_registry_url = f"{central_registry_url}/"
    crate.metadata.extra_terms[name] = f"{central_registry_url}vocab/#{name}"
    return name


def _get_default_license(crate):
    """
    Get a ContextEntity representing a CC BY 4.0 license.

    @return a ContextEntity representing a CC BY 4.0 license

    """
    url = "https://creativecommons.org/licenses/by/4.0/"
    default_license = ContextEntity(
        crate,
        url,
        properties={
            RO_TYPE: "CreativeWork",
            "description": "Attribution 4.0 International",
            "identifier": url,
            "name": "CC BY 4.0",
        },
    )

    return default_license


def _generate_ro_crate_from_dp(data_product, crate, registry_url, level):
    """
    Update an RO Crate based around the data product.

    @param data_product: a data_product from the DataProduct table
    @param crate: the RO Crate object
    @param registry_url: a str containing the registry URL
    @param level: an int, what travels with each file (see the module docstring)

    """
    _get_data_product(crate, data_product, registry_url, level)

    # add the activity, i.e. the code run
    components = data_product.object.components.all()
    code_run_ids = set()

    for component in components:
        try:
            code_run = component.outputs_of.all()[0]
        except IndexError:
            # there is no code run for this component so we cannot add any more
            # provenance data
            continue

        # the components of a data product are usually outputs of the same code run
        if code_run.id in code_run_ids:
            continue
        code_run_ids.add(code_run.id)

        # a run reached before, through another of its outputs, is complete already:
        # its first visit listed every output
        if f"urn:uuid:{code_run.uuid}" in crate:
            continue

        crate_code_run = _get_code_run(crate, code_run, registry_url)
        _add_code_run_files(crate, crate_code_run, code_run, registry_url, level)

        # every output of the run; those outside this crate's provenance are
        # described at level 1, with neither bytes nor address, whatever was asked
        crate_code_run["result"] = _get_data_products(
            crate, code_run.outputs.all(), registry_url, 1
        )


def _generate_ro_crate_from_cr(code_run, crate, registry_url, level):
    """
    Crate an RO Crate based around the code run.

    @param code_run: a code_run from the CodeRun table
    @param crate: the RO Crate object
    @param registry_url: a str containing the registry URL
    @param level: an int, what travels with each file (see the module docstring)

    """
    crate_code_run = _get_code_run(crate, code_run, registry_url)
    _add_code_run_files(crate, crate_code_run, code_run, registry_url, level)

    # add output files
    crate_code_run["result"] = _get_data_products(
        crate, code_run.outputs.all(), registry_url, level
    )


def _add_code_run_files(crate, crate_code_run, code_run, registry_url, level):
    """
    Add a code run's software and inputs to its CreateAction.

    The repo at the commit that was run is the instrument, or the submission script
    for a run without a repo. The working config and the submission script are among
    the run's objects, and the run names which is which.

    @param crate: the RO Crate object
    @param crate_code_run: the RO Crate ContextEntity representing the code run
    @param code_run: a code_run from the CodeRun table
    @param registry_url: a str containing the registry URL
    @param level: an int, what travels with each file (see the module docstring)

    """
    input_files = []

    if code_run.model_config is not None:
        model_config = _get_software(
            crate, code_run.model_config, registry_url, "model_config", level
        )
        crate_code_run[_fair_term(crate, "model_configuration")] = model_config
        input_files.append(model_config)

    submission_script = _get_software(
        crate, code_run.submission_script, registry_url, "submission_script", level
    )
    crate_code_run[_fair_term(crate, "submission_script")] = submission_script
    input_files.append(submission_script)

    if code_run.code_repo is not None:
        crate_code_run["instrument"] = _get_code_repo_release(
            crate, code_run.code_repo, registry_url
        )
    else:
        crate_code_run["instrument"] = submission_script

    input_files.extend(
        _get_data_products(crate, code_run.inputs.all(), registry_url, level)
    )
    crate_code_run["object"] = input_files


def _get_code_repo_release(crate, code_repo, registry_url):
    """
    Create an RO Crate ContextEntity representing a code repo release.

    @param crate: the RO Crate object
    @param code_repo: a code_repo object
    @param registry_url: a str containing the registry URL

    @return an RO Crate ContextEntity representing the code repo release

    """

    code_repo_id = str(code_repo.storage_location)

    try:
        code_repo_release = code_repo.code_repo_release
    except models.Object.code_repo_release.RelatedObjectDoesNotExist:
        code_repo_release = None

    if code_repo_release is None:
        properties = {
            RO_TYPE: "SoftwareApplication",
            "url": code_repo_id,
            "name": (
                code_repo.storage_location.path
                if code_repo.storage_location is not None
                else str(code_repo.uuid)
            ),
        }
    else:
        properties = {
            RO_TYPE: "SoftwareApplication",
            "url": code_repo_id,
            "name": code_repo_release.name,
            "softwareVersion": code_repo_release.version,
        }

    if code_repo.storage_location is not None:
        # the hash of a repo's location is the commit that was run, and the same repo
        # at another commit is different software, so the commit is in the id; it
        # also stands as the version where there is no release
        commit = code_repo.storage_location.hash
        code_repo_id = f"{code_repo_id}#{commit}"
        if code_repo_release is None:
            properties["version"] = commit

    crate_code_release = ContextEntity(
        crate,
        code_repo_id,
        properties=properties,
    )

    _add_authors(
        code_repo.authors.all(),
        crate,
        crate_code_release,
    )
    _add_issues(crate, crate_code_release, code_repo)
    crate.add(crate_code_release)

    return crate_code_release


def _get_code_run(crate, code_run, registry_url):
    """
    Create an RO Crate ContextEntity representing the code run.

    @param crate: the RO Crate object
    @param code_run: a code_run object
    @param registry_url: a str containing the registry URL

    @return an RO Crate ContextEntity representing the code run

    """

    # the uuid identifies a code run in every registry
    code_run_id = f"urn:uuid:{code_run.uuid}"
    crate_code_run = ContextEntity(
        crate,
        code_run_id,
        properties={
            RO_TYPE: "CreateAction",
            "name": f"code run {code_run.uuid}",
            "identifier": str(code_run.uuid),
            "startTime": code_run.run_date.isoformat(),
            "description": code_run.description,
        },
    )

    crate.add(crate_code_run)

    user_authors = models.UserAuthor.objects.filter(user=code_run.updated_by)

    if len(user_authors) == 0:
        # a user has no identity beyond one registry: a local id, and the name
        user = code_run.updated_by
        agent = crate.add(
            Person(
                crate,
                f"#user-{quote(user.username, safe='')}",
                properties={"name": user.full_name()},
            )
        )
    else:
        agent = _add_author(crate, user_authors[0].author)

    crate_code_run["agent"] = agent

    return crate_code_run


def _get_data_product(crate, data_product, registry_url, level):
    """
    Create an RO Crate file entity representing the data product.

    A data product registered from an external source is linked to that source: by
    `sameAs` where the registered bytes are the identified item or one of its files,
    and by `isBasedOn` where the data was requested or derived from the source.

    @param crate: RO Crate entity
    @param data_product: a data_product from the DataProduct table
    @param registry_url: a str containing the registry URL
    @param level: an int, what travels with the file (see the module docstring)

    @return an RO Crate file entity representing the data product

    """
    crate_data_product = _get_local_data_product(
        crate, data_product, registry_url, level
    )

    external_object = data_product.external_object
    if external_object is not None:
        relation = "sameAs" if external_object.primary_not_supplement else "isBasedOn"
        crate_data_product[relation] = _add_external_object(crate, external_object)

    _add_licenses(crate, crate_data_product, data_product.object)

    _add_authors(
        data_product.object.authors.all(),
        crate,
        crate_data_product,
    )

    return crate_data_product


def _get_data_products(crate, object_components, registry_url, level):
    """
    Add the data products of a code run's components to the RO Crate.

    @param crate: the RO Crate object
    @param object_components: a list of object_components from the ObjectComponent table
    @param registry_url: a str containing the registry URL
    @param level: an int, what travels with each file (see the module docstring)

    @return a list of RO Crate file entities representing the data products

    """
    all_data_products = []
    data_product_ids = set()
    for component in object_components:
        for data_product in component.object.data_products.all():
            # a run that reads or writes several components of a file lists each of
            # its data products once
            if data_product.id in data_product_ids:
                continue
            data_product_ids.add(data_product.id)
            all_data_products.append(
                _get_data_product(crate, data_product, registry_url, level)
            )

    return all_data_products


def _get_input_files_for_code_run(code_run):
    """
    Get the list of data products used to produce the given code run.

    @param code_run: a code run from the CodeRun table

    @return a list of data products

    """
    all_code_run_inputs = []
    for component in code_run.inputs.all():
        all_code_run_inputs.extend(component.object.data_products.all())

    return all_code_run_inputs


def _get_input_files_for_data_product(data_product):
    """
    Get the list of data products used to produce the given data product.

    @param data_product: a data product from the DataProduct table

    @return a list of data products

    """
    all_input_files = []

    for initial_dp_component in data_product.object.components.all():
        try:
            code_run = initial_dp_component.outputs_of.all()[0]
        except IndexError:
            # there is no code run for this component so we cannot add any more
            # data inputs data
            continue

        # now get the inputs for this code run
        all_code_run_inputs = []
        for component in code_run.inputs.all():
            all_code_run_inputs.extend(component.object.data_products.all())

        all_input_files.extend(all_code_run_inputs)

    return all_input_files


def _get_local_data_product(crate, data_product, registry_url, level):
    """
    Create an RO Crate file entity representing the data product.

    The entity is the data product's, at the path its namespace, name and version
    give it, whether or not the file's bytes are in the crate: two data products
    with the same bytes are two entities with one hash, and two names for one
    object two entities with one identifier.

    @param crate: the RO Crate object
    @param data_product: a data_product from the DataProduct table
    @param registry_url: a str containing the registry URL
    @param level: an int, what travels with the file (see the module docstring); at
        level 1 a file the crate already holds is left as it is

    @return an RO Crate file entity representing the data product

    """
    obj = data_product.object
    storage_location = obj.storage_location
    dest_path = _data_product_path(data_product)
    if level == 1 and dest_path in crate:
        return crate.dereference(dest_path)

    # bytes travel from level 3, unless a primary source stands for them until level 4
    pack = level >= 4 or (level == 3 and not _has_primary_source(data_product))
    _fetch_remote = False
    if storage_location is None:
        # an object with no file: the data product is recorded, with nothing to pack
        source_loc = None

    elif storage_location.public is not True:
        # a file that is not public is still named by its storage location
        source_loc = f"{registry_url}api/storage_location/{storage_location.id}"
        dest_path = None

    elif not pack:
        source_loc = None

    elif len(str(storage_location).split(FILE)) > 1:
        source_loc = str(storage_location).split(FILE)[1]

        if not os.path.isfile(source_loc):
            source_loc = None

    elif settings.REMOTE_REGISTRY:
        source_loc = storage_location.full_uri()
        _fetch_remote = True

    else:
        # public, but on a root this registry cannot read: recorded, not packed
        source_loc = None

    properties = {
        "name": data_product.name,
        "version": data_product.version,
        "identifier": str(obj.uuid),
    }

    extension = _extension(obj)
    if extension is not None:
        properties["encodingFormat"] = _get_mime_type(extension)

    if storage_location is not None and storage_location.hash is not None:
        properties["sha1"] = storage_location.hash
        crate.metadata.extra_terms.update(SHA1)

    if level >= 2 and storage_location is not None and storage_location.public is True:
        properties["contentUrl"] = storage_location.full_uri()

    if obj.description is not None:
        properties["description"] = obj.description

    crate_data_product = crate.add_file(
        source_loc,
        dest_path=dest_path,
        properties=properties,
        fetch_remote=_fetch_remote,
    )
    crate_data_product["namespace"] = _get_namespace(crate, data_product.namespace)
    _add_issues(crate, crate_data_product, obj)

    return crate_data_product


def _get_mime_type(extension):
    """
    Get the mime type for the given extension.

    @param extension(str): the file extension

    @result the mime type of the extension

    """
    try:
        mime_type = mimetypes.types_map[f".{extension}"]
    except KeyError:
        # mime type not found, use extension
        mime_type = extension
    return mime_type


def _get_namespace(crate, namespace):
    """
    Create an RO Crate ContextEntity representing a namespace.

    Its id is made from its name, which is what identifies a namespace in every
    registry.

    @param crate: the RO Crate object
    @param namespace: a namespace from the Namespace table

    @return an RO Crate ContextEntity representing the namespace

    """
    properties = {RO_TYPE: _fair_term(crate, "Namespace"), "name": namespace.name}
    if namespace.full_name:
        properties["alternateName"] = namespace.full_name
    if namespace.website:
        properties["url"] = namespace.website

    _fair_term(crate, "namespace")
    return crate.add(
        ContextEntity(
            crate,
            f"#namespace-{quote(namespace.name, safe='')}",
            properties=properties,
        )
    )


def _get_software(crate, software_object, registry_url, software_type, level):
    """
    Create a file entity for the working config or the submission script.

    Its bytes are packed whenever the registry can read them, at every level.

    @param crate: the RO Crate object
    @param software_object: an "object" representing the software
    @param registry_url: a str containing the registry URL
    @param software_type: a str containing the name of the type of software
    @param level: an int, what travels with the file (see the module docstring)

    @return an RO Crate file entity representing the software

    """
    storage_location = software_object.storage_location
    if storage_location is None:
        # an object with no file can only be named by its uuid
        file_name = str(software_object.uuid)
    else:
        file_name = str(storage_location).split("/")[-1]
    dest_path = f"{software_type}/{file_name}"
    _fetch_remote = False
    if storage_location is None:
        source_loc = None

    elif storage_location.public is not True:
        # a file that is not public is still named by its storage location
        source_loc = f"{registry_url}api/storage_location/{storage_location.id}"
        dest_path = None

    elif len(str(storage_location).split(FILE)) > 1:
        source_loc = str(storage_location).split(FILE)[1]

        if not os.path.isfile(source_loc):
            source_loc = None

    elif settings.REMOTE_REGISTRY:
        # a remote's files are named by their hash alone
        extension = _extension(software_object)
        if extension is not None:
            dest_path = f"{dest_path}.{extension}"
        source_loc = storage_location.full_uri()
        _fetch_remote = True

    else:
        # public, but on a root this registry cannot read: recorded, not packed
        source_loc = None

    crate_software_object = crate.add_file(
        source_loc,
        dest_path=dest_path,
        properties={
            RO_TYPE: ["File", "SoftwareSourceCode"],
            "name": file_name,
            "identifier": str(software_object.uuid),
        },
        fetch_remote=_fetch_remote,
    )

    if software_object.description is not None:
        crate_software_object["description"] = software_object.description

    extension = _extension(software_object)
    if extension is not None:
        crate_software_object["encodingFormat"] = _get_mime_type(extension)

    if storage_location is not None and storage_location.hash is not None:
        crate_software_object["sha1"] = storage_location.hash
        crate.metadata.extra_terms.update(SHA1)

    if level >= 2 and storage_location is not None and storage_location.public is True:
        crate_software_object["contentUrl"] = storage_location.full_uri()

    _add_licenses(crate, crate_software_object, software_object)

    _add_authors(
        software_object.authors.all(),
        crate,
        crate_software_object,
    )
    _add_issues(crate, crate_software_object, software_object)

    return crate_software_object


# Whether a data product was registered from a source whose identifier it is a copy of
def _has_primary_source(data_product):
    external_object = data_product.external_object
    return external_object is not None and external_object.primary_not_supplement


def generate_ro_crate_from_cr(code_run, depth, request, level):
    """
    Crate an RO Crate based around the code run.

    @param code_run: a code_run from the CodeRun table
    @param depth: The depth for the crate. How many levels of code runs to include.
    @param request: A request object
    @param level: an int, what travels with each file (see the module docstring)

    @return the RO Crate object

    """
    mimetypes.init()
    registry_url = request.build_absolute_uri("/")

    crate = ROCrate()
    crate.publisher = "FAIR Data Pipeline"
    crate.datePublished = datetime.now().isoformat()
    crate.name = f"RO Crate for code run {code_run.uuid}"

    # add the licenses from each of the data products to the ROCrate
    for output in code_run.outputs.all():
        _add_licenses(crate, crate, output.object)
    if crate.license is None:
        crate_license = _get_default_license(crate)
        crate.add(crate_license)
        crate.license = crate_license

    _add_metadata_license(crate)
    _declare_profile(crate)

    _generate_ro_crate_from_cr(code_run, crate, registry_url, level)

    if depth == 1:
        return crate

    input_data_products = _get_input_files_for_code_run(code_run)

    # a data product reached by several routes is added once, at the first level it
    # is reached
    data_product_ids = set()

    # add extra layers to the report if requested by the user
    while depth > 1:
        next_level_input_data_products = []

        for data_product in input_data_products:
            if data_product.id in data_product_ids:
                continue
            data_product_ids.add(data_product.id)

            _generate_ro_crate_from_dp(data_product, crate, registry_url, level)

            next_level_input_data_products.extend(
                _get_input_files_for_data_product(data_product)
            )

        # reset the input files for the next level
        input_data_products = next_level_input_data_products
        depth = depth - 1

    return crate


def generate_ro_crate_from_dp(data_product, depth, request, level):
    """
    Crate an RO Crate based around the data product.

    @param data_product: a data_product from the DataProduct table
    @param depth: The depth for the crate. How many levels of code runs to include.
    @param request: A request object
    @param level: an int, what travels with each file (see the module docstring)

    @return the RO Crate object

    """
    mimetypes.init()
    registry_url = request.build_absolute_uri("/")

    crate = ROCrate()
    crate.publisher = "FAIR Data Pipeline"
    crate.datePublished = datetime.now().isoformat()
    crate.name = f"RO Crate for {data_product.name}"

    _add_licenses(crate, crate, data_product.object)
    if crate.license is None:
        crate_license = _get_default_license(crate)
        crate.add(crate_license)
        crate.license = crate_license

    _add_metadata_license(crate)
    _declare_profile(crate)

    # add the the main data product
    _generate_ro_crate_from_dp(data_product, crate, registry_url, level)

    if depth == 1:
        return crate

    input_data_products = _get_input_files_for_data_product(data_product)

    # a data product reached by several routes is added once, at the first level it
    # is reached
    data_product_ids = {data_product.id}

    # add extra layers to the report if requested by the user
    while depth > 1:
        next_level_input_data_products = []

        for data_product in input_data_products:
            if data_product.id in data_product_ids:
                continue
            data_product_ids.add(data_product.id)

            _generate_ro_crate_from_dp(data_product, crate, registry_url, level)

            next_level_input_data_products.extend(
                _get_input_files_for_data_product(data_product)
            )

        # reset the input files for the next level
        input_data_products = next_level_input_data_products
        depth = depth - 1

    return crate


def serialize_ro_crate(crate, format_):
    if format_ == "zip":
        tmp = tempfile.NamedTemporaryFile()
        file_name = crate.write_zip(f"{tmp.name}.zip")
        zip_file = open(file_name, "rb")
        return zip_file
    if format_ == "json-ld":
        return json.dumps(crate.metadata.generate())
    return crate.metadata.generate()
