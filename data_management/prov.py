import io
import json
import xml.etree.ElementTree

from django.conf import settings
from prov.constants import PROV, PROV_ROLE, PROV_TYPE
import prov.dot
from prov.identifier import QualifiedName
import prov.model
import prov.serializers
from rdflib import Graph

from data_management.views import external_object

from . import models


DCAT_VOCAB_PREFIX = 'dcat'
DCAT_VOCAB_NAMESPACE = 'http://www.w3.org/ns/dcat#'
DCMITYPE_VOCAB_PREFIX = 'dcmitype'
DCMITYPE_VOCAB_NAMESPACE = 'http://purl.org/dc/dcmitype/'
DCTERMS_VOCAB_PREFIX = 'dcterms'
DCTERMS_VOCAB_NAMESPACE = 'http://purl.org/dc/terms/'
FAIR_VOCAB_PREFIX = 'fair'
FOAF_VOCAB_PREFIX = 'foaf'
FOAF_VOCAB_NAMESPACE = 'http://xmlns.com/foaf/spec/#'


def _generate_object_meta(obj, vocab_namespaces):
    data = []

    data.append(
        (
            QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'modified'),
            obj.last_updated,
        )
    )

    if obj.storage_location:
        data.append(
            (
                QualifiedName(PROV, 'atLocation'),
                str(obj.storage_location),
            )
        )

    if obj.description:
        data.append(
            (
                QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'description'),
                obj.description,
            )
        )

    for data_product in obj.data_products.all():
        data.append(
            (
                QualifiedName(vocab_namespaces[FAIR_VOCAB_PREFIX], 'namespace'),
                str(data_product.namespace),
            )
        )
        data.append(
            (
                QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'title'),
                str(data_product.name),
            )
        )
        data.append(
            (
                QualifiedName(vocab_namespaces[DCAT_VOCAB_PREFIX], 'hasVersion'),
                str(data_product.version),
            )
        )

    for component in obj.components.all():
        for issue in component.issues.all():
            data.append(
                (
                    QualifiedName(vocab_namespaces[FAIR_VOCAB_PREFIX], 'issue'),
                    f"{issue.description} severity: {issue.severity} ID: {issue.id}"
                )
            )

    if obj.file_type is not None:
        data.append(
            (
                QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'format'),
                str(obj.file_type.name),
            )
        )

    return data


def _add_author_agents(authors, doc, entity, reg_uri_prefix, vocab_namespaces):
    """
    Add the authors to the entity as agents.

    @param authors: a list of authors from the Author table
    @param doc: a ProvDocument that the agent will belong to
    @param entity: the entity to attach the authors to
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    """
    for author in authors:
        agent_id = f'{reg_uri_prefix}:api/author/{author.id}'
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
                    PROV_TYPE: QualifiedName(PROV, 'Person'),
                    QualifiedName(
                        vocab_namespaces[FOAF_VOCAB_PREFIX], 'name'
                    ): author.name,
                    QualifiedName(
                        vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'identifier'
                    ): author.identifier,
                },
            )
        doc.wasAttributedTo(
            entity,
            author_agent,
            None,
            {
                PROV_ROLE: QualifiedName(
                    vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'creator'
                )
            },
        )


def _add_code_repo_release(
    cr_activity, doc, code_repo, reg_uri_prefix, vocab_namespaces
):
    """
    Add code repo release to the code run activity.

    @param cr_activity: a prov.activity representing the code run
    @param doc: a ProvDocument that the entities will belong to
    @param code_repo: a code_repo object
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    """
    try:
        code_repo_release = code_repo.code_repo_release
    except models.Object.code_repo_release.RelatedObjectDoesNotExist:
        code_repo_release = None

    if code_repo_release is None:
        code_release_entity = doc.entity(
            f'{reg_uri_prefix}:api/object/{code_repo.id}',
            (*_generate_object_meta(code_repo, vocab_namespaces),),
        )
    else:
        code_release_entity = doc.entity(
            f'{reg_uri_prefix}:api/code_repo_release/{code_repo_release.id}',
            (
                (
                    PROV_TYPE,
                    QualifiedName(vocab_namespaces[DCMITYPE_VOCAB_PREFIX], 'Software'),
                ),
                *_generate_object_meta(code_repo, vocab_namespaces),
                (
                    QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'title'),
                    code_repo_release.name,
                ),
                (
                    QualifiedName(vocab_namespaces[DCAT_VOCAB_PREFIX], 'hasVersion'),
                    code_repo_release.version,
                ),
                (
                    QualifiedName(vocab_namespaces[FAIR_VOCAB_PREFIX], 'website'),
                    code_repo_release.website,
                ),
            ),
        )

    _add_author_agents(
        code_repo.authors.all(),
        doc,
        code_release_entity,
        reg_uri_prefix,
        vocab_namespaces,
    )
    doc.used(
        cr_activity,
        code_release_entity,
        None,
        None,
        {PROV_ROLE: QualifiedName(vocab_namespaces[FAIR_VOCAB_PREFIX], 'software')},
    )


