import io
import json

from prov.constants import PROV_ROLE, PROV_TYPE
import prov.dot
import prov.model
import prov.serializers

from data_management.views import external_object

from . import models


def _generate_object_meta(obj):
    data = []

    data.append(('last_updated', obj.last_updated))

    if obj.storage_location:
        data.append(('storage', str(obj.storage_location)))

    if obj.description:
        data.append(('description', obj.description))

    for data_product in obj.data_products.all():
        data.append(('namespace', str(data_product.namespace)))
        data.append(('name', str(data_product.name)))
        data.append(('version', str(data_product.version)))

    if obj.file_type is not None:
        data.append(('file_type', str(obj.file_type.name)))

    return data


def _add_author_agents(authors, doc, entity):
    """
    Add the authors to the entity as agents.

    @param authors: a list of authors from the Author table
    @param doc: a ProvDocument that the agent will belong to
    @param entity: the entity to attach the authors to

    """
    for author in authors:
        agent_id = f'api/author/{author.id}'
        agent = doc.get_record(agent_id)
        # check to see if we have already created an agent for this author
        if len(agent) > 0:
            # The prov documentation says a ProvRecord is returned, but actually a
            # list of ProvRecord is returned
            author_agent = agent[0]
        else:
            author_agent = doc.agent(
                agent_id,
                {
                    PROV_TYPE: 'prov:Person',
                    'name': author.name,
                    'identifier': author.identifier,
                },
            )
        doc.wasAttributedTo(entity, author_agent, None, {PROV_ROLE: 'author'})


def _add_code_repo_release(cr_activity, doc, code_repo):
    """
    Add code repo release to the code run activity.

    @param cr_activity: a prov.activity representing the code run
    @param doc: a ProvDocument that the entities will belong to
    @param code_repo: a code_repo object

    """
    try:
        code_repo_release = code_repo.code_repo_release
    except models.Object.code_repo_release.RelatedObjectDoesNotExist:
        code_repo_release = None

    if code_repo_release is None:
        code_release_entity = doc.entity(
            f'api/code_repo/{code_repo.id}',
            (
                *_generate_object_meta(code_repo),
            ),
        )
    else:
        code_release_entity = doc.entity(
            f'api/code_repo_release/{code_repo_release.id}',
            (
                *_generate_object_meta(code_repo),
                ('name', code_repo_release.name),
                ('version', code_repo_release.version),
                ('website', code_repo_release.website),
            ),
        )

    _add_author_agents(code_repo.authors.all(), doc, code_release_entity)
    doc.used(cr_activity, code_release_entity, None, None, {PROV_ROLE: 'software'})


def _add_external_object(doc, data_product, data_product_entity):
    """
    Add an external_object entity to the provenance document for the given data product.

    @param doc: a ProvDocument that the entity will belong to
    @param data_product: a data_product from the DataProduct table
    @param data_product_entity: a prov.entity representing the data_product

    """
    # check for external object linked to the data product
    try:
        external_object = data_product.external_object
    except (
        models.DataProduct.external_object.RelatedObjectDoesNotExist,
    ):
        return

    data = []
    data.append(('title', external_object.title))
    data.append(('release_date', external_object.release_date))
    data.append(('version', external_object.version))

    if external_object.identifier:
        data.append(('identifier', external_object.identifier))

    if external_object.alternate_identifier:
        data.append(('alternate_identifier', external_object.alternate_identifier))

    if external_object.alternate_identifier_type:
        data.append(
            ('alternate_identifier_type', external_object.alternate_identifier_type)
        )

    if external_object.description:
        data.append(('description', external_object.description))

    if external_object.original_store:
        data.append(('original_store', str(external_object.original_store)))

    external_object_entity = doc.entity(
        f'api/external_object/{external_object.id}', (*data,)
    )
    doc.specializationOf(external_object_entity, data_product_entity)


def _add_linked_files(
    cr_activity, doc, dp_entity, dp_id, input_objects, object_components
):
    """
    Add linked files to the code run activity.

    @param cr_activity: a prov.activity representing the code run
    @param doc: a ProvDocument that the entities will belong to
    @param dp_entity: a prov.entity representing the data_product
    @param dp_id: the data_product id
    @param input_objects: boolean, 'True' if the object_components represent input
                objects
    @param object_components: a list of object_components from the ObjectComponent table

    """
    for component in object_components:
        obj = component.object
        data_products = obj.data_products.all()

        for data_product in data_products:
            if not input_objects and data_product.id == dp_id:
                # we have already added the original data product
                continue

            file_id = f'api/data_product/{data_product.id}'
            file_entity = doc.entity(
                file_id,
                (
                    (PROV_TYPE, 'file'),
                    *_generate_object_meta(obj),
                ),
            )

            # add external object linked to the data product
            _add_external_object(doc, data_product, file_entity)

            _add_author_agents(obj.authors.all(), doc, file_entity)

            if input_objects:
                # add link to the code run
                doc.used(
                    cr_activity, file_entity, None, None, {PROV_ROLE: 'input data'})
                # add the link to the data product
                doc.wasDerivedFrom(dp_entity, file_entity)
            else:
                # add the link to the code run
                doc.wasGeneratedBy(file_entity, cr_activity)


