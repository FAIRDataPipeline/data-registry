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

"""
from datetime import datetime
import json
import mimetypes
import tempfile

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
CLI_URL = "https://github.com/FAIRDataPipeline/FAIR-CLI"
REMOTE_STORAGE_ROOT = "https://data.fairdatapipeline.org/data/"


def _add_authors(authors, crate, entity, registry_url):
    """
    Add the authors to the crate and associate them with the entity.

    @param authors: a list of authors from the Author table
    @param crate: the RO Crate object
    @param entity: the entity to attach the authors to
    @param registry_url: a str containing the registry URL

    """
    cr_authors = []
    for author in authors:
        if author.identifier is not None:
            # if present use the identifier as the id
            author_id = author.identifier
        else:
            author_id = f"{registry_url}api/author/{author.id}"
        cr_author = crate.add(
            Person(crate, author_id, properties={"name": author.name})
        )

        cr_authors.append(cr_author)

    entity["author"] = cr_authors


def _add_data_extraction_action(crate, data_product, external_object, registry_url):
    """
    Create an RO Crate context entity to link the data product and external object.

    @param crate: the RO Crate object
    @param data_product: a data_product from the DataProduct table
    @param external_object: a external_object from the ExternalObject table
    @param registry_url: a str containing the registry URL

    @return an RO Crate file entity representing the data product

    """
    data_extraction_id = f"{registry_url}api/data_extraction/{data_product.id}"
    crate_data_extraction = ContextEntity(
        crate,
        data_extraction_id,
        properties={
            RO_TYPE: "CreateAction",
            "name": f"data extraction {data_product.id}",
            "startTime": data_product.last_updated.isoformat(),
            "description": "import/extract data from an external source",
        },
    )

    # the data product is an output of the transformation but an input to the code run
    # therefore output has been set to False
    crate_data_product = _get_local_data_product(
        crate, data_product, registry_url, False
    )

    crate_data_extraction["result"] = crate_data_product
    crate_data_extraction["object"] = _add_external_object(crate, external_object)

    # add the instrument
    properties = {
        RO_TYPE: "SoftwareApplication",
        "url": CLI_URL,
    }

    crate_instrument = ContextEntity(
        crate,
        CLI_URL,
        properties=properties,
    )

    crate_data_extraction["instrument"] = crate_instrument

    crate.add(crate_instrument)
    crate.add(crate_data_extraction)

    return crate_data_product


def _add_external_object(crate, external_object):
    """
    Create an RO Crate file entity representing the external object.

    @param crate_code_run: RO Crate entity representing the code run
    @param external_object: a external_object from the ExternalObject table

    @return an RO Crate file entity representing the external object

    """
    properties = {}
    properties["name"] = external_object.title
    properties["datePublished"] = str(external_object.release_date)

    if external_object.identifier:
        source_loc = external_object.identifier
    else:
        source_loc = external_object.alternate_identifier

    if external_object.description:
        properties["description"] = external_object.description

    crate_external_object = crate.add_file(source_loc, properties=properties)

    return crate_external_object


def _add_licenses(crate, crate_entity, file_object, registry_url):
    """
    Add licenses from the file_object to the crate_entity.

    @param crate: the RO Crate object
    @param crate_entity: an entity to add the license to
    @param file_object: an "object" from the database representing a file
    @param registry_url: a str containing the registry URL

    """
    license_entities = []
    try:
        licenses = file_object.licences.all()
    except AttributeError:
        licenses = []

    for license_ in licenses:
        if license_.identifier is not None:
            license_id = license_.identifier
        else:
            license_id = f"{registry_url}api/license/{license_.id}"

        license_entity = ContextEntity(
            crate,
            license_id,
            properties={
                RO_TYPE: "CreativeWork",
                "description": license_.licence_info,
                "identifier": license_id,
                "name": f"license {license_.id}",
            },
        )

        crate.add(license_entity)
        license_entities.append(license_entity)

    # where the crate_entity is a crate we are adding the licenses from all the
    # data products in turn, so there may already be some there
    if isinstance(crate_entity, ROCrate) and crate_entity.license is not None:
        license_entities.extend(crate_entity.license)

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


def _generate_ro_crate_from_dp(data_product, crate, registry_url, output_flag):
    """
    Update an RO Crate based around the data product.

    @param data_product: a data_product from the DataProduct table
    @param crate: the RO Crate object
    @param registry_url: a str containing the registry URL
    @param output_flag (bool): true if the data product is an output

    """
    crate_data_product = _get_data_product(
        crate, data_product, registry_url, output_flag
    )

    # add the activity, i.e. the code run
    components = data_product.object.components.all()

    for component in components:
        try:
            code_run = component.outputs_of.all()[0]
        except IndexError:
            # there is no code run for this component so we cannot add any more
            # provenance data
            continue

        input_files = []

        # add the code run
        crate_code_run = _get_code_run(
            crate_data_product, crate, code_run, registry_url
        )

        # add the code repo release
        if code_run.code_repo is not None:
            crate_code_run["instrument"] = _get_code_repo_release(
                crate, code_run.code_repo, registry_url
            )

        # add the model config
        if code_run.model_config is not None:
            model_config = _get_software(
                crate, code_run.model_config, registry_url, "model_config"
            )
            input_files.append(model_config)

        # add the submission script
        submission_script = _get_software(
            crate, code_run.submission_script, registry_url, "submission_script"
        )
        input_files.append(submission_script)

        # get data files
        input_files.extend(
            _get_data_products(crate, code_run.inputs.all(), registry_url, False)
        )

        # add input files
        crate_code_run["object"] = input_files


def _generate_ro_crate_from_cr(code_run, crate, registry_url):
    """
    Crate an RO Crate based around the code run.

    @param code_run: a code_run from the CodeRun table
    @param crate: the RO Crate object
    @param request: A request object

    @return the RO Crate object

    """
    input_files = []
    crate_data_product = None

    # add the code run
    crate_code_run = _get_code_run(crate_data_product, crate, code_run, registry_url)

    # add the code repo release
    if code_run.code_repo is not None:
        crate_code_run["instrument"] = _get_code_repo_release(
            crate, code_run.code_repo, registry_url
        )

    # add the model config
    if code_run.model_config is not None:
        model_config = _get_software(
            crate, code_run.model_config, registry_url, "model_config"
        )
        input_files.append(model_config)

    # add the submission script
    submission_script = _get_software(
        crate, code_run.submission_script, registry_url, "submission_script"
    )
    input_files.append(submission_script)

    # get data files
    input_files.extend(
        _get_data_products(crate, code_run.inputs.all(), registry_url, False)
    )

    # add input files
    crate_code_run["object"] = input_files

    # add output files
    crate_code_run["result"] = _get_data_products(
        crate, code_run.outputs.all(), registry_url, True
    )


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
        }
    else:
        properties = {
            RO_TYPE: "SoftwareApplication",
            "url": code_repo_id,
            "name": code_repo_release.name,
            "version": code_repo_release.version,
        }

    crate_code_release = ContextEntity(
        crate,
        code_repo_id,
        properties=properties,
    )

    _add_authors(
        code_repo.authors.all(),
        crate,
        crate_code_release,
        registry_url,
    )
    crate.add(crate_code_release)

    return crate_code_release


def _get_code_run(crate_data_product, crate, code_run, registry_url):
    """
    Create an RO Crate ContextEntity representing the code run and add the data product.

    @param crate_data_product: an RO data entity representing a data product
    @param crate: the RO Crate object
    @param code_run: a code_run object
    @param registry_url: a str containing the registry URL

    @return an RO Crate ContextEntity representing the code run

    """

    code_run_id = f"{registry_url}api/code_run/{code_run.id}"
    crate_code_run = ContextEntity(
        crate,
        code_run_id,
        properties={
            RO_TYPE: "CreateAction",
            "name": f"code run {code_run.id}",
            "startTime": code_run.run_date.isoformat(),
            "description": code_run.description,
        },
    )

    crate.add(crate_code_run)

    user_authors = models.UserAuthor.objects.filter(user=code_run.updated_by)

    if len(user_authors) == 0:
        agent_id = f"{registry_url}api/user/{code_run.updated_by.id}"
        crate.add(
            Person(
                crate, agent_id, properties={"name": code_run.updated_by.full_name()}
            )
        )

    else:
        # we have an author linked to the user
        if user_authors[0].author.identifier is not None:
            # if present use the identifier as the id
            agent_id = user_authors[0].author.identifier
        else:
            agent_id = f"{registry_url}api/author/{user_authors[0].author.id}"
        crate.add(
            Person(crate, agent_id, properties={"name": user_authors[0].author.name})
        )

    crate_code_run["agent"] = {"@id": agent_id}

    # add the data product to the code run
    crate_code_run["result"] = crate_data_product

    return crate_code_run


def _get_data_product(crate, data_product, registry_url, output):
    """
    Create an RO Crate file entity representing the data product.

    @param crate: RO Crate entity
    @param data_product: a data_product from the DataProduct table
    @param registry_url: a str containing the registry URL
    @param output (bool): true if the data product is an output

    @return an RO Crate file entity representing the data product

    """
    # Is it an external data product?
    crate_data_product = _get_external_object(crate, data_product, registry_url)

    if crate_data_product is None:
        crate_data_product = _get_local_data_product(
            crate, data_product, registry_url, output
        )

    _add_licenses(crate, crate_data_product, data_product.object, registry_url)

    _add_authors(
        data_product.object.authors.all(),
        crate,
        crate_data_product,
        registry_url,
    )

    return crate_data_product


def _get_data_products(crate, object_components, registry_url, output):
    """
    Add input data products to the RO Crate code run entity.

    @param crate: the RO Crate object
    @param object_components: a list of object_components from the ObjectComponent table
    @param registry_url: a str containing the registry URL
    @param output (bool): true if the data product is an output

    @return a list of RO Crate file entities representing the data products

    """
    all_data_products = []
    for component in object_components:
        obj = component.object
        data_products = obj.data_products.all()

        for data_product in data_products:
            crate_data_product = _get_data_product(
                crate, data_product, registry_url, output
            )
            all_data_products.append(crate_data_product)

    return all_data_products


def _get_external_object(crate, data_product, registry_url):
    """
    Create an RO Crate file entity for the given data product if it is an external
    product.

    If the data product is not an external product then `None` will be returned.

    @param crate: the RO Crate object
    @param data_product: a data_product from the DataProduct table
    @param registry_url: a str containing the registry URL

    @return an RO Crate file entity representing the external object, may be None

    """
    # check for external object linked to the data product
    try:
        external_object = data_product.external_object
    except (models.DataProduct.external_object.RelatedObjectDoesNotExist,):
        # no external object
        return None

    if external_object.primary_not_supplement is False:
        # the data_product was derived from the external object
        return _add_data_extraction_action(
            crate, data_product, external_object, registry_url
        )

    return _add_external_object(crate, external_object)


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


def _get_local_data_product(crate, data_product, registry_url, output):
    """
    Create an RO Crate file entity representing the data product.

    @param crate_code_run: RO Crate entity representing the code run
    @param data_product: a data_product from the DataProduct table
    @param registry_url: a str containing the registry URL
    @param output (bool): true if the data product is an output

    @return an RO Crate file entity representing the data product

    """
    if (
        data_product.object.storage_location.public is True
        and len(str(data_product.object.storage_location).split(FILE)) > 1
    ):
        source_loc = str(data_product.object.storage_location).split(FILE)[1]

        if output:
            dest_path = f"outputs/{source_loc.split('/')[-1]}"
        else:
            dest_path = f"inputs/data/{source_loc.split('/')[-1]}"

    elif (
        data_product.object.storage_location.public is True
        and settings.REMOTE_REGISTRY
    ):
        file_name = str(data_product.object.storage_location).split('/')[-1]

        _url = data_product.object.storage_location.full_uri()
        tmp = tempfile.NamedTemporaryFile(delete=False)
        response = requests.get(_url, allow_redirects = True, verify = False)
        open(tmp.name, mode= 'wb').write(response.content)

        source_loc = tmp.name

        if output:
            dest_path = f"outputs/{file_name}"
        else:
            dest_path = f"inputs/data/{file_name}"

    else:
        source_loc = f"{registry_url}api/storage_location/{data_product.object.storage_location.id}"
        dest_path = None

    encoding_format = _get_mime_type(data_product.object.file_type.extension)

    properties = {
        "name": data_product.name,
        "encodingFormat": encoding_format,
    }

    if data_product.object.storage_location.hash is not None:
        properties["sha1"] = data_product.object.storage_location.hash
        crate.metadata.extra_terms.update(SHA1)

    if data_product.object.description is not None:
        properties["description"] = data_product.object.description

    crate_data_product = crate.add_file(
        source_loc,
        dest_path=dest_path,
        properties=properties,
    )

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


def _get_software(crate, software_object, registry_url, software_type):
    """
    Create a file entity for the model configuration.

    @param crate: the RO Crate object
    @param software_object: an "object" representing the software
    @param registry_url: a str containing the registry URL
    @param software_type: a str containing the name of the type of software

    @return an RO Crate file entity representing the model configuration

    """
    _fetch_remote = False
    if (
        software_object.storage_location.public is True
        and len(str(software_object.storage_location).split(FILE)) > 1
    ):
        source_loc = str(software_object.storage_location).split(FILE)[1]
        dest_path = f"inputs/{software_type}/{source_loc.split('/')[-1]}"

    elif (
        software_object.storage_location.public is True
        and settings.REMOTE_REGISTRY
    ):
        file_name = str(software_object.storage_location).split('/')[-1]
        source_loc = software_object.object.storage_location.full_uri()

        dest_path = f"inputs/{software_type}/{file_name}"
        _fetch_remote = True

    else:
        source_loc = (
            f"{registry_url}api/storage_location/{software_object.storage_location.id}"
        )
        dest_path = None

    crate_software_object = crate.add_file(
        source_loc,
        dest_path=dest_path,
        properties={
            RO_TYPE: ["File", "SoftwareSourceCode"],
            "name": str(software_object.storage_location).split("/")[-1],
        },
        fetch_remote = _fetch_remote
    )

    if software_object.description is not None:
        crate_software_object["description"] = software_object.description

    if (
        software_object.file_type is not None
        and software_object.file_type.extension is not None
    ):
        crate_software_object["encodingFormat"] = _get_mime_type(
            software_object.file_type.extension
        )

    if software_object.storage_location.hash is not None:
        crate_software_object["sha1"] = software_object.storage_location.hash
        crate.metadata.extra_terms.update(SHA1)

    _add_licenses(crate, crate_software_object, software_object, registry_url)

    _add_authors(
        software_object.authors.all(),
        crate,
        crate_software_object,
        registry_url,
    )

    return crate_software_object


def generate_ro_crate_from_cr(code_run, depth, request):
    """
    Crate an RO Crate based around the code run.

    @param code_run: a code_run from the CodeRun table
    @param depth: The depth for the crate. How many levels of code runs to include.
    @param request: A request object

    @return the RO Crate object

    """
    mimetypes.init()
    registry_url = request.build_absolute_uri("/")

    crate = ROCrate()
    crate.publisher = "FAIR Data Pipeline"
    crate.datePublished = datetime.now().isoformat()
    crate.name = f"RO Crate for code run {code_run.id}"

    # add the licenses from each of the data products to the ROCrate
    for output in code_run.outputs.all():
        _add_licenses(crate, crate, output.object, registry_url)
    if crate.license is None:
        crate_license = _get_default_license(crate)
        crate.add(crate_license)
        crate.license = crate_license

    _add_metadata_license(crate)

    _generate_ro_crate_from_cr(code_run, crate, registry_url)

    if depth == 1:
        return crate

    input_data_products = _get_input_files_for_code_run(code_run)

    # add extra layers to the report if requested by the user
    while depth > 1:
        next_level_input_data_products = []

        for data_product in input_data_products:
            _generate_ro_crate_from_dp(data_product, crate, registry_url, False)

            next_level_input_data_products.extend(
                _get_input_files_for_data_product(data_product)
            )

        # reset the input files for the next level
        input_data_products = next_level_input_data_products
        depth = depth - 1

    return crate


def generate_ro_crate_from_dp(data_product, depth, request):
    """
    Crate an RO Crate based around the data product.

    @param data_product: a data_product from the DataProduct table
    @param depth: The depth for the crate. How many levels of code runs to include.
    @param request: A request object

    @return the RO Crate object

    """
    mimetypes.init()
    registry_url = request.build_absolute_uri("/")

    crate = ROCrate()
    crate.publisher = "FAIR Data Pipeline"
    crate.datePublished = datetime.now().isoformat()
    crate.name = f"RO Crate for {data_product.name}"
    crate.version = data_product.version

    _add_licenses(crate, crate, data_product.object, registry_url)
    if crate.license is None:
        crate_license = _get_default_license(crate)
        crate.add(crate_license)
        crate.license = crate_license

    _add_metadata_license(crate)

    # add the the main data product
    _generate_ro_crate_from_dp(data_product, crate, registry_url, True)

    if depth == 1:
        return crate

    input_data_products = _get_input_files_for_data_product(data_product)

    # add extra layers to the report if requested by the user
    while depth > 1:
        next_level_input_data_products = []

        for data_product in input_data_products:
            _generate_ro_crate_from_dp(data_product, crate, registry_url, False)

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
