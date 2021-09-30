from data_management.models import (
    Author,
    CodeRun,
    DataProduct,
    ExternalObject,
    FileType,
    Object,
    ObjectComponent,
    StorageLocation,
    StorageRoot,
    UserAuthor,
    Namespace,
)
from django.contrib.auth import get_user_model


def init_db():
    user = get_user_model().objects.get_or_create(username="exampleusera")[0]

    csv_file = FileType.objects.get_or_create(
        updated_by=user, extension="csv", name="Comma-Separated Values File"
    )[0]
    FileType.objects.get_or_create(
        updated_by=user, extension="toml", name="TOML Configuration File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="json", name="JavaScript Object Notation File"
    )
    yaml_document = FileType.objects.get_or_create(
        updated_by=user, extension="yaml", name="YAML Document"
    )[0]
    FileType.objects.get_or_create(
        updated_by=user, extension="ini", name="Windows Initialization File"
    )
    FileType.objects.get_or_create(updated_by=user, extension="dat", name="Data File")
    FileType.objects.get_or_create(
        updated_by=user, extension="npy", name="Python NumPy Array File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="xls", name="Microsoft Excel Spreadsheet (Legacy)"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="xlsx", name="Microsoft Excel Spreadsheet"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="doc", name="Microsoft Word Document (Legacy)"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="docx", name="Microsoft Word Document"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="txt", name="Plain Text File"
    )
    FileType.objects.get_or_create(updated_by=user, extension="r", name="R Script File")
    FileType.objects.get_or_create(
        updated_by=user, extension="exe", name="Windows Executable File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="jl", name="Julia Source Code File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="java", name="Java Source Code File"
    )
    shell_script = FileType.objects.get_or_create(
        updated_by=user, extension="sh", name="Bash Shell Script"
    )[0]
    FileType.objects.get_or_create(
        updated_by=user, extension="ps1", name="Windows PowerShell Cmdlet File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="h5", name="Hierarchical Data Format 5 File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="hdf5", name="Hierarchical Data Format 5 File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="pdb", name="Program Database"
    )
    FileType.objects.get_or_create(updated_by=user, extension="zip", name="Zipped File")
    FileType.objects.get_or_create(
        updated_by=user, extension="tar", name="Consolidated Unix File Archive"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="tar.gz", name="Compressed Tarball File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="gz", name="Gnu Zipped Archive"
    )
    FileType.objects.get_or_create(updated_by=user, extension="xml", name="XML File")
    FileType.objects.get_or_create(
        updated_by=user, extension="ascii", name="ASCII Text File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="sql", name="Structured Query Language Data File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="sas", name="SAS Program File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="rdata", name="R Workspace File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="tab", name="Typinator Set File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="cfg", name="Configuration File"
    )
    FileType.objects.get_or_create(
        updated_by=user, extension="pkl", name="Python Pickle File"
    )
    python_script = FileType.objects.get_or_create(
        updated_by=user, extension="py", name="Python Script"
    )[0]
    pdf = FileType.objects.get_or_create(updated_by=user, extension="pdf", name="pdf")[
        0
    ]

    author = Author.objects.get_or_create(
        updated_by=user,
        name="Interface Test",
        uuid="2ddb2358-84bf-43ff-b2aa-3ac7dc3b49f1",
    )[0]

    UserAuthor.objects.get_or_create(updated_by=user, user=user, author=author)

    storage_root_1 = StorageRoot.objects.get_or_create(
        root="file:///var/folders/0f/fj5r_1ws15x4jzgnm27h_y6h0000gr/T/tmptjtzaz9p/data_store/",
        local=True,
        updated_by=user,
    )[0]

    storage_root_2 = StorageRoot.objects.get_or_create(
        root="/var/folders/0f/fj5r_1ws15x4jzgnm27h_y6h0000gr/T/tmptjtzaz9p/data_store",
        local=True,
        updated_by=user,
    )[0]

    storage_location_1 = StorageLocation.objects.get_or_create(
        path="BioSS/disease/sars_cov2/SEINRD_model/parameters/static_params/0.20210914.0.csv",
        hash="ff77a4ec301a7f7520784e5a6ba0e9539b80867d",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_2 = StorageLocation.objects.get_or_create(
        path="BioSS/disease/sars_cov2/SEINRD_model/parameters/rts/0.20210914.0.csv",
        hash="51d991044075b64994f4c795b07d85c9fd351f1a",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_3 = StorageLocation.objects.get_or_create(
        path="BioSS/disease/sars_cov2/SEINRD_model/parameters/efoi/0.20210914.0.csv",
        hash="3b6825cb72915d2dfbb74439f78cccfb92129368",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_4 = StorageLocation.objects.get_or_create(
        path="/var/folders/0f/fj5r_1ws15x4jzgnm27h_y6h0000gr/T/tmptjtzaz9p/data_store/jobs/2021-09-14_16_05_18_613674/config.yaml",
        hash="570605496a6ae60062c476330d49fe21c2736fca",
        public=True,
        updated_by=user,
        storage_root=storage_root_2,
    )[0]

    storage_location_5 = StorageLocation.objects.get_or_create(
        path="/var/folders/0f/fj5r_1ws15x4jzgnm27h_y6h0000gr/T/tmptjtzaz9p/data_store/jobs/2021-09-14_16_05_18_613674/script.sh",
        hash="62f1262d526266d374161c29ee4a9763f5b0ce45",
        public=True,
        updated_by=user,
        storage_root=storage_root_2,
    )[0]

    storage_location_6 = StorageLocation.objects.get_or_create(
        path="testing/disease/sars_cov2/SEINRD_model/results/model_output/73ebe2360650ffb3f885d607e04ac2fa036bf8c6.csv",
        hash="73ebe2360650ffb3f885d607e04ac2fa036bf8c6",
        public=True,
        updated_by=user,
        storage_root=storage_root_2,
    )[0]

    storage_location_7 = StorageLocation.objects.get_or_create(
        path="testing/disease/sars_cov2/SEINRD_model/results/figure/6309da2221b0917fcbfa8c02098e499c63e01753.pdf",
        hash="6309da2221b0917fcbfa8c02098e499c63e01753",
        public=True,
        updated_by=user,
        storage_root=storage_root_2,
    )[0]

    object_1 = Object.objects.get_or_create(
        uuid="a5f0522f-6c7b-4d5b-a328-2c129b23652a",
        description="Static parameters of the model",
        updated_by=user,
        storage_location=storage_location_1,
        file_type=python_script,
    )[0]
    object_1.authors.add(author)

    object_2 = Object.objects.get_or_create(
        uuid="f372a204-5b1c-4b31-a39d-4473d607f12a",
        description="Values of Rt at time t",
        updated_by=user,
        storage_location=storage_location_2,
        file_type=python_script,
    )[0]
    object_2.authors.add(author)

    object_3 = Object.objects.get_or_create(
        uuid="00f26144-2ee2-46f8-b4fe-fa2d8bfed341",
        description="Effective force of infection at time t",
        updated_by=user,
        storage_location=storage_location_3,
        file_type=python_script,
    )[0]
    object_3.authors.add(author)

    object_4 = Object.objects.get_or_create(
        uuid="ff351c5b-0d53-4341-92b3-4a54a09190e1",
        description="Working config.yaml file location in local datastore",
        updated_by=user,
        storage_location=storage_location_4,
        file_type=yaml_document,
    )[0]
    object_4.authors.add(author)

    object_5 = Object.objects.get_or_create(
        uuid="d243ebc0-d6aa-4c09-90ea-331c87e24973",
        description="Submission script location in local datastore",
        updated_by=user,
        storage_location=storage_location_5,
        file_type=shell_script,
    )[0]
    object_5.authors.add(author)

    object_6 = Object.objects.get_or_create(
        uuid="fc1ff6fc-d42a-4103-9991-9f2a0d50a761",
        updated_by=user,
        storage_location=storage_location_6,
        file_type=csv_file,
    )[0]
    object_6.authors.add(author)

    object_7 = Object.objects.get_or_create(
        uuid="36696f81-cdf1-4871-a984-476132b2b4b9",
        updated_by=user,
        storage_location=storage_location_7,
        file_type=pdf,
    )[0]
    object_7.authors.add(author)

    code_run = CodeRun.objects.get_or_create(
        uuid="bff4b8f6-f720-4a73-b63d-1f73229663db",
        run_date="2021-09-14T16:05:22Z",
        description="Simple Model",
        updated_by=user,
        model_config=object_4,
        submission_script=object_5,
    )[0]

    object_component_1 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_1
    )[0]
    object_component_1.inputs_of.add(code_run)

    object_component_2 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_2
    )[0]
    object_component_2.inputs_of.add(code_run)

    object_component_3 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_3
    )[0]
    object_component_3.inputs_of.add(code_run)

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_4
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_5
    )

    object_component_6 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_6
    )[0]
    object_component_6.outputs_of.add(code_run)

    object_component_7 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_7
    )[0]
    object_component_7.outputs_of.add(code_run)

    namespace = Namespace.objects.get_or_create(
        name="BioSS",
        full_name="Biomathematics and Statistics Scotland",
        website="https://www.bioss.ac.uk",
        updated_by=user,
    )[0]

    data_product_1 = DataProduct.objects.get_or_create(
        name="disease/sars_cov2/SEINRD_model/parameters/static_params",
        version="0.20210914.0",
        updated_by=user,
        object=object_1,
        namespace=namespace,
    )[0]

    data_product_2 = DataProduct.objects.get_or_create(
        name="disease/sars_cov2/SEINRD_model/parameters/rts",
        version="0.20210914.0",
        updated_by=user,
        object=object_2,
        namespace=namespace,
    )[0]

    data_product_3 = DataProduct.objects.get_or_create(
        name="disease/sars_cov2/SEINRD_model/parameters/efoi",
        version="0.20210914.0",
        updated_by=user,
        object=object_3,
        namespace=namespace,
    )[0]

    DataProduct.objects.get_or_create(
        name="disease/sars_cov2/SEINRD_model/results/model_output",
        version="0.0.1",
        updated_by=user,
        object=object_6,
        namespace=namespace,
    )

    DataProduct.objects.get_or_create(
        name="disease/sars_cov2/SEINRD_model/results/figure",
        version="0.0.1",
        updated_by=user,
        object=object_7,
        namespace=namespace,
    )

    ExternalObject.objects.get_or_create(
        alternate_identifier="Simple model parameters - Static parameters of the model",
        alternate_identifier_type="simple_model_params",
        primary_not_supplement=True,
        release_date="2021-09-14T16:04:49Z",
        title="Static parameters of the model",
        version="0.20210914.0",
        updated_by=user,
        data_product=data_product_1,
    )

    ExternalObject.objects.get_or_create(
        alternate_identifier="Simple model parameters - Values of Rt at time t",
        alternate_identifier_type="simple_model_params",
        primary_not_supplement=True,
        release_date="2021-09-14T16:04:49Z",
        title="Values of Rt at time t",
        version="0.20210914.0",
        updated_by=user,
        data_product=data_product_2,
    )

    ExternalObject.objects.get_or_create(
        alternate_identifier="Simple model parameters - Effective force of infection",
        alternate_identifier_type="simple_model_params",
        primary_not_supplement=True,
        release_date="2021-09-14T16:04:49Z",
        title="Effective force of infection at time t",
        version="0.20210914.0",
        updated_by=user,
        data_product=data_product_3,
    )