def _add_code_run(dp_entity, doc, code_run, reg_uri_prefix, vocab_namespaces):
    """
    Add code repo release to the code run activity.

    @param dp_entity: a prov.entity representing the data_product
    @param doc: a ProvDocument that the entities will belong to
    @param code_run: a code_run object
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    @return a prov.activity representing the code run

    """
    cr_activity = doc.activity(
        f'{reg_uri_prefix}:api/code_run/{code_run.id}',
        str(code_run.run_date),
        None,
        {
            PROV_TYPE: QualifiedName(vocab_namespaces[FAIR_VOCAB_PREFIX], 'Run'),
            QualifiedName(
                vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'description'
            ): code_run.description,
        },
    )

    doc.wasGeneratedBy(dp_entity, cr_activity)

    user_authors = models.UserAuthor.objects.filter(user=code_run.updated_by)
    if len(user_authors) == 0:
        run_agent = doc.agent(
            f'{reg_uri_prefix}:api/user/{code_run.updated_by.id}',
            {
                PROV_TYPE: QualifiedName(PROV, 'Person'),
                QualifiedName(
                    vocab_namespaces[FOAF_VOCAB_PREFIX], 'name'
                ): code_run.updated_by.full_name(),
            },
        )
    else:
        # we have an author linked to the user
        agent_id = f'{reg_uri_prefix}:api/author/{user_authors[0].author.id}'
        agent = doc.get_record(agent_id)
        # check to see if we have already created an agent for this author
        if len(agent) > 0:
            # The prov documentation says a ProvRecord is returned, but actually a
            # list of ProvRecord is returned
            run_agent = agent[0]
        else:
            run_agent = doc.agent(
                agent_id,
                {
                    PROV_TYPE: QualifiedName(PROV, 'Person'),
                    QualifiedName(
                        vocab_namespaces[FOAF_VOCAB_PREFIX], 'name'
                    ): user_authors[0].author.name,
                    QualifiedName(
                        vocab_namespaces[FAIR_VOCAB_PREFIX], 'identifier'
                    ): user_authors[0].author.identifier,
                },
            )

    doc.wasStartedBy(
        cr_activity,
        run_agent,
        None,
        str(code_run.run_date),
        None,
        {PROV_ROLE: QualifiedName(vocab_namespaces[FAIR_VOCAB_PREFIX], 'code_runner')},
    )

    return cr_activity