def _add_model_config(cr_activity, doc, model_config):
    """
    Add model config to the code run activity.

    @param cr_activity: a prov.activity representing the code run
    @param doc: a ProvDocument that the entities will belong to
    @param model_config: a model_config object

    """
    model_config_entity = doc.entity(
        f'api/object/{model_config.id}', (*_generate_object_meta(model_config),)
    )

    _add_author_agents(model_config.authors.all(), doc, model_config_entity)
    doc.used(
        cr_activity, model_config_entity, None, None, {PROV_ROLE: 'model configuration'}
    )


def _add_submission_script(cr_activity, doc, submission_script):
    """
    Add submission script to the code run activity.

    @param cr_activity: a prov.activity representing the code run
    @param doc: a ProvDocument that the entities will belong to
    @param submission_script: a submission_script object

    """
    submission_script_entity = doc.entity(
        'api/object/' + str(submission_script.id),
        (*_generate_object_meta(submission_script),),
    )

    _add_author_agents(submission_script.authors.all(), doc, submission_script_entity)
    doc.used(
        cr_activity,
        submission_script_entity,
        None,
        None,
        {PROV_ROLE: 'submission script'},
    )


def get_whole_object_component(components):
    for component in components:
        if component.whole_object:
            return component


def generate_prov_document(data_product, request):
    """
    Generate a PROV document for a DataProduct detailing all the input and outputs and
    how they were generated.

    This uses the W3C PROV ontology (https://www.w3.org/TR/prov-o/).

    :param data_product: The DataProduct to generate the PROV document for

    :return: A PROV-O document

    """
    url = request.build_absolute_uri('/')

    doc = prov.model.ProvDocument()
    doc.set_default_namespace(url)

    # add the data product
    dp_entity = doc.entity(
        'api/data_product/' + str(data_product.id),
        (
            (PROV_TYPE, 'file'),
            *_generate_object_meta(data_product.object),
        ),
    )

    _add_author_agents(data_product.object.authors.all(), doc, dp_entity)
    _add_external_object(doc, data_product, dp_entity)

    # add the activity, i.e. the code run
    components = data_product.object.components.all()
    whole_object = get_whole_object_component(components)
    try:
        code_run = whole_object.outputs_of.all()[0]
    except IndexError:
        # there is no code run so we cannot add any more provenance data
        return doc

    cr_activity = doc.activity(
        'api/code_run/' + str(code_run.id),
        str(code_run.run_date),
        None,
        {
            PROV_TYPE: 'run',
            'description': code_run.description,
        },
    )

    doc.wasGeneratedBy(dp_entity, cr_activity)

    run_agent = doc.agent(
        f'api/user/{code_run.updated_by.id}',
        {
            PROV_TYPE: 'prov:Person',
            'name': code_run.updated_by.full_name(),
        },
    )
    doc.wasStartedBy(
        cr_activity,
        run_agent,
        None,
        str(code_run.run_date),
        None,
        {PROV_ROLE: 'code runner'},
    )

    # add the code repo release
    if code_run.code_repo is not None:
        _add_code_repo_release(cr_activity, doc, code_run.code_repo)

    # add the model config
    if code_run.model_config is not None:
        _add_model_config(cr_activity, doc, code_run.model_config)

    # add the submission script
    _add_submission_script(cr_activity, doc, code_run.submission_script)

    # add input files
    _add_linked_files(cr_activity, doc, dp_entity, None, True, code_run.inputs.all())

    # add additional output files
    _add_linked_files(
        cr_activity,
        doc,
        dp_entity,
        data_product.id,
        False,
        code_run.outputs.all(),
    )

    return doc


def serialize_prov_document(doc, format_, show_attributes=True):
    """
    Serialise a PROV document as either a JPEG or SVG image or an XML or PROV-N report.

    :param doc: A PROV-O document
    :param format_: The format to generate: jpg, svg, xml or provn
    :return: The PROV report in the specified format
    """
    if format_ in ('jpg', 'svg'):
        dot = prov.dot.prov_to_dot(doc, show_element_attributes=show_attributes)
        with io.BytesIO() as buf:
            if format_ == 'jpg':
                buf.write(dot.create_jpg())
            else:
                buf.write(dot.create_svg())
            buf.seek(0)
            return buf.read()
    elif format_ == 'xml':
        with io.StringIO() as buf:
            serializer = prov.serializers.get('xml')
            serializer(doc).serialize(buf)
            buf.seek(0)
            return buf.read()
    elif format_ == 'provn':
        with io.StringIO() as buf:
            serializer = prov.serializers.get('provn')
            serializer(doc).serialize(buf)
            buf.seek(0)
            return buf.read()
    else:
        with io.StringIO() as buf:
            serializer = prov.serializers.get('json')
            serializer(doc).serialize(buf)
            buf.seek(0)
            return json.loads(buf.read())
