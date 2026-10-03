"""
Can a registry be rebuilt from an RO Crate?

The crate of a data product is exported from one registry, the registry is emptied,
and the crate is imported through the REST API, as a client would import it. Each
test then compares one kind of record before and after, by what identifies it in any
registry - never by its row in this one.

The bar is the provenance path: every code run with its inputs and outputs by data
product identity, its script and config by hash, and its repo by URL and commit
(`test_code_run_details`, `test_code_run_outputs`, `test_code_run_software`), and
the same path read back from a crate of the rebuilt registry (`test_reexport`). The
other tests compare the metadata around the path.

A test marked expectedFailure is a pending issue: something the crate does not yet
carry, or carries in a form the import cannot use; when the crate gains it the test
passes, the runner reports an unexpected success, and the mark comes off. The import
is deliberately simple - a crate holds either enough or not - and it records nothing
the crate does not say, with one exception: an author or licence that the crate
identifies by the exporting registry's own URL is recognised by the shape of that
URL and imported without an identifier.

Not compared, and not pending: which component of a data product a run read (the
whole file stands for it); file types; and who ran a code run, which the registry
derives from the account that created the row, so that no import can keep it.
"""

from pathlib import PurePosixPath
from unittest import expectedFailure
from urllib.parse import quote, urlparse

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from data_management import models
from .init_shared_ancestry_db import init_db as init_shared_ancestry_db

IMPORT_ROOT = "https://import.example.org/"


def _id(url):
    """The row id at the end of an API URL."""
    return url.rstrip("/").rsplit("/", 1)[1]


def _snapshot():
    """Every record of the registry that a crate could carry, keyed by portable identity."""

    def data_product_id(data_product):
        return (data_product.namespace.name, data_product.name, data_product.version)

    def author_id(author):
        return author.identifier or author.name

    def location(obj):
        return obj.storage_location.hash if obj and obj.storage_location else None

    def data_product_ids(components):
        return frozenset(
            data_product_id(data_product)
            for component in components
            for data_product in component.object.data_products.all()
        )

    snapshot = {
        "namespaces": {
            namespace.name: (namespace.full_name, namespace.website)
            for namespace in models.Namespace.objects.all()
        },
        "authors": {
            author_id(author): (author.name, author.identifier, author.uuid)
            for author in models.Author.objects.all()
        },
        "data_products": {},
        "external_objects": {},
        "code_runs": {},
        "issues": {
            issue.uuid: (
                issue.severity,
                issue.description,
                data_product_ids(issue.component_issues.all()),
            )
            for issue in models.Issue.objects.all()
        },
    }
    for external_object in models.ExternalObject.objects.all():
        snapshot["external_objects"][data_product_id(external_object.data_product)] = {
            "identifier": external_object.identifier,
            "alternate_identifier": external_object.alternate_identifier,
            "title": external_object.title,
            "description": external_object.description,
            "release_date": external_object.release_date,
            "primary": external_object.primary_not_supplement,
        }
    for data_product in models.DataProduct.objects.all():
        obj = data_product.object
        snapshot["data_products"][data_product_id(data_product)] = {
            "hash": location(obj),
            "description": obj.description,
            "authors": frozenset(author_id(author) for author in obj.authors.all()),
            "licences": frozenset(
                (licence.identifier, licence.licence_info)
                for licence in obj.licences.all()
            ),
        }
    for code_run in models.CodeRun.objects.all():
        repo = code_run.code_repo
        snapshot["code_runs"][code_run.uuid] = {
            "description": code_run.description,
            "run_date": code_run.run_date,
            "repo": (str(repo.storage_location), location(repo)) if repo else None,
            "config": location(code_run.model_config),
            "script": location(code_run.submission_script),
            "inputs": data_product_ids(code_run.inputs.all()),
            "outputs": data_product_ids(code_run.outputs.all()),
        }
    return snapshot


