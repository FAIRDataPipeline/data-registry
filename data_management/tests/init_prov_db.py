from dateutil import parser

from data_management.models import (
    Author,
    CodeRepoRelease,
    CodeRun,
    DataProduct,
    ExternalObject,
    FileType,
    Licence,
    Object,
    StorageLocation,
    StorageRoot,
    Issue,
    Namespace,
    UserAuthor,
)
from django.contrib.auth import get_user_model


def reset_db():
    Object.objects.all().delete()
    StorageRoot.objects.all().delete()
    Issue.objects.all().delete()
    Namespace.objects.all().delete()


def init_db():
    user = get_user_model().objects.first()
    usera = get_user_model().objects.create(username="testusera")
    userb = get_user_model().objects.create(username="testuserb")
    get_user_model().objects.create(username="testuserc")

    sr_github = StorageRoot.objects.create(
        updated_by=user,
        root="https://github.com",
    )

    sr_textfiles = StorageRoot.objects.create(
        updated_by=user,
        root="https://data.fairdatapipeline.org/api/text_file/",
    )

    sr_example = StorageRoot.objects.create(
        updated_by=user,
        root="https://example.org/",
    )

    sr_file = StorageRoot.objects.create(
        updated_by=user,
        root="file:/",
    )

    sl_file_1 = StorageLocation.objects.create(
        updated_by=user,
        path="file_strore/1.txt",
        hash="346df017da291fe0e9d1169846efb12f3377aef1",
        storage_root=sr_example,
    )

    sl_file_2 = StorageLocation.objects.create(
        updated_by=user,
        path="file_strore/2.txt",
        hash="346df017da291fe0e9d1169846efb12f3377aef2",
        storage_root=sr_example,
    )

    sl_file_3 = StorageLocation.objects.create(
        updated_by=user,
        path="file_strore/3.txt",
        hash="346df017da291fe0e9d1169846efb12f3377aef3",
        storage_root=sr_file,
    )

    sl_code = StorageLocation.objects.create(
        updated_by=user,
        path="ScottishCovidResponse/SCRCdata repository",
        hash="b98782baaaea3bf6cc2882ad7d1c5de7aece362a",
        storage_root=sr_github,
    )

    sl_model_config = StorageLocation.objects.create(
        updated_by=user,
        path="15/?format=text",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90e8",
        storage_root=sr_textfiles,
    )

    sl_model_config_2 = StorageLocation.objects.create(
        updated_by=user,
        path="model_config",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90z8",
        public=False,
        storage_root=sr_file,
    )

    sl_script = StorageLocation.objects.create(
        updated_by=user,
        path="16/?format=text",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90e9",
        storage_root=sr_textfiles,
    )

    sl_script_2 = StorageLocation.objects.create(
        updated_by=user,
        path="submission_script",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90z9",
        storage_root=sr_file,
    )

    sl_input_1 = StorageLocation.objects.create(
        updated_by=user,
        path="input/1",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a1",
        storage_root=sr_textfiles,
    )

    sl_input_2 = StorageLocation.objects.create(
        updated_by=user,
        path="input/2",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a2",
        storage_root=sr_textfiles,
    )

    sl_input_3 = StorageLocation.objects.create(
        updated_by=user,
        path="input/3",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a3",
        storage_root=sr_textfiles,
    )

    sl_input_4 = StorageLocation.objects.create(
        updated_by=user,
        path="input/4",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a4",
        storage_root=sr_textfiles,
    )

    sl_input_5 = StorageLocation.objects.create(
        updated_by=user,
        path="input/5",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a5",
        public=False,
        storage_root=sr_file,
    )

    sl_input_6 = StorageLocation.objects.create(
        updated_by=user,
        path="input/6",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90a6",
        storage_root=sr_file,
    )

    sl_output_1 = StorageLocation.objects.create(
        updated_by=user,
        path="output/1",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90b1",
        storage_root=sr_textfiles,
    )

    sl_output_2 = StorageLocation.objects.create(
        updated_by=user,
        path="output/2",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90b2",
        storage_root=sr_textfiles,
    )

    sl_output_3 = StorageLocation.objects.create(
        updated_by=user,
        path="output/3",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90b3",
        public=False,
        storage_root=sr_file,
    )

    sl_output_4 = StorageLocation.objects.create(
        updated_by=user,
        path="output/4",
        hash="5b6fafc594cdb619104ceeef7a4802f4086e90b4",
        storage_root=sr_file,
    )

    text_file = FileType.objects.create(
        updated_by=user,
        extension="txt",
        name="text file",
    )

    duff_file = FileType.objects.create(
        updated_by=user,
        extension="duff",
        name="duff file",
    )

    a1 = Author.objects.create(updated_by=user, name="Ivana Valenti")
    a2 = Author.objects.create(updated_by=user, name="Maria Cipriani")
    a3 = Author.objects.create(updated_by=user, name="Rosanna Massabeti")
    a4 = Author.objects.create(
        updated_by=user, name="James Brown", identifier="https://example.org/testuserid"
    )
    UserAuthor.objects.get_or_create(updated_by=user, user=usera, author=a1)
    UserAuthor.objects.get_or_create(updated_by=user, user=userb, author=a4)

    o_code = Object.objects.create(updated_by=user, storage_location=sl_code)
    o_code_2 = Object.objects.create(updated_by=user, storage_location=sl_code)
    o_model_config = Object.objects.create(
        updated_by=user, storage_location=sl_model_config
    )
    o_script = Object.objects.create(
        updated_by=user, storage_location=sl_script, file_type=text_file
    )

    o_input_1 = Object.objects.create(
        updated_by=user, storage_location=sl_input_1, description="input 1 object"
    )
    o_input_1.authors.add(a1)
    o_input_2 = Object.objects.create(
        updated_by=user,
        storage_location=sl_input_2,
        description="input 2 object",
        file_type=text_file,
    )
    o_input_2.authors.add(a2)
    o_input_3 = Object.objects.create(
        updated_by=user,
        storage_location=sl_input_3,
        description="input 3 object",
        file_type=text_file,
    )
    o_input_3.authors.add(a3)
    o_input_4 = Object.objects.create(
        updated_by=user,
        storage_location=sl_input_4,
        description="input 4 object",
        file_type=text_file,
    )
    o_input_5 = Object.objects.create(
        updated_by=user,
        storage_location=sl_input_5,
        description="input 5 object",
        file_type=text_file,
    )
    o_input_5.authors.add(a4)
    o_input_6 = Object.objects.create(
        updated_by=user,
        storage_location=sl_input_6,
        description="input 6 object",
        file_type=duff_file,
    )
    o_input_6.authors.add(a4)

    o_output_1 = Object.objects.create(
        updated_by=user, storage_location=sl_output_1, description="output 1 object"
    )
    o_output_1.authors.add(a3)
    o_output_2 = Object.objects.create(
        updated_by=user, storage_location=sl_output_2, description="output 2 object"
    )
    o_output_2.authors.add(a3)
    o_output_3 = Object.objects.create(updated_by=user)
    o_output_4 = Object.objects.create(updated_by=user)
    o_output_5 = Object.objects.create(updated_by=user)
    o_output_6 = Object.objects.create(updated_by=user)
    o_output_7 = Object.objects.create(
        updated_by=user,
        storage_location=sl_output_3,
        description="output 7 object",
        file_type=text_file,
    )
    o_output_7.authors.add(a3)
    o_output_8 = Object.objects.create(
        updated_by=user,
        storage_location=sl_output_4,
        description="output 8 object",
        file_type=text_file,
    )
    o_output_8.authors.add(a3)

    o_model_config_2 = Object.objects.create(
        updated_by=user, storage_location=sl_model_config_2
    )

    o_script_2 = Object.objects.create(
        updated_by=user, storage_location=sl_script_2, description="submission script"
    )

    n_prov = Namespace.objects.create(updated_by=user, name="prov")

    dp_cr_input_1 = DataProduct.objects.create(
        updated_by=user,
        object=o_input_1,
        namespace=n_prov,
        name="this/is/cr/test/input/1",
        version="0.2.0",
    )

    Licence.objects.create(
        updated_by=user,
        object=o_input_1,
        licence_info="licence info",
        identifier="https://example.org/licence",
    )

    ExternalObject.objects.create(
        updated_by=user,
        data_product=dp_cr_input_1,
        alternate_identifier="this_is_cr_test_input_1",
        alternate_identifier_type="text",
        release_date=parser.isoparse("2020-07-10T18:38:00Z"),
        title="this is cr test input 1",
        description="this is code run test input 1",
        original_store=sl_file_1,
    )

    dp_cr_output_1 = DataProduct.objects.create(
        updated_by=user,
        object=o_output_1,
        namespace=n_prov,
        name="this/is/cr/test/output/1",
        version="0.2.0",
    )

    Licence.objects.create(
        updated_by=user,
        object=o_output_1,
        licence_info="licence info 1",
    )

    Licence.objects.create(
        updated_by=user,
        object=o_output_1,
        licence_info="licence info 2",
    )

    ExternalObject.objects.create(
        updated_by=user,
        data_product=dp_cr_output_1,
        identifier="this_is_cr_test_output_1_id",
        alternate_identifier="this_is_cr_test_output_1",
        alternate_identifier_type="text",
        release_date=parser.isoparse("2021-07-10T18:38:00Z"),
        title="this is cr test output 1",
        description="this is code run test output 1",
        original_store=sl_file_2,
    )

    dp_cr_output_2 = DataProduct.objects.create(
        updated_by=user,
        object=o_output_2,
        namespace=n_prov,
        name="this/is/cr/test/output/2",
        version="0.2.0",
    )

    ExternalObject.objects.create(
        updated_by=user,
        data_product=dp_cr_output_2,
        identifier="this_is_cr_test_output_2",
        release_date=parser.isoparse("2021-07-10T18:38:00Z"),
        title="this is cr test output 2",
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_input_2,
        namespace=n_prov,
        name="this/is/cr/test/input/2",
        version="0.2.0",
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_input_3,
        namespace=n_prov,
        name="this/is/cr/test/input/3",
        version="0.2.0",
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_output_3,
        namespace=n_prov,
        name="this/is/cr/test/output/3",
        version="0.3.0",
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_output_4,
        namespace=n_prov,
        name="this/is/cr/test/output/4",
        version="0.4.0",
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_output_5,
        namespace=n_prov,
        name="this/is/cr/test/output/5",
        version="0.5.0",
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_output_6,
        namespace=n_prov,
        name="this/is/cr/test/output/6",
        version="0.6.0",
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_output_7,
        namespace=n_prov,
        name="this/is/cr/test/output/7",
        version="0.7.0",
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_output_8,
        namespace=n_prov,
        name="this/is/cr/test/output/8",
        version="0.8.0",
    )

    CodeRepoRelease.objects.create(
        updated_by=user,
        name="ScottishCovidResponse/SCRCdata",
        version="0.1.0",
        website="https://github.com/ScottishCovidResponse/SCRCdata",
        object=o_code,
    )

    cr1 = CodeRun.objects.create(
        updated_by=user,
        run_date="2021-07-17T18:21:11Z",
        description="Test run",
        code_repo=o_code,
        model_config=o_model_config,
        submission_script=o_script,
    )
    cr1.inputs.set(
        [
            o_input_1.components.first(),
            o_input_2.components.first(),
            o_input_3.components.first(),
            o_input_4.components.first(),
        ]
    )
    cr1.outputs.set([o_output_1.components.first(), o_output_2.components.first()])

    cr2 = CodeRun.objects.create(
        updated_by=user,
        run_date="2021-07-17T19:21:11Z",
        code_repo=o_code_2,
        submission_script=o_script,
    )
    cr2.inputs.set([o_input_1.components.first()])
    cr2.outputs.set([o_output_3.components.first()])

    cr3 = CodeRun.objects.create(
        updated_by=usera,
        run_date="2021-07-17T19:21:11Z",
        submission_script=o_script,
    )
    cr3.inputs.set([o_input_1.components.first()])
    cr3.outputs.set([o_output_4.components.first()])

    cr4 = CodeRun.objects.create(
        updated_by=usera,
        run_date="2021-07-17T19:41:11Z",
        submission_script=o_script,
    )
    cr4.inputs.set([o_output_3.components.first(), o_output_4.components.first()])
    cr4.outputs.set([o_output_5.components.first()])

    cr5 = CodeRun.objects.create(
        updated_by=usera,
        run_date="2021-07-17T19:51:11Z",
        submission_script=o_script,
    )
    cr5.inputs.set([o_output_5.components.first()])
    cr5.outputs.set([o_output_6.components.first()])

    dp_cr_input_5 = DataProduct.objects.create(
        updated_by=user,
        object=o_input_5,
        namespace=n_prov,
        name="this/is/cr/test/input/5",
        version="0.2.0",
    )

    ExternalObject.objects.create(
        updated_by=user,
        data_product=dp_cr_input_5,
        alternate_identifier="this_is_cr_test_input_5",
        alternate_identifier_type="text",
        release_date=parser.isoparse("2020-07-10T18:38:00Z"),
        title="this is cr test input 5",
        description="this is code run test input 5",
        original_store=sl_file_3,
        primary_not_supplement=False,
    )

    DataProduct.objects.create(
        updated_by=user,
        object=o_input_6,
        namespace=n_prov,
        name="this/is/cr/test/input/6",
        version="0.2.0",
    )

    cr6 = CodeRun.objects.create(
        updated_by=userb,
        run_date="2021-07-17T19:59:11Z",
        description="Test run",
        code_repo=o_code_2,
        model_config=o_model_config_2,
        submission_script=o_script_2,
    )
    cr6.inputs.set([o_input_5.components.first(), o_input_6.components.first()])
    cr6.outputs.set([o_output_7.components.first(), o_output_8.components.first()])


if __name__ == "__main__":
    init_db()