def _add_external_object(
    doc, data_product, data_product_entity, reg_uri_prefix, vocab_namespaces
):
    """
    Add an external_object entity to the provenance document for the given data product.

    @param doc: a ProvDocument that the entity will belong to
    @param data_product: a data_product from the DataProduct table
    @param data_product_entity: a prov.entity representing the data_product
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    """
    # check for external object linked to the data product
    try:
        external_object = data_product.external_object
    except (models.DataProduct.external_object.RelatedObjectDoesNotExist,):
        return

    data = []
    data.append(
        (PROV_TYPE, QualifiedName(vocab_namespaces[DCAT_VOCAB_PREFIX], 'Dataset'))
    )

    data.append(
        (
            QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'title'),
            external_object.title,
        )
    )
    data.append(
        (
            QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'issued'),
            external_object.release_date,
        )
    )
    data.append(
        (
            QualifiedName(vocab_namespaces[DCAT_VOCAB_PREFIX], 'hasVersion'),
            external_object.version,
        )
    )

    if external_object.identifier:
        data.append(
            (
                QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'identifier'),
                external_object.identifier,
            )
        )

    if external_object.alternate_identifier:
        data.append(
            (
                QualifiedName(
                    vocab_namespaces[FAIR_VOCAB_PREFIX], 'alternate_identifier'
                ),
                external_object.alternate_identifier,
            )
        )

    if external_object.alternate_identifier_type:
        data.append(
            (
                QualifiedName(
                    vocab_namespaces[FAIR_VOCAB_PREFIX], 'alternate_identifier_type'
                ),
                external_object.alternate_identifier_type,
            )
        )

    if external_object.description:
        data.append(
            (
                QualifiedName(vocab_namespaces[DCTERMS_VOCAB_PREFIX], 'description'),
                external_object.description,
            )
        )

    if external_object.original_store:
        data.append(
            (
                QualifiedName(PROV, 'atLocation'),
                str(external_object.original_store),
            )
        )

    external_object_entity = doc.entity(
        f'{reg_uri_prefix}:api/external_object/{external_object.id}', (*data,)
    )
    doc.specializationOf(external_object_entity, data_product_entity)


def _add_input_data_products(
    cr_activity,
    doc,
    dp_entity,
    object_components,
    reg_uri_prefix,
    vocab_namespaces,
):
    """
    Add input data products to the code run activity.

    @param cr_activity: a prov.activity representing the code run
    @param doc: a ProvDocument that the entities will belong to
    @param dp_entity: a prov.entity representing the data_product
    @param object_components: a list of object_components from the ObjectComponent table
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    @return a list of data products that were added

    """
    all_data_products = []
    for component in object_components:
        obj = component.object
        data_products = obj.data_products.all()

        for data_product in data_products:
            file_id = f'{reg_uri_prefix}:api/data_product/{data_product.id}'

            entity = doc.get_record(file_id)
            # check to see if we have already created an entity for this data product
            if len(entity) > 0:
                # The prov documentation says a ProvRecord is returned, but actually a
                # list of ProvRecord is returned
                file_entity = entity[0]
            else:
                file_entity = doc.entity(
                    file_id,
                    (
                        (
                            PROV_TYPE,
                            QualifiedName(vocab_namespaces[DCAT_VOCAB_PREFIX], 'Dataset'),
                        ),
                        *_generate_object_meta(obj, vocab_namespaces),
                    ),
                )

                # add external object linked to the data product
                _add_external_object(
                    doc, data_product, file_entity, reg_uri_prefix, vocab_namespaces
                )

                _add_author_agents(
                    obj.authors.all(), doc, file_entity, reg_uri_prefix, vocab_namespaces
                )

            # add link to the code run
            doc.used(
                cr_activity,
                file_entity,
                None,
                None,
                {
                    PROV_ROLE: QualifiedName(
                        vocab_namespaces[FAIR_VOCAB_PREFIX], 'input_data'
                    )
                },
            )
            # add the link to the data product
            doc.wasDerivedFrom(dp_entity, file_entity)

        all_data_products.extend(data_products)

    return all_data_products


def _add_model_config(cr_activity, doc, model_config, reg_uri_prefix, vocab_namespaces):
    """
    Add model config to the code run activity.

    @param cr_activity: a prov.activity representing the code run
    @param doc: a ProvDocument that the entities will belong to
    @param model_config: a model_config object
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    """
    model_config_entity = doc.entity(
        f'{reg_uri_prefix}:api/object/{model_config.id}',
        (*_generate_object_meta(model_config, vocab_namespaces),),
    )

    _add_author_agents(
        model_config.authors.all(),
        doc,
        model_config_entity,
        reg_uri_prefix,
        vocab_namespaces,
    )
    doc.used(
        cr_activity,
        model_config_entity,
        None,
        None,
        {
            PROV_ROLE: QualifiedName(
                vocab_namespaces[FAIR_VOCAB_PREFIX], 'model_configuration'
            )
        },
    )