def _path(crate):
    """
    What each code run of a crate read and wrote, by portable identity.

    A data file is its namespace, name, version and hash; a software file (the
    config or the script) its hash; a source outside the registry its id.
    """
    graph = {entity["@id"]: entity for entity in crate["@graph"]}

    def files(refs):
        refs = refs if isinstance(refs, list) else [refs]
        described = []
        for ref in refs:
            entity = graph[ref["@id"]]
            if "SoftwareSourceCode" in entity["@type"]:
                described.append(("software", entity.get("sha1")))
            elif "sha1" in entity:
                described.append(
                    (
                        "data",
                        entity["namespace"]["@id"],
                        entity["name"],
                        entity["version"],
                        entity["sha1"],
                    )
                )
            else:
                described.append(("source", entity["@id"]))
        return sorted(described)

    return {
        entity["identifier"]: {
            "instrument": entity.get("instrument", {}).get("@id"),
            "object": files(entity.get("object", [])),
            "result": files(entity.get("result", [])),
        }
        for entity in graph.values()
        if entity.get("@type") == "CreateAction" and "identifier" in entity
    }


def _empty_registry():
    """Delete every row, children before the rows they protect."""
    for model in (
        models.CodeRun,
        models.Issue,
        models.ExternalObject,
        models.DataProduct,
        models.Licence,
        models.CodeRepoRelease,
        models.ObjectComponent,
        models.Object,
        models.FileType,
        models.StorageLocation,
        models.StorageRoot,
        models.Namespace,
        models.Author,
    ):
        model.objects.all().delete()


