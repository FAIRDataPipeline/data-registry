from data_management.models import (
    Author,
    CodeRun,
    DataProduct,
    FileType,
    Namespace,
    Object,
    ObjectComponent,
    StorageLocation,
    StorageRoot,
)
from django.contrib.auth import get_user_model


def init_db():
    """
    Create code runs whose provenance reaches the same things by several routes.

        source -> [prepare] -> raw
        raw -> [left] -> left             raw -> [right] -> right
        left, right -> [pair] -> first, second
        first, second, raw -> [final] -> end

    `raw` is reached from `end` directly and through both `left` and `right`,
    `pair` is the source of two data products, `first` has named components that
    are written by `pair` and read by `final`, and the code runs share a user, a
    repo, a submission script and (the first three) a model config, each of which
    has the same author.

    """
    user = get_user_model().objects.first()

    sr_github = StorageRoot.objects.create(updated_by=user, root="https://github.com")
    sr_example = StorageRoot.objects.create(
        updated_by=user, root="https://example.org/"
    )
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
    hashes = iter(range(1, 100))

    def create_object(storage_root, path):
        storage_location = StorageLocation.objects.create(
            updated_by=user,
            path=path,
            hash=f"{next(hashes):040x}",
            storage_root=storage_root,
        )
        return Object.objects.create(
            updated_by=user,
            storage_location=storage_location,
            description=path,
            file_type=text_file,
        )

    def create_data_product(name):
        obj = create_object(sr_example, name)
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
    o_script = create_object(sr_example, "script")
    o_model_config = create_object(sr_example, "model_config")
    for obj in (o_code, o_script, o_model_config):
        obj.authors.add(author)

    o_source = create_data_product("source")
    o_raw = create_data_product("raw")
    o_left = create_data_product("left")
    o_right = create_data_product("right")
    o_first = create_data_product("first")
    for name in ("a", "b"):
        ObjectComponent.objects.create(updated_by=user, object=o_first, name=name)
    o_second = create_data_product("second")
    o_end = create_data_product("end")

    create_code_run("prepare", [whole(o_source)], [whole(o_raw)], o_model_config)
    create_code_run("left", [whole(o_raw)], [whole(o_left)], o_model_config)
    create_code_run("right", [whole(o_raw)], [whole(o_right)], o_model_config)
    create_code_run(
        "pair",
        [whole(o_left), whole(o_right)],
        [*o_first.components.all(), whole(o_second)],
    )
    create_code_run(
        "final",
        [*o_first.components.filter(whole_object=False), whole(o_second), whole(o_raw)],
        [whole(o_end)],
    )
