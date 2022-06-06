"""
Produce a RO Crate of a CodeRun or DataProduct.

An RO Crate is research object (RO) that has been packaged up, in this case as a zip
file. This research object is centred around a `CodeRun` or the creation of a
`DataProduct`.

For a `CodeRun` all output `DataProduct` files are packaged up along with any other
local files that were used to produce them.
For the `DataProduct` the `DataProduct` file is packaged up along with any other local
files that were used to produce it.

Also included in the RO Crate is the metadata file `ro-crate-metadata.json`.
All of the packaged files are represented as `File` data entities in the metadata file.
Any external files will have a link to them in the metadata file, but will not be
packaged in the zip file.

The `CodeRun` has been modelled as a RO Crate `ContextEntity` of type `CreateAction`,
see
[software-used-to-create-files](https://www.researchobject.org/ro-crate/1.1/provenance.html#software-used-to-create-files).

A `CreateAction` has `instrument` property, which represents the software used to
generate the product. For our purposes `instrument`s include the link to the repo, the
submission script and configuration file. The submission script metadata is based on
information from
[describing-scripts-and-workflows](https://www.researchobject.org/ro-crate/1.1/workflows.html#describing-scripts-and-workflows).

`CreateAction` (`CodeRun`) properties:

* `instrument`: the software used to generate the output
* `object`: the input files
* `result`: the output file
* `agent`: the `Author`
The RO Crate is available as a `zip` file.

The contents of the ro-crate-metadata file can be viewed as `JSON` or `JSON-LD`.

"""
import json

import mimetypes
from datetime import datetime
from rocrate.model.person import Person
from rocrate.rocrate import ContextEntity
from rocrate.rocrate import ROCrate

from data_management.views import external_object

from . import models


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
        author_id = f"{registry_url}api/author/{author.id}"
        cr_author = crate.add(
            Person(crate, author_id, properties={"name": author.name})
        )
        if author.identifier is not None:
            cr_author["identifier"] = author.identifier
        cr_authors.append({"@id": author_id})

    entity["author"] = cr_authors