def _add_prime_data_product(doc, data_product, reg_uri_prefix, vocab_namespaces):
    """
    Add the prime data product for this level of the provenance report.

    @param doc: a ProvDocument that the entities will belong to
    @param data_product: The DataProduct to generate the PROV document for
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    @return the data product entity

    """
    data_product_id = f'{reg_uri_prefix}:api/data_product/{data_product.id}'
    entity = doc.get_record(data_product_id)
    # check to see if we have already created an entity for this data product
    if len(entity) > 0:
        # The prov documentation says a ProvRecord is returned, but actually a
        # list of ProvRecord is returned
        return entity[0]

    # add the data product
    dp_entity = doc.entity(
        f'{reg_uri_prefix}:api/data_product/{data_product.id}',
        (
            (PROV_TYPE, QualifiedName(vocab_namespaces[DCAT_VOCAB_PREFIX], 'Dataset')),
            *_generate_object_meta(data_product.object, vocab_namespaces),
        ),
    )

    _add_author_agents(
        data_product.object.authors.all(),
        doc,
        dp_entity,
        reg_uri_prefix,
        vocab_namespaces,
    )

    _add_external_object(doc, data_product, dp_entity, reg_uri_prefix, vocab_namespaces)

    return dp_entity


def _add_submission_script(
    cr_activity, doc, submission_script, reg_uri_prefix, vocab_namespaces
):
    """
    Add submission script to the code run activity.

    @param cr_activity: a prov.activity representing the code run
    @param doc: a ProvDocument that the entities will belong to
    @param submission_script: a submission_script object
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    """
    submission_script_entity = doc.entity(
        f'{reg_uri_prefix}:api/object/{submission_script.id}',
        (
            (
                PROV_TYPE,
                QualifiedName(vocab_namespaces[DCMITYPE_VOCAB_PREFIX], 'Software'),
            ),
            *_generate_object_meta(submission_script, vocab_namespaces),
        ),
    )

    _add_author_agents(
        submission_script.authors.all(),
        doc,
        submission_script_entity,
        reg_uri_prefix,
        vocab_namespaces,
    )
    doc.used(
        cr_activity,
        submission_script_entity,
        None,
        None,
        {
            PROV_ROLE: QualifiedName(
                vocab_namespaces[FAIR_VOCAB_PREFIX], 'submission_script'
            )
        },
    )


def _generate_prov_document(doc, data_product, reg_uri_prefix, vocab_namespaces):
    """
    Add the next level to the provenance doc.

    This takes a data product and finds generates it provenance. A list of input files
    are returned so they can be used to create the next level of the provenane if
    needed.

    @param doc: a ProvDocument that the entities will belong to
    @param data_product: The DataProduct to generate the PROV document for
    @param reg_uri_prefix: a str containing the name of the prefix
    @param vocab_namespaces: a dict containing the Namespaces for the vocab

    @return a list of files that were used as input files, may be empty

    """
    # add the the root data product
    dp_entity = _add_prime_data_product(
        doc, data_product, reg_uri_prefix, vocab_namespaces
    )

    # add the activity, i.e. the code run
    components = data_product.object.components.all()
    all_input_files = []

    for component in components:
        try:
            code_run = component.outputs_of.all()[0]
        except IndexError:
            # there is no code run for this component so we cannot add any more provenance data
            continue

        # add the code run, this is the central activity
        cr_activity = _add_code_run(
            dp_entity, doc, code_run, reg_uri_prefix, vocab_namespaces
        )

        # add the code repo release
        if code_run.code_repo is not None:
            _add_code_repo_release(
                cr_activity, doc, code_run.code_repo, reg_uri_prefix, vocab_namespaces
            )

        # add the model config
        if code_run.model_config is not None:
            _add_model_config(
                cr_activity, doc, code_run.model_config, reg_uri_prefix, vocab_namespaces
            )

        # add the submission script
        _add_submission_script(
            cr_activity, doc, code_run.submission_script, reg_uri_prefix, vocab_namespaces
        )

        # add input files
        input_files = _add_input_data_products(
            cr_activity,
            doc,
            dp_entity,
            code_run.inputs.all(),
            reg_uri_prefix,
            vocab_namespaces,
        )

        all_input_files.extend(input_files)

    return all_input_files


