from data_management.models import (
    Author,
    CodeRepoRelease,
    CodeRun,
    DataProduct,
    ExternalObject,
    FileType,
    Issue,
    Object,
    ObjectComponent,
    StorageLocation,
    StorageRoot,
    UserAuthor,
    Namespace,
)
from django.contrib.auth import get_user_model


ANALYSIS_DESCRIPTION = "Analysis / processing script location"
GITHUB_COM = "https://github.com/"
SEIRS_DESCRIPTION = "SEIRS model results"
SUBMISSION_SCRIPT_DESCRIPTION = "Submission script location in local datastore"
YAML_DESCRIPTION = "Working config.yaml file location in local datastore"


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
    git = FileType.objects.get_or_create(updated_by=user, extension="git", name="git")[
        0
    ]
    pdf = FileType.objects.get_or_create(updated_by=user, extension="pdf", name="pdf")[
        0
    ]
    png = FileType.objects.get_or_create(updated_by=user, extension="png", name="png")[
        0
    ]

    issue_1 = Issue.objects.get_or_create(
        updated_by=user,
        severity=3,
        description="Model has been run over 3649 timesteps rather than 1000",
    )[0]

    issue_2 = Issue.objects.get_or_create(
        updated_by=user,
        severity=5,
        description=(
            "Model has assumed there to be 365 days in a year rather than 365.25"
        ),
    )[0]

    author_1 = Author.objects.get_or_create(
        updated_by=user,
        name="Author 1",
    )[0]

    author_2 = Author.objects.get_or_create(
        updated_by=user,
        name="Author 2",
    )[0]

    author_3 = Author.objects.get_or_create(
        updated_by=user,
        name="Author 3",
    )[0]

    UserAuthor.objects.get_or_create(updated_by=user, user=user, author=author_3)

    storage_root_1 = StorageRoot.objects.get_or_create(
        root="file:///Users/user_home/.fair/data/",
        local=True,
        updated_by=user,
    )[0]

    storage_root_2 = StorageRoot.objects.get_or_create(
        root=GITHUB_COM,
        local=False,
        updated_by=user,
    )[0]

    storage_location_1 = StorageLocation.objects.get_or_create(
        path="PSU/SEIRS_model/parameters/1.0.0.csv",
        hash="6294a5951677e6b8438cabf55234b7974adeaee3",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_2 = StorageLocation.objects.get_or_create(
        path="data/jobs/2021-10-07_12_14_00_128346//config.yaml",
        hash="6ed2ca688a71c3964597f64eac5249ffcf80bf7f",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_3 = StorageLocation.objects.get_or_create(
        path="data/jobs/2021-10-07_12_14_00_128346//script.sh",
        hash="89961dc1ec5e622fa68e678495569f10f0f285bb",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_4 = StorageLocation.objects.get_or_create(
        path="FAIRDataPipeline/SimpleModel.git",
        hash="3006fae4e2d0fc04233190ae4161be4c09b76a38",
        public=False,
        updated_by=user,
        storage_root=storage_root_2,
    )[0]

    storage_location_5 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/results/model_output/R/"
            "72e13dceb2a924f0babad5e1920b3191af0ebe50.csv"
        ),
        hash="72e13dceb2a924f0babad5e1920b3191af0ebe50",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_6 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/results/figure/R/555f1e26344f95298c9d483a65f13505d4534d3f.pdf"
        ),
        hash="555f1e26344f95298c9d483a65f13505d4534d3f",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_7 = StorageLocation.objects.get_or_create(
        path="jobs/2021-10-07_12_14_20_009490/config.yaml",
        hash="72b4dbee1d3de2a1d915be9940a6a88f02634bc4",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_8 = StorageLocation.objects.get_or_create(
        path="jobs/2021-10-07_12_14_20_009490/script.sh",
        hash="967f93058392d7cf73317c5123b0d60143da68d9",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_9 = StorageLocation.objects.get_or_create(
        path="FAIRDataPipeline/javaSimpleModel.git",
        hash="c8d9fa8cddf079b065eca42d7b4b276639756c2f",
        public=True,
        updated_by=user,
        storage_root=storage_root_2,
    )[0]

    storage_location_10 = StorageLocation.objects.get_or_create(
        path="SEIRS_model/results/model_output/java/0.0.1.csv",
        hash="331ca0438da07027796819709296b4da0d81732b",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_11 = StorageLocation.objects.get_or_create(
        path="jobs/2021-10-07_12_14_44_801088/config.yaml",
        hash="6bcb49dca940f932ac9c885a1eae23fc9d8e43222f13b1944d60bc646c84b2ea",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_12 = StorageLocation.objects.get_or_create(
        path="jobs/2021-10-07_12_14_44_801088/script.sh",
        hash="ca709e32ffbbf95a30ff93a2f848827566d55df7b093d6c3bec2cdbaf815a0b1",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_13 = StorageLocation.objects.get_or_create(
        path="FAIRDataPipeline/DataPipeline.jl.git",
        hash="6382a2c26cba21ee3ca03d031e3094a3d038923d5653a38a66342027f253f769",
        public=False,
        updated_by=user,
        storage_root=storage_root_2,
    )[0]

    storage_location_14 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/results/figure/julia/"
            "f28c29183a9880d4b6b32ff0391c033a2e878c9c7260037473dbfce04940b35d.pdf"
        ),
        hash="e42682dcaca4a3aacb1ce2da683f1b285f75b98749f2772244bdf6dcef309e26",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_15 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/results/model_output/julia/"
            "e601a89e9e1f6a8f263ca102cf0cffde1a880c91534cc63eadb75cb0cfb12d67.csv"
        ),
        hash="6974174e21eca43e03c3f412589160a795596de4068f29540c9da74c71904773",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_16 = StorageLocation.objects.get_or_create(
        path="jobs/2021-10-07_12_15_53_596966/config.yaml",
        hash="012fc266f39697d42a6926af2b145e965cce335b",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_17 = StorageLocation.objects.get_or_create(
        path="jobs/2021-10-07_12_15_53_596966/script.sh",
        hash="8888514380fa211b0c1869059316652e2ead3dd7",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_18 = StorageLocation.objects.get_or_create(
        path="FAIRDataPipeline/pythonFDP.git",
        hash="5990e80e3e6f0cd6d81e702926518ae16fa18e88",
        public=True,
        updated_by=user,
        storage_root=storage_root_2,
    )[0]

    storage_location_19 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/results/model_output/python/"
            "f94100af31fb54b5cdfaa22b31eadbad13c9e633.csv"
        ),
        hash="f94100af31fb54b5cdfaa22b31eadbad13c9e633",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_20 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/results/figure/python/"
            "d78bf7a40b694c9933015b521f380633af6a7de5.png"
        ),
        hash="d78bf7a40b694c9933015b521f380633af6a7de5",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_21 = StorageLocation.objects.get_or_create(
        path="jobs/2021-10-07_12_17_07_254572//config.yaml",
        hash="8cfbdca1f593ddc754c355ac9ed7be7113c718ae",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_22 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/compare_results/output/"
            "c2351d9bb49857728421e9344d88a45f9e88e835.toml"
        ),
        hash="88b4e0bf5abaf43cdd96ed2bdb2e63f8eefd75c1",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_23 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/compare_results/output/"
            "c2351d9bb49857728421e9344d88a45f9e88e835.toml"
        ),
        hash="c2351d9bb49857728421e9344d88a45f9e88e835",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    storage_location_24 = StorageLocation.objects.get_or_create(
        path=(
            "SEIRS_model/compare_results/figure/"
            "a5ffd3479af8e37f9ea128a36b5aeb75240d1160.pdf"
        ),
        hash="a5ffd3479af8e37f9ea128a36b5aeb75240d1160",
        public=True,
        updated_by=user,
        storage_root=storage_root_1,
    )[0]

    object_1 = Object.objects.get_or_create(
        description="Static parameters of the model",
        updated_by=user,
        storage_location=storage_location_1,
        file_type=csv_file,
    )[0]
    object_1.authors.add(author_1)

    object_2 = Object.objects.get_or_create(
        description=YAML_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_2,
        file_type=yaml_document,
    )[0]
    object_2.authors.add(author_1)

    object_3 = Object.objects.get_or_create(
        description=SUBMISSION_SCRIPT_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_3,
        file_type=shell_script,
    )[0]
    object_3.authors.add(author_1)

    object_4 = Object.objects.get_or_create(
        description=ANALYSIS_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_4,
        file_type=git,
    )[0]
    object_4.authors.add(author_1)

    object_5 = Object.objects.get_or_create(
        updated_by=user,
        storage_location=storage_location_5,
        file_type=pdf,
    )[0]
    object_5.authors.add(author_1)

    object_6 = Object.objects.get_or_create(
        updated_by=user,
        storage_location=storage_location_6,
        file_type=pdf,
    )[0]
    object_6.authors.add(author_1)

    object_7 = Object.objects.get_or_create(
        description=YAML_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_7,
        file_type=yaml_document,
    )[0]
    object_7.authors.add(author_2)

    object_8 = Object.objects.get_or_create(
        description=SUBMISSION_SCRIPT_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_8,
        file_type=shell_script,
    )[0]
    object_8.authors.add(author_2)

    object_9 = Object.objects.get_or_create(
        description=ANALYSIS_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_9,
    )[0]
    object_9.authors.add(author_2)

    object_10 = Object.objects.get_or_create(
        description=SEIRS_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_10,
        file_type=csv_file,
    )[0]
    object_10.authors.add(author_2)

    object_11 = Object.objects.get_or_create(
        description="Working config file.",
        updated_by=user,
        storage_location=storage_location_11,
        file_type=yaml_document,
    )[0]
    object_11.authors.add(author_1)

    object_12 = Object.objects.get_or_create(
        description="Submission script (Julia.)",
        updated_by=user,
        storage_location=storage_location_12,
        file_type=shell_script,
    )[0]
    object_12.authors.add(author_1)

    object_13 = Object.objects.get_or_create(
        description="Remote code repository.",
        updated_by=user,
        storage_location=storage_location_13,
        file_type=git,
    )[0]
    object_13.authors.add(author_1)

    object_14 = Object.objects.get_or_create(
        description="SEIRS output plot",
        updated_by=user,
        storage_location=storage_location_14,
        file_type=pdf,
    )[0]
    object_14.authors.add(author_1)

    object_15 = Object.objects.get_or_create(
        description=SEIRS_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_15,
        file_type=csv_file,
    )[0]
    object_15.authors.add(author_1)

    object_16 = Object.objects.get_or_create(
        description="Working config.yaml location in datastore",
        updated_by=user,
        storage_location=storage_location_16,
        file_type=yaml_document,
    )[0]
    object_16.authors.add(author_1)

    object_17 = Object.objects.get_or_create(
        description="Working script location in datastore",
        updated_by=user,
        storage_location=storage_location_17,
        file_type=python_script,
    )[0]
    object_17.authors.add(author_1)

    object_18 = Object.objects.get_or_create(
        description=ANALYSIS_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_18,
    )[0]
    object_18.authors.add(author_1)

    object_19 = Object.objects.get_or_create(
        description=SEIRS_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_19,
        file_type=csv_file,
    )[0]
    object_19.authors.add(author_1)

    object_20 = Object.objects.get_or_create(
        description="SEIRS output plot",
        updated_by=user,
        storage_location=storage_location_20,
        file_type=png,
    )[0]
    object_20.authors.add(author_1)

    object_21 = Object.objects.get_or_create(
        description=YAML_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_21,
        file_type=yaml_document,
    )[0]
    object_21.authors.add(author_1)

    object_22 = Object.objects.get_or_create(
        description=SUBMISSION_SCRIPT_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_22,
        file_type=shell_script,
    )[0]
    object_22.authors.add(author_1)

    object_23 = Object.objects.get_or_create(
        description=ANALYSIS_DESCRIPTION,
        updated_by=user,
        storage_location=storage_location_4,
        file_type=git,
    )[0]
    object_23.authors.add(author_1)

    object_24 = Object.objects.get_or_create(
        updated_by=user,
        storage_location=storage_location_23,
        file_type=pdf,
    )[0]
    object_24.authors.add(author_1)

    object_25 = Object.objects.get_or_create(
        updated_by=user,
        storage_location=storage_location_24,
        file_type=pdf,
    )[0]
    object_25.authors.add(author_1)

    code_run_1 = CodeRun.objects.get_or_create(
        run_date="2021-10-07T12:14:02Z",
        description="SEIRS Model R",
        updated_by=user,
        code_repo=object_4,
        model_config=object_2,
        submission_script=object_3,
    )[0]

    code_run_2 = CodeRun.objects.get_or_create(
        run_date="2021-10-07T12:14:26.896067Z",
        description="SEIRS Model java",
        updated_by=user,
        code_repo=object_9,
        model_config=object_7,
        submission_script=object_8,
    )[0]

    code_run_3 = CodeRun.objects.get_or_create(
        run_date="2021-10-07T12:15:13Z",
        description="SEIRS Model julia",
        updated_by=user,
        code_repo=object_13,
        model_config=object_11,
        submission_script=object_12,
    )[0]

    code_run_4 = CodeRun.objects.get_or_create(
        run_date="2021-10-07T12:15:54.842457Z",
        description="SEIRS Model python",
        updated_by=user,
        code_repo=object_18,
        model_config=object_16,
        submission_script=object_17,
    )[0]

    code_run_5 = CodeRun.objects.get_or_create(
        run_date="2021-10-07T12:17:10Z",
        description="SEIRS Model comparison",
        updated_by=user,
        code_repo=object_23,
        model_config=object_21,
        submission_script=object_22,
    )[0]

    CodeRepoRelease.objects.get_or_create(
        updated_by=user,
        name="SimpleModel",
        version="1.0.0",
        website=GITHUB_COM,
        object=object_4,
    )

    CodeRepoRelease.objects.get_or_create(
        updated_by=user,
        name="javaSimpleModel",
        version="1.0.0",
        website=GITHUB_COM,
        object=object_9,
    )

    CodeRepoRelease.objects.get_or_create(
        updated_by=user,
        name="DataPipeline.jl",
        version="1.0.0",
        website=GITHUB_COM,
        object=object_13,
    )

    CodeRepoRelease.objects.get_or_create(
        updated_by=user,
        name="pythonFDP",
        version="1.0.0",
        website=GITHUB_COM,
        object=object_18,
    )

    object_component_1 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_1
    )[0]
    object_component_1.inputs_of.add(code_run_4)
    object_component_1.inputs_of.add(code_run_3)
    object_component_1.inputs_of.add(code_run_2)
    object_component_1.inputs_of.add(code_run_1)

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_2
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_3
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_4
    )

    object_component_5 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_5
    )[0]
    object_component_5.inputs_of.add(code_run_5)
    object_component_5.outputs_of.add(code_run_1)

    object_component_6 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_6
    )[0]
    object_component_6.outputs_of.add(code_run_1)

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_7
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_8
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_9
    )

    object_component_10 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_10
    )[0]
    object_component_10.issues.add(issue_1)
    object_component_10.issues.add(issue_2)
    object_component_10.inputs_of.add(code_run_5)
    object_component_10.outputs_of.add(code_run_2)

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_11
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_12
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_13
    )

    object_component_14 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_14
    )[0]
    object_component_14.outputs_of.add(code_run_3)

    object_component_15 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_15
    )[0]
    object_component_15.inputs_of.add(code_run_5)
    object_component_15.outputs_of.add(code_run_3)

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_16
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_17
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_18
    )

    object_component_19 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_19
    )[0]
    object_component_19.inputs_of.add(code_run_5)
    object_component_19.outputs_of.add(code_run_4)

    object_component_20 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_20
    )[0]
    object_component_20.outputs_of.add(code_run_4)

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_21
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_22
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_23
    )

    ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_24
    )

    object_component_25 = ObjectComponent.objects.get_or_create(
        name="whole_object", whole_object=True, updated_by=user, object=object_25
    )[0]
    object_component_25.outputs_of.add(code_run_5)

    object_component_26 = ObjectComponent.objects.get_or_create(
        name="difference", whole_object=False, updated_by=user, object=object_24
    )[0]
    object_component_26.outputs_of.add(code_run_5)

    namespace_1 = Namespace.objects.get_or_create(
        name="user_1",
        full_name = 'Example user 1', 
        defaults={'updated_by' : user},
    )[0]

    namespace_2 = Namespace.objects.get_or_create(
        name="PSU",
        full_name = "Pennsylvania State University",
        defaults={'website': 'https://ror.org/04p491231', 'updated_by' : user},
    )[0]

    namespace_3 = Namespace.objects.get_or_create(
        name="user_3",
        full_name = "Example user 3",
        defaults={'updated_by' : user},
    )[0]

    namespace_4 = Namespace.objects.get_or_create(
        name="user_4",
        full_name = "Example user 4",
        defaults={'updated_by' : user},
    )[0]

    data_product_1 = DataProduct.objects.get_or_create(
        name="SEIRS_model/parameters",
        version="1.0.0",
        updated_by=user,
        object=object_1,
        namespace=namespace_2,
    )[0]

    DataProduct.objects.get_or_create(
        name="SEIRS_model/results/model_output/R",
        version="0.0.1",
        updated_by=user,
        object=object_5,
        namespace=namespace_1,
    )

    DataProduct.objects.get_or_create(
        name="SEIRS_model/results/figure/R",
        version="0.0.1",
        updated_by=user,
        object=object_6,
        namespace=namespace_1,
    )

    DataProduct.objects.get_or_create(
        name="SEIRS_model/results/model_output/java",
        version="0.0.1",
        updated_by=user,
        object=object_10,
        namespace=namespace_3,
    )

    DataProduct.objects.get_or_create(
        name="SEIRS_model/results/figure/julia",
        version="0.0.1",
        updated_by=user,
        object=object_14,
        namespace=namespace_1,
    )

    DataProduct.objects.get_or_create(
        name="SEIRS_model/results/model_output/julia",
        version="0.0.1",
        updated_by=user,
        object=object_15,
        namespace=namespace_1,
    )

    DataProduct.objects.get_or_create(
        name="SEIRS_model/results/model_output/python",
        version="0.0.1",
        updated_by=user,
        object=object_19,
        namespace=namespace_4,
    )

    DataProduct.objects.get_or_create(
        name="SEIRS_model/results/figure/python",
        version="0.0.1",
        updated_by=user,
        object=object_20,
        namespace=namespace_4,
    )

    DataProduct.objects.get_or_create(
        name="SEIRS_model/compare_results/output",
        version="0.0.1",
        updated_by=user,
        object=object_24,
        namespace=namespace_1,
    )

    DataProduct.objects.get_or_create(
        name="SEIRS_model/compare_results/figure",
        version="0.0.1",
        updated_by=user,
        object=object_25,
        namespace=namespace_1,
    )

    ExternalObject.objects.get_or_create(
        identifier="https://doi.org/10.1038/s41592-020-0856-2",
        primary_not_supplement=True,
        release_date="2021-09-20T12:00",
        title="Static parameters of the model",
        version="1.0.0",
        updated_by=user,
        data_product=data_product_1,
    )