def _add_data_products(crate_code_run, crate, object_components, registry_url, output):
    """
    Add input data products to the RO Crate code run entity.

    @param crate_code_run: RO Crate entity representing the code run
    @param crate: the RO Crate object
    @param object_components: a list of object_components from the ObjectComponent table
    @param registry_url: a str containing the registry URL
    @param output (bool): true if the data product is an output

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

    if output:
        crate_code_run["result"] = all_data_products
    else:
        crate_code_run["object"] = all_data_products


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
            "@type": "SoftwareApplication",
            "url": code_repo_id,
        }
    else:
        properties = {
            "@type": "SoftwareApplication",
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
            "@type": "CreateAction",
            "name": "code run",
            "endTime": code_run.run_date.isoformat(),
            "description": code_run.description,
        },
    )

    crate.add(crate_code_run)

    user_authors = models.UserAuthor.objects.filter(user=code_run.updated_by)

    if len(user_authors) == 0:
        agent_id = f"{registry_url}api/user/{code_run.updated_by.id}"
        run_agent = crate.add(
            Person(
                crate, agent_id, properties={"name": code_run.updated_by.full_name()}
            )
        )

    else:
        # we have an author linked to the user
        agent_id = f"{registry_url}api/author/{user_authors[0].author.id}"
        run_agent = crate.add(
            Person(crate, agent_id, properties={"name": user_authors[0].author.name})
        )
        if user_authors[0].author.identifier is not None:
            run_agent["identifier"] = user_authors[0].author.identifier

    crate_code_run["agent"] = {"@id": agent_id}

    # add the data product to the code run
    crate_code_run["result"] = crate_data_product

    return crate_code_run


def _get_data_product(crate, data_product, registry_url, output):
    """
    Create an RO Crate file entity representing the data product.

    @param crate_code_run: RO Crate entity representing the code run
    @param data_product: a data_product from the DataProduct table
    @param registry_url: a str containing the registry URL
    @param output (bool): true if the data product is an output

    @return an RO Crate file entity representing the data product

    """
    # Is it an external data product?
    crate_data_product = _get_external_object(crate, data_product)

    if crate_data_product is None:
        source_loc = str(data_product.object.storage_location).split("file:")[1]
        encoding_format = _get_mime_type(data_product.object.file_type.extension)

        if output:
            dest_path = f"outputs/{source_loc.split('/')[-1]}"
        else:
            dest_path = f"inputs/data/{source_loc.split('/')[-1]}"

        properties = {
            "name": data_product.name,
            "encodingFormat": encoding_format,
        }

        if data_product.object.description is not None:
            properties["description"] = data_product.object.description

        crate_data_product = crate.add_file(
            source_loc,
            dest_path=dest_path,
            properties=properties,
        )

    _add_authors(
        data_product.object.authors.all(),
        crate,
        crate_data_product,
        registry_url,
    )

    return crate_data_product


def _get_external_object(crate, data_product):
    """
    Create an RO Crate file entity for the given data product.

    @param crate: the RO Crate object
    @param data_product: a data_product from the DataProduct table

    @return an RO Crate file entity representing the external object, may be None

    """
    # check for external object linked to the data product
    try:
        external_object = data_product.external_object
    except (models.DataProduct.external_object.RelatedObjectDoesNotExist,):
        return None

    properties = {}
    properties["name"] = external_object.title
    properties["sdDatePublished"] = str(external_object.release_date)

    if external_object.identifier:
        source_loc = external_object.identifier
    else:
        source_loc = external_object.alternate_identifier

    if external_object.description:
        properties["description"] = external_object.description

    if external_object.original_store:
        properties["original_store"] = external_object.original_store

    crate_external_object = crate.add_file(source_loc, properties=properties)

    return crate_external_object


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


def _get_model_config(crate, model_config, registry_url):
    """
    Create a file entity for the model configuration.

    @param crate: the RO Crate object
    @param model_config: a model_config object
    @param registry_url: a str containing the registry URL

    @return an RO Crate file entity representing the model configuration

    """
    source_loc = str(model_config.storage_location)

    crate_model_config = crate.add_file(
        source_loc,
        dest_path=f"inputs/model_config/{source_loc.split('/')[-1]}",
        properties={
            "@type": ["File", "SoftwareSourceCode"],
            "name": source_loc.split("/")[-1],
        },
    )

    if model_config.description is not None:
        crate_model_config["description"] = model_config.description

    if (
        model_config.file_type is not None
        and model_config.file_type.extension is not None
    ):
        crate_model_config["encodingFormat"] = _get_mime_type(
            model_config.file_type.extension
        )

    _add_authors(
        model_config.authors.all(),
        crate,
        crate_model_config,
        registry_url,
    )

    return crate_model_config


def _get_submission_script(crate, submission_script, registry_url):
    """
    Create an RO Crate file entity for the submission script.

    @param crate: the RO Crate object
    @param submission_script: a submission_script object
    @param registry_url: a str containing the registry URL

    @return an RO Crate file entity representing the submission script

    """
    source_loc = str(submission_script.storage_location)

    crate_submission_script = crate.add_file(
        source_loc,
        dest_path=f"inputs/submission_script/{source_loc.split('/')[-1]}",
        properties={
            "@type": ["File", "SoftwareSourceCode"],
            "name": source_loc.split("/")[-1],
        },
    )

    if submission_script.description is not None:
        crate_submission_script["description"] = submission_script.description

    if (
        submission_script.file_type is not None
        and submission_script.file_type.extension is not None
    ):
        crate_submission_script["encodingFormat"] = _get_mime_type(
            submission_script.file_type.extension
        )

    _add_authors(
        submission_script.authors.all(),
        crate,
        crate_submission_script,
        registry_url,
    )

    return crate_submission_script


def _init_crate(data_product):
    crate = ROCrate()
    crate.publisher = "FAIR Data Pipeline"
    crate.datePublished = datetime.now().isoformat()
    crate.name = data_product.name
    crate.version = data_product.version

    return crate


def generate_ro_crate_from_cr(code_run, request):
    """
    Crate an RO Crate based around the code run.

    @param code_run: a code_run from the CodeRun table

    @return the RO Crate object

    """
    mimetypes.init()
    registry_url = request.build_absolute_uri("/")

    crate = ROCrate()
    crate.publisher = "FAIR Data Pipeline"
    crate.datePublished = datetime.now().isoformat()
    crate.name = code_run.uuid
    # crate.version = code_run.version
    instruments = []
    crate_data_product = None

    # add the code run
    crate_code_run = _get_code_run(crate_data_product, crate, code_run, registry_url)

    # add the code repo release
    if code_run.code_repo is not None:
        code_release = _get_code_repo_release(crate, code_run.code_repo, registry_url)
        instruments.append(code_release)

    # add the model config
    if code_run.model_config is not None:
        model_config = _get_model_config(crate, code_run.model_config, registry_url)
        instruments.append(model_config)

    # add the submission script
    submission_script = _get_submission_script(
        crate, code_run.submission_script, registry_url
    )
    instruments.append(submission_script)

    crate_code_run["instrument"] = instruments

    # add input files
    _add_data_products(
        crate_code_run, crate, code_run.inputs.all(), registry_url, False
    )

    # add output files
    _add_data_products(
        crate_code_run, crate, code_run.outputs.all(), registry_url, True
    )

    return crate


def generate_ro_crate_from_dp(data_product, request):
    """
    Crate an RO Crate based around the data product.

    @param data_product: a data_product from the DataProduct table

    @return the RO Crate object

    """
    mimetypes.init()
    registry_url = request.build_absolute_uri("/")

    crate = ROCrate()
    crate.publisher = "FAIR Data Pipeline"
    crate.datePublished = datetime.now().isoformat()
    crate.name = data_product.name
    crate.version = data_product.version

    # add the the main data product
    crate_data_product = _get_data_product(crate, data_product, registry_url, True)

    # add the activity, i.e. the code run
    components = data_product.object.components.all()

    for component in components:
        try:
            code_run = component.outputs_of.all()[0]
        except IndexError:
            # there is no code run for this component so we cannot add any more
            # provenance data
            continue

        instruments = []

        # add the code run
        crate_code_run = _get_code_run(
            crate_data_product, crate, code_run, registry_url
        )

        # add the code repo release
        if code_run.code_repo is not None:
            code_release = _get_code_repo_release(
                crate, code_run.code_repo, registry_url
            )
            instruments.append(code_release)

        # add the model config
        if code_run.model_config is not None:
            model_config = _get_model_config(crate, code_run.model_config, registry_url)
            instruments.append(model_config)

        # add the submission script
        submission_script = _get_submission_script(
            crate, code_run.submission_script, registry_url
        )
        instruments.append(submission_script)

        crate_code_run["instrument"] = instruments

        # add input files
        _add_data_products(
            crate_code_run, crate, code_run.inputs.all(), registry_url, False
        )

        return crate


def serialize_ro_crate(crate, format_):
    if format_ == "zip":
        file_name = crate.write_zip(f"/tmp/{crate.name}/{crate.version}.zip")
        zip_file = open(file_name, "rb")
        return zip_file
    if format_ == "json-ld":
        return json.dumps(crate.metadata.generate())
    return crate.metadata.generate()
