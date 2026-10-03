import hashlib
import os
import tempfile

from dateutil import parser

from data_management.models import (
    Author,
    CodeRun,
    DataProduct,
    ExternalObject,
    FileType,
    Issue,
    Licence,
    Namespace,
    Object,
    ObjectComponent,
    StorageLocation,
    StorageRoot,
)
from django.contrib.auth import get_user_model


def init_db(test_case):
    """
    Create code runs whose provenance reaches the same things by several routes.

        source -> [prepare] -> raw, extra
        raw -> [left] -> left             raw -> [right] -> right
        left, right -> [pair] -> first, second, twin
        first, second, twin, raw -> [final] -> end

    `raw` is reached from `end` directly and through both `left` and `right`;
    `alias` is a second name for `raw`'s object, so every run that reads `raw` reads
    `alias` too; `twin` is an object of its own holding `second`'s bytes (one
    storage location, two objects), which is how the APIs register identical
    outputs; `extra` is in nobody's ancestry; `pair` is the source of three data
    products; `first` has named components that are written by `pair` and read by
    `final`; and the code runs share a user, a repo, a submission script and (the
    first three) a model config, each of which has the same author. `source` was
    registered from an external source with a DOI; `end` has a licence with an
    identifier and `first` one without; one issue is raised against `raw` and
    another against both `left` and `right`.

    The data store is a `file://` root over real files in a temporary directory
    that lasts as long as `test_case`, as a local registry's is. Each file holds
    its own path and is registered under its real SHA-1; the repo's "hash" is a
    made-up commit.

    """
    user = get_user_model().objects.first()
    directory = tempfile.TemporaryDirectory()
    test_case.addCleanup(directory.cleanup)
    store = directory.name

    sr_github = StorageRoot.objects.create(updated_by=user, root="https://github.com")
    sr_store = StorageRoot.objects.create(updated_by=user, root=f"file://{store}/")
    text_file = FileType.objects.create(
        updated_by=user, name="text file", extension="txt"
    )
    namespace = Namespace.objects.create(
        updated_by=user,
        name="shared",
        full_name="Shared Ancestry",
        website="https://example.org/shared",
    )
    author = Author.objects.create(updated_by=user, name="Ivana Valenti")
    commits = iter(range(1, 100))

    def create_object(storage_root, path):
        if storage_root is sr_store:
            content = f"{path}\n".encode()
            with open(os.path.join(store, path), "wb") as file:
                file.write(content)
            file_hash = hashlib.sha1(content).hexdigest()
        else:
            file_hash = f"{next(commits):040x}"
        storage_location = StorageLocation.objects.create(
            updated_by=user,
            path=path,
            hash=file_hash,
            storage_root=storage_root,
        )
        return Object.objects.create(
            updated_by=user,
            storage_location=storage_location,
            description=path,
            file_type=text_file,
        )

    def create_data_product(name, obj=None):
        if obj is None:
            obj = create_object(sr_store, name)
        DataProduct.objects.create(
            updated_by=user,
            object=obj,
            namespace=namespace,
            name=name,
            version="1.0.0",
        )
        return obj

    def create_code_run(description, inputs, outputs, model_config=None):
        code_run = CodeRun.objects.create(
            updated_by=user,
            run_date="2021-07-17T19:21:11Z",
            description=description,
            code_repo=o_code,
            model_config=model_config,
            submission_script=o_script,
        )
        code_run.inputs.set(inputs)
        code_run.outputs.set(outputs)

    def whole(obj):
        return obj.components.get(whole_object=True)

    o_code = create_object(sr_github, "FAIRDataPipeline/shared")
    o_script = create_object(sr_store, "script")
    o_model_config = create_object(sr_store, "model_config")
    for obj in (o_code, o_script, o_model_config):
        obj.authors.add(author)

    o_source = create_data_product("source")
    o_raw = create_data_product("raw")
    create_data_product("alias", o_raw)
    o_extra = create_data_product("extra")
    o_left = create_data_product("left")
    o_right = create_data_product("right")
    o_first = create_data_product("first")
    for name in ("a", "b"):
        ObjectComponent.objects.create(updated_by=user, object=o_first, name=name)
    o_second = create_data_product("second")
    o_twin = create_data_product(
        "twin",
        Object.objects.create(
            updated_by=user,
            storage_location=o_second.storage_location,
            description="twin",
            file_type=text_file,
        ),
    )
    o_end = create_data_product("end")

    ExternalObject.objects.create(
        updated_by=user,
        data_product=DataProduct.objects.get(object=o_source),
        identifier="https://doi.org/10.5281/zenodo.1234567",
        title="The source data",
        description="Where the source data came from",
        release_date=parser.isoparse("2020-07-10T18:38:00Z"),
    )
    Licence.objects.create(
        updated_by=user,
        object=o_end,
        licence_info="Creative Commons Attribution 4.0",
        identifier="https://creativecommons.org/licenses/by/4.0/",
    )
    Licence.objects.create(
        updated_by=user, object=o_first, licence_info="For project use only"
    )
    Issue.objects.create(
        updated_by=user, severity=7, description="raw has a bad row"
    ).component_issues.set([whole(o_raw)])
    Issue.objects.create(
        updated_by=user, severity=2, description="left and right disagree"
    ).component_issues.set([whole(o_left), whole(o_right)])

    create_code_run(
        "prepare", [whole(o_source)], [whole(o_raw), whole(o_extra)], o_model_config
    )
    create_code_run("left", [whole(o_raw)], [whole(o_left)], o_model_config)
    create_code_run("right", [whole(o_raw)], [whole(o_right)], o_model_config)
    create_code_run(
        "pair",
        [whole(o_left), whole(o_right)],
        [*o_first.components.all(), whole(o_second), whole(o_twin)],
    )
    create_code_run(
        "final",
        [
            *o_first.components.filter(whole_object=False),
            whole(o_second),
            whole(o_twin),
            whole(o_raw),
        ],
        [whole(o_end)],
    )