class CrateImporter:
    """
    Rebuild registry rows from the metadata of an RO Crate, through the REST API.

    `graph` is the crate's `@graph`. Every entity is created once and remembered by
    its `@id`, so that a later entity can refer to it.
    """

    def __init__(self, graph, client):
        self.entities = {entity["@id"]: entity for entity in graph}
        self.client = client
        self.urls = {}
        self.objects = {}

    def _post(self, table, data):
        response = self.client.post(f"/api/{table}/", data, format="json")
        assert response.status_code == 201, (table, data, response.content)
        return response.json()["url"]

    def _get_or_post(self, table, params, data):
        found = self.client.get(f"/api/{table}/", params).json()["results"]
        return found[0]["url"] if found else self._post(table, data)

    def _storage_location(self, root, path, file_hash, public=True):
        root_url = self._get_or_post(
            "storage_root", {"root": root}, {"root": root, "local": False}
        )
        # identical bytes under one root are one storage location, however many
        # objects point at it
        return self._get_or_post(
            "storage_location",
            {"storage_root": _id(root_url), "hash": file_hash, "public": public},
            {
                "path": path,
                "hash": file_hash,
                "public": public,
                "storage_root": root_url,
            },
        )

    def _referenced(self, entity, key):
        """The entities an entity's property points at, as a list."""
        refs = entity.get(key, [])
        refs = refs if isinstance(refs, list) else [refs]
        return [
            self.entities[ref["@id"]] for ref in refs if ref["@id"] in self.entities
        ]

    def _ensure(self, entity_id, make):
        if entity_id not in self.urls:
            self.urls[entity_id] = make(self.entities[entity_id])
        return self.urls[entity_id]

    def _namespace(self, entity):
        data = {"name": entity["name"]}
        if "alternateName" in entity:
            data["full_name"] = entity["alternateName"]
        if "url" in entity:
            data["website"] = entity["url"]
        return self._post("namespace", data)

    def _author(self, entity):
        data = {"name": entity.get("name")}
        # an author with no identifier is identified by the exporting registry's URL,
        # which an importer can only recognise by its shape
        if urlparse(entity["@id"]).scheme in ("http", "https") and not (
            "/api/author/" in entity["@id"] or "/api/users/" in entity["@id"]
        ):
            data["identifier"] = entity["@id"]
        return self._post("author", data)

    def _software(self, entity):
        """A code repo: its url split at the host, and the commit from the id."""
        url = entity["url"]
        parsed = urlparse(url)
        root = f"{parsed.scheme}://{parsed.netloc}/"
        commit = entity["@id"].split("#", 1)[1] if "#" in entity["@id"] else None
        storage_location = self._storage_location(root, parsed.path.lstrip("/"), commit)
        return self._post("object", {"storage_location": storage_location})

    def _extension(self, entity):
        """
        The extension of a file's path, which is all the crate says of its file type.

        A data product's path ends in its version, which has dots of its own, so the
        extension is what follows the version; a software file's path is the file's
        name.
        """
        last = entity["@id"].rsplit("/", 1)[-1]
        if "version" in entity:
            last = last[len(quote(entity["version"], safe="")) :]
            return last.lstrip(".") or None
        return PurePosixPath(last).suffix.lstrip(".") or None

    def _object(self, entity):
        """A file's object, which every data product of the object shares."""
        uuid = entity["identifier"]
        if uuid in self.objects:
            return self.objects[uuid]
        data = {
            "uuid": uuid,
            "storage_location": self._storage_location(
                IMPORT_ROOT, entity["sha1"], entity["sha1"]
            ),
            "description": entity.get("description"),
            "authors": [
                self._ensure(author["@id"], self._author)
                for author in self._referenced(entity, "author")
            ],
        }
        extension = self._extension(entity)
        if extension is not None:
            data["file_type"] = self._get_or_post(
                "file_type",
                {"extension": extension},
                {"name": extension, "extension": extension},
            )
        object_url = self.objects[uuid] = self._post("object", data)
        for licence in self._referenced(entity, "license"):
            # a licence with no identifier is identified by the exporting registry's
            # URL, recognisable only by its shape
            identifier = licence["@id"]
            if not identifier.startswith("http") or "/api/license/" in identifier:
                identifier = None
            self._post(
                "licence",
                {
                    "object": object_url,
                    "licence_info": licence.get("description", ""),
                    "identifier": identifier,
                },
            )
        return object_url

    def _file(self, entity):
        """A file in the data store: its object, and a data product if it is one."""
        if "sha1" not in entity:
            # a source outside the registry, with nothing to register
            return None
        object_url = self._object(entity)
        if "namespace" in entity:
            self._post(
                "data_product",
                {
                    "object": object_url,
                    "namespace": self._ensure(
                        entity["namespace"]["@id"], self._namespace
                    ),
                    "name": entity["name"],
                    "version": entity["version"],
                },
            )
        return object_url

    def _whole_object(self, object_url):
        components = self.client.get(
            "/api/object_component/",
            {"object": _id(object_url), "whole_object": True},
        ).json()["results"]
        return components[0]["url"]

    def _code_run(self, entity):
        software = [
            self._ensure(file["@id"], self._file)
            for file in self._referenced(entity, "object")
            if "SoftwareSourceCode" in file["@type"]
        ]
        inputs = [
            self._ensure(file["@id"], self._file)
            for file in self._referenced(entity, "object")
            if "SoftwareSourceCode" not in file["@type"]
        ]
        outputs = [
            self._ensure(file["@id"], self._file)
            for file in self._referenced(entity, "result")
        ]
        instrument = self._referenced(entity, "instrument")
        data = {
            "uuid": entity["@id"].removeprefix("urn:uuid:"),
            "description": entity.get("description", ""),
            "run_date": entity["startTime"],
            "code_repo": (
                self._ensure(instrument[0]["@id"], self._software)
                if instrument
                else None
            ),
            # the crate does not say which software file is the config and which the
            # script, so the first is taken as the script and nothing as the config
            "submission_script": software[0] if software else None,
            "model_config": None,
            # two names for one object are one component read
            "inputs": list({self._whole_object(url): 1 for url in inputs if url}),
            "outputs": list({self._whole_object(url): 1 for url in outputs if url}),
        }
        return self._post("code_run", data)

    def run(self):
        for entity_id, entity in self.entities.items():
            if entity.get("@type") == "CreateAction":
                self._ensure(entity_id, self._code_run)


class RoundTripTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_shared_ancestry_db(self)
        self.before = _snapshot()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.crate = self._export()
        _empty_registry()
        CrateImporter(self.crate["@graph"], self.client).run()
        self.after = _snapshot()

    def _export(self):
        """The crate of `end`, to the whole depth of its ancestry."""
        end = models.DataProduct.objects.get(name="end")
        response = self.client.get(
            f"/api/ro-crate/data-product/{end.id}/",
            {"depth": 100},
            format="json-ld",
            HTTP_ACCEPT="application/ld+json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_namespaces(self):
        self.assertEqual(self.after["namespaces"], self.before["namespaces"])

    def _local(self, snapshot):
        """The data products that were not registered from an external source."""
        return {
            name: data_product
            for name, data_product in snapshot["data_products"].items()
            if name not in snapshot["external_objects"]
        }

    @expectedFailure
    def test_data_products(self):
        # extra, prepare's other output, is not in the crate at all, as a run's
        # outputs outside the ancestry are not listed
        before, after = self._local(self.before), self._local(self.after)
        self.assertEqual(set(after), set(before))
        for name, data_product in before.items():
            with self.subTest(data_product=name):
                self.assertEqual(after[name], data_product)

    @expectedFailure
    def test_registered_inputs(self):
        # a data product registered from an external source is in the crate only as
        # its identifier: the data product itself, and the source's details, are not
        self.assertEqual(
            self.after["external_objects"], self.before["external_objects"]
        )
        for name in self.before["external_objects"]:
            self.assertEqual(
                self.after["data_products"][name], self.before["data_products"][name]
            )
        for uuid, code_run in self.before["code_runs"].items():
            self.assertEqual(
                self.after["code_runs"][uuid]["inputs"], code_run["inputs"]
            )

    @expectedFailure
    def test_authors(self):
        # an author with no identifier is still identified by this registry's URL
        self.assertEqual(self.after["authors"], self.before["authors"])

    def test_code_runs_exist(self):
        self.assertEqual(set(self.after["code_runs"]), set(self.before["code_runs"]))

    def test_code_run_details(self):
        registered = set(self.before["external_objects"])
        for uuid, code_run in self.before["code_runs"].items():
            with self.subTest(code_run=code_run["description"]):
                after = self.after["code_runs"][uuid]
                for key in ("description", "run_date", "repo"):
                    self.assertEqual(after[key], code_run[key], key)
                # inputs registered from an external source are test_registered_inputs'
                self.assertEqual(
                    after["inputs"] - registered, code_run["inputs"] - registered
                )

    @expectedFailure
    def test_code_run_outputs(self):
        # a data product's crate gives a run with several outputs only one of them
        for uuid, code_run in self.before["code_runs"].items():
            with self.subTest(code_run=code_run["description"]):
                self.assertEqual(
                    self.after["code_runs"][uuid]["outputs"], code_run["outputs"]
                )

    @expectedFailure
    def test_code_run_software(self):
        # the crate does not say which software file is the config and which the script
        for uuid, code_run in self.before["code_runs"].items():
            with self.subTest(code_run=code_run["description"]):
                after = self.after["code_runs"][uuid]
                self.assertEqual(
                    (after["config"], after["script"]),
                    (code_run["config"], code_run["script"]),
                )

    @expectedFailure
    def test_issues(self):
        # issues are not in the crate
        self.assertEqual(self.after["issues"], self.before["issues"])

    @expectedFailure
    def test_reexport(self):
        # two differences remain: a registered input is in the first crate only as
        # its source, which the import cannot register; and the import loses one of
        # a run's two software files, not knowing which is the config and which the
        # script
        self.assertEqual(_path(self._export()), _path(self.crate))
