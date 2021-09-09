from dateutil import parser

from data_management.models import (
    Author,
    CodeRepoRelease,
    CodeRun,
    DataProduct,
    ExternalObject,
    FileType,
    Object,
    StorageLocation,
    StorageRoot,
    Namespace,
)
from django.contrib.auth import get_user_model


def init_db():
    user = get_user_model().objects.get_or_create(username="exampleusera")[0]
    get_user_model().objects.get_or_create(username="exampleuserb")
    get_user_model().objects.get_or_create(username="exampleuserc")

    sr_github = StorageRoot.objects.get_or_create(
        updated_by=user, root="https://github.com"
    )[0]

    sr_textfiles = StorageRoot.objects.get_or_create(
        updated_by=user, root="https://data.scrc.uk/api/text_file/"
    )[0]

    sr_example = StorageRoot.objects.get_or_create(
        updated_by=user, root="https://example.org/"
    )[0]

    sl_file_1 = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="file_strore/1.txt",
        hash="346df017da291fe0e9d1169846efb12f3377aef1",
        storage_root=sr_example,
    )[0]

    sl_file_2 = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="file_strore/2.txt",
        hash="346df017da291fe0e9d1169846efb12f3377aef2",
        storage_root=sr_example,
    )[0]

    sl_code = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="ScottishCovidResponse/SCRCdata repository",
        hash="b98782baaaea3bf6cc2882ad7d1c5de7aece362a",
        storage_root=sr_github,
    )[0]

    sl_model_config = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="15/?format=text",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90e8",
        storage_root=sr_textfiles,
    )[0]

    sl_script = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="16/?format=text",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90e9",
        storage_root=sr_textfiles,
    )[0]

    sl_input_1 = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="input/1",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a1",
        storage_root=sr_textfiles,
    )[0]

    sl_input_2 = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="input/2",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a2",
        storage_root=sr_textfiles,
    )[0]

    sl_input_3 = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="input/3",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a3",
        storage_root=sr_textfiles,
    )[0]

    sl_input_4 = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="input/4",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a4",
        storage_root=sr_textfiles,
    )[0]

    sl_output_1 = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="output/1",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90b1",
        storage_root=sr_textfiles,
    )[0]

    sl_output_2 = StorageLocation.objects.get_or_create(
        updated_by=user,
        path="output/2",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90b2",
        storage_root=sr_textfiles,
    )[0]

    text_file = FileType.objects.get_or_create(
        updated_by=user, extension="txt", name="text file"
    )[0]

    a1 = Author.objects.get_or_create(updated_by=user, name="Ivana Valenti")[0]
    a2 = Author.objects.get_or_create(updated_by=user, name="Maria Cipriani")[0]
    a3 = Author.objects.get_or_create(updated_by=user, name="Rosanna Massabeti")[0]

    o_code = Object.objects.get_or_create(updated_by=user, storage_location=sl_code)[0]
    o_code_2 = Object.objects.get_or_create(updated_by=user, storage_location=sl_code)[
        0
    ]
    o_model_config = Object.objects.get_or_create(
        updated_by=user, storage_location=sl_model_config
    )[0]
    o_script = Object.objects.get_or_create(
        updated_by=user, storage_location=sl_script, file_type=text_file
    )[0]

    o_input_1 = Object.objects.get_or_create(
        updated_by=user, storage_location=sl_input_1, description="input 1 object"
    )[0]
    o_input_1.authors.add(a1)
    o_input_2 = Object.objects.get_or_create(
        updated_by=user, storage_location=sl_input_2, description="input 2 object"
    )[0]
    o_input_2.authors.add(a2)
    o_input_3 = Object.objects.get_or_create(
        updated_by=user, storage_location=sl_input_3, description="input 3 object"
    )[0]
    o_input_3.authors.add(a3)
    o_input_4 = Object.objects.get_or_create(
        updated_by=user, storage_location=sl_input_4, description="input 4 object"
    )[0]
    o_output_1 = Object.objects.get_or_create(
        updated_by=user, storage_location=sl_output_1, description="output 1 object"
    )[0]
    o_output_1.authors.add(a3)
    o_output_2 = Object.objects.get_or_create(
        updated_by=user, storage_location=sl_output_2, description="output 2 object"
    )[0]
    o_output_2.authors.add(a3)
    o_output_3 = Object.objects.get_or_create(
        updated_by=user, description="output 2 object"
    )[0]
    o_output_4 = Object.objects.get_or_create(
        updated_by=user, description="output 2 object"
    )[0]

    n_prov = Namespace.objects.get_or_create(updated_by=user, name="prov")[0]

    dp_cr_input_1 = DataProduct.objects.get_or_create(
        updated_by=user,
        object=o_input_1,
        namespace=n_prov,
        name="this/is/cr/example/input/1",
        version="0.2.0",
    )[0]

    ExternalObject.objects.get_or_create(
        updated_by=user,
        data_product=dp_cr_input_1,
        alternate_identifier="this_is_cr_example_input_1",
        alternate_identifier_type="text",
        release_date=parser.isoparse("2020-07-10T18:38:00Z"),
        title="this is cr example input 1",
        description="this is code run example input 1",
        original_store=sl_file_1,
    )

    dp_cr_output_1 = DataProduct.objects.get_or_create(
        updated_by=user,
        object=o_output_1,
        namespace=n_prov,
        name="this/is/cr/example/output/1",
        version="0.2.0",
    )[0]

    ExternalObject.objects.get_or_create(
        updated_by=user,
        data_product=dp_cr_output_1,
        identifier="this_is_cr_example_output_1_id",
        alternate_identifier="this_is_cr_example_output_1",
        alternate_identifier_type="text",
        release_date=parser.isoparse("2021-07-10T18:38:00Z"),
        title="this is cr example output 1",
        description="this is code run example output 1",
        original_store=sl_file_2,
    )

    dp_cr_output_2 = DataProduct.objects.get_or_create(
        updated_by=user,
        object=o_output_2,
        namespace=n_prov,
        name="this/is/cr/example/output/2",
        version="0.2.0",
    )[0]

    ExternalObject.objects.get_or_create(
        updated_by=user,
        data_product=dp_cr_output_2,
        identifier="this_is_cr_example_output_2",
        release_date=parser.isoparse("2021-07-10T18:38:00Z"),
        title="this is cr example output 2",
    )

    DataProduct.objects.get_or_create(
        updated_by=user,
        object=o_input_2,
        namespace=n_prov,
        name="this/is/cr/example/input/2",
        version="0.2.0",
    )

    DataProduct.objects.get_or_create(
        updated_by=user,
        object=o_input_3,
        namespace=n_prov,
        name="this/is/cr/example/input/3",
        version="0.2.0",
    )

    DataProduct.objects.get_or_create(
        updated_by=user,
        object=o_output_3,
        namespace=n_prov,
        name="this/is/cr/example/output/3",
        version="0.3.0",
    )

    DataProduct.objects.get_or_create(
        updated_by=user,
        object=o_output_4,
        namespace=n_prov,
        name="this/is/cr/example/output/4",
        version="0.4.0",
    )

    CodeRepoRelease.objects.get_or_create(
        updated_by=user,
        name="ScottishCovidResponse/SCRCdata",
        version="0.1.0",
        website="https://github.com/ScottishCovidResponse/SCRCdata",
        object=o_code,
    )

    cr1 = CodeRun.objects.get_or_create(
        updated_by=user,
        run_date="2021-07-17T18:21:11Z",
        description="Test run",
        code_repo=o_code,
        model_config=o_model_config,
        submission_script=o_script,
    )[0]
    cr1.inputs.set(
        [
            o_input_1.components.first(),
            o_input_2.components.first(),
            o_input_3.components.first(),
            o_input_4.components.first(),
        ]
    )
    cr1.outputs.set([o_output_1.components.first(), o_output_2.components.first()])

    cr2 = CodeRun.objects.get_or_create(
        updated_by=user,
        run_date="2021-07-17T19:21:11Z",
        code_repo=o_code_2,
        submission_script=o_script,
    )[0]
    cr2.inputs.set([o_input_1.components.first()])
    cr2.outputs.set([o_output_3.components.first()])

    cr3 = CodeRun.objects.get_or_create(
        updated_by=user, run_date="2021-07-17T19:21:11Z", submission_script=o_script
    )[0]
    cr3.inputs.set([o_input_1.components.first()])
    cr3.outputs.set([o_output_4.components.first()])