def generate_prov_document(data_product, depth, request):
    """
    Generate a PROV document for a DataProduct detailing all the input and outputs and
    how they were generated.

    This uses the W3C PROV ontology (https://www.w3.org/TR/prov-o/).

    :param data_product: The DataProduct to generate the PROV document for
    :param depth: The depth for the document. How many levels of code runs to include.
    :param request: A request object

    :return: A PROV-O document

    """
    url = request.build_absolute_uri('/')
    central_registry_url = settings.CENTRAL_REGISTRY_URL
    if not central_registry_url.endswith('/'):
        central_registry_url = f'{central_registry_url}/'

    doc = prov.model.ProvDocument()

    if url == central_registry_url:
        # we are using the main registry
        reg_uri_prefix = 'reg'
        doc.add_namespace(reg_uri_prefix, central_registry_url)
    else:
        # we are using a local registry
        reg_uri_prefix = 'lreg'
        doc.add_namespace(reg_uri_prefix, url)

    # the vocab namespace is always the main registry
    doc.add_namespace(FAIR_VOCAB_PREFIX, f'{central_registry_url}vocab/#')
    # we need to tell SONAR to ignore 'http' in the vocab URLs
    doc.add_namespace(DCAT_VOCAB_PREFIX, DCAT_VOCAB_NAMESPACE)  # NOSONAR
    doc.add_namespace(DCMITYPE_VOCAB_PREFIX, DCMITYPE_VOCAB_NAMESPACE)  # NOSONAR
    doc.add_namespace(DCTERMS_VOCAB_PREFIX, DCTERMS_VOCAB_NAMESPACE)  # NOSONAR
    doc.add_namespace(FOAF_VOCAB_PREFIX, FOAF_VOCAB_NAMESPACE)  # NOSONAR

    vocab_namespaces = {}
    for namespace in doc.get_registered_namespaces():
        vocab_namespaces[namespace.prefix] = namespace

    # get the initial set of input files
    input_files = _generate_prov_document(
        doc, data_product, reg_uri_prefix, vocab_namespaces
    )

    if depth == 1:
        return doc

    # add extra layers to the report if requested by the user
    while depth > 1:
        next_level_input_files = []

        for input_file in input_files:
            next_input_files = _generate_prov_document(
                doc, input_file, reg_uri_prefix, vocab_namespaces
            )
            next_level_input_files.extend(next_input_files)

        # reset the input files for the next level
        input_files = next_level_input_files
        depth = depth - 1

    return doc


def highlight_issues(dot):
    nodes = dot.get_node_list()
    for node in nodes:
        if "fair:issue" in node.obj_dict["attributes"]["label"]:
            label = node.get_label()
            table = xml.etree.ElementTree.fromstring(label[1:-1:])
            for row in table:
                for cell in row:
                    if "href" in cell.attrib and cell.attrib["href"] == "https://data.scrc.uk/vocab/#issue":
                        cell.attrib["bgcolor"] = "red"
            new_label = xml.etree.ElementTree.tostring(table, encoding="unicode")
            node.set_label('<' + new_label + '>')


def serialize_prov_document(doc, format_, aspect_ratio, dpi=None, show_attributes=True):
    """
    Serialise a PROV document as either a JPEG or SVG image or an XML or JSON-LD or PROV-N report.

    :param doc: A PROV-O document
    :param format_: The format to generate: jpg, svg, xml, json-ld or provn
    :param aspect_ratio: a float used to define the ratio for images
    :param dpi:  a float used to define the dpi for images
    :param show_attributes: a boolean, shows attributes of elements when True

    :return: The PROV report in the specified format

    """
    if format_ in ('jpg', 'svg'):
        dot = prov.dot.prov_to_dot(doc, show_element_attributes=show_attributes)
        highlight_issues(dot)
        dot.set_ratio(aspect_ratio)
        dot.set_dpi(dpi)
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

    elif format_ == 'json-ld':
        with io.StringIO() as buf:
            serializer = prov.serializers.get('rdf')
            serializer(doc).serialize(buf)
            buf.seek(0)
            graph = Graph()
            graph.parse(data=buf.read(), format='trig')
        # we should be able to use `context = dict(graph.namespaces())` but this
        # appears not to work in RDFlib 5.0.0
        context = {}
        for prefix, uri in graph.namespaces():
            context[prefix] = str(uri)
        return graph.serialize(format='json-ld', indent=4, context=context)

    else:
        with io.StringIO() as buf:
            serializer = prov.serializers.get('json')
            serializer(doc).serialize(buf)
            buf.seek(0)
            return json.loads(buf.read())
