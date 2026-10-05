import io
from unittest import mock
import zipfile

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from data_management import models, prov, rocrate
from data_management.rest import views
from .initdb import init_db
from .init_prov_db import init_db as init_prov_db
from .init_shared_ancestry_db import init_db as init_shared_ancestry_db


class UsersAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_full_name(self):
        self.assertEqual(self.user.full_name(), "User Not Found")

    def test_user_orgs(self):
        self.assertEqual(self.user.orgs(), [])

    # def _get_token(self):
    #     request = self.factory.get(reverse('get_token'))
    #     request.user = self.user
    #     response = views.get_token(request)
    #     self.assertEqual(response.status_code, 200)
    #     self.assert_(response.content.decode().startswith('Your token is: '))
    #     token = response.content.decode().replace('Your token is: ', '')
    #     return token

    def test_get_list_without_authentication(self):
        client = APIClient()
        url = reverse("user-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(), {"detail": "Authentication credentials were not provided."}
        )

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("user-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 4)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("user-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["username"], "Test User")

    def test_filter_by_username(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("user-list")
        response = client.get(url, data={"username": "testuserb"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["username"], "testuserb")

    def test_get_username_without_authentication(self):
        client = APIClient()
        url = reverse("username")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json(), {"detail": "Authentication credentials were not provided."}
        )

    def test_get_username(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("username")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"username": self.user.username})


class GroupsAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("group-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 0)


class StorageRootAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("storageroot-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 9)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("storageroot-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["root"], "https://jptcp.com/")

    def test_filter_by_root(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("storageroot-list")
        response = client.get(url, data={"root": "https://github.com"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["root"], "https://github.com")


class StorageLocationAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("storagelocation-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 20)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("storagelocation-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json()["path"],
            "master/SCRC/human/infection/SARS-CoV-2/symptom-probability/0.1.0.toml",
        )

    def test_filter_by_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("storagelocation-list")
        response = client.get(
            url,
            data={
                "path": "master/SCRC/human/infection/SARS-CoV-2/latent-period/0.1.0.toml"
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["path"],
            "master/SCRC/human/infection/SARS-CoV-2/latent-period/0.1.0.toml",
        )

    def test_filter_by_hash(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("storagelocation-list")
        response = client.get(
            url,
            data={"hash": "43faf6d048b92ed1820db2e662ba403eb0e371fb"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["path"],
            "human/infection/SARS-CoV-2/scotland/cases_and_management/v0.1.0.h5",
        )


class StorageAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_data_for_a_shared_file(self):
        # identical bytes under two objects are one storage location; the download
        # view must serve it, not report it as not found
        from django.contrib.sites.models import Site

        domain = Site.objects.get_current().domain
        root = models.StorageRoot.objects.create(
            updated_by=self.user, root=f"https://{domain}/data/"
        )
        location = models.StorageLocation.objects.create(
            updated_by=self.user, path="abc123", hash="abc123", storage_root=root
        )
        for description in ("first copy", "second copy"):
            models.Object.objects.create(
                updated_by=self.user, storage_location=location, description=description
            )
        with mock.patch.object(
            views.object_storage, "create_url", return_value="https://store/abc123"
        ):
            response = self.client.get("/data/abc123")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://store/abc123")

    def test_get_data(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse(
            "get_data_product",
            kwargs={
                "data_product_name": "human/infection/SARS-CoV-2/symptom-probability",
                "namespace": "FAIR",
                "version": "0.1.0",
            },
        )
        response = client.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            "https://raw.githubusercontent.com/ScottishCovidResponse/DataRepository/master/SCRC/human/infection/SARS-CoV-2/symptom-probability/0.1.0.toml",
        )

    def test_get_external_object(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse(
            "get_external_object",
            kwargs={
                "alternate_identifier": "scottish deaths-involving-coronavirus-covid-19",
                "title": "scottish deaths-involving-coronavirus-covid-19",
                "version": "0.1.0",
            },
        )
        response = client.get(url)

        self.assertEqual(response.status_code, 302)

    def test_get_data_product(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse(
            "get_data_product",
            kwargs={
                "data_product_name": "test/txt",
                "namespace": "FAIR",
                "version": "0.0.1",
            },
        )
        response = client.get(url)

        self.assertEqual(
            b"".join(response.streaming_content), bytes("This is a text file.", "utf-8")
        )


class ObjectAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("object-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 20)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("object-detail", kwargs={"pk": 3})
        response = client.get(url, format="json", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json()["storage_location"],
            "http://localhost/api/storage_location/2/",
        )

    def test_filter_by_storage_location(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("object-list")
        response = client.get(
            url, data={"storage_location": "3"}, format="json", HTTP_HOST="localhost"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["storage_location"], "http://localhost/api/storage_location/3/"
        )


class ObjectComponentAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("objectcomponent-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 52)

    def test_get_detail_whole_object(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("objectcomponent-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["name"], "whole_object")

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("objectcomponent-detail", kwargs={"pk": 18})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["name"], "symptom-probability")

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("objectcomponent-list")
        response = client.get(
            url,
            data={"name": "nhs_health_board/per_location/all_deaths"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "nhs_health_board/per_location/all_deaths")

    def test_filter_by_outputs_of(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("objectcomponent-list")
        code_run = models.CodeRun.objects.get()
        response = client.get(url, data={"outputs_of": code_run.id}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 3)
        self.assertEqual(
            sorted(result["name"] for result in results),
            sorted(code_run.outputs.values_list("name", flat=True)),
        )

    def test_filter_by_unknown_outputs_of(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("objectcomponent-list")
        response = client.get(url, data={"outputs_of": "99999"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])


class IssueAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("issue-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("issue-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["description"], "Test Issue 1")

    def test_filter_by_severity(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("issue-list")
        response = client.get(url, data={"severity": "6"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["description"], "Test Issue 2")

    def test_filter_by_component_issues(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("issue-list")
        with_issue, without_issue = models.ObjectComponent.objects.all()[:2]
        with_issue.issues.add(models.Issue.objects.get(description="Test Issue 2"))

        response = client.get(
            url, data={"component_issues": with_issue.id}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual(
            [result["description"] for result in results], ["Test Issue 2"]
        )

        response = client.get(
            url, data={"component_issues": without_issue.id}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])


class FilterFieldsTests(TestCase):

    def test_every_query_key_has_a_filter(self):
        """
        Test that every field a list endpoint accepts as a query key, including the
        reverse side of each relation, has a filter rather than being accepted and
        ignored. This checks only that each filter exists; what the filters match is
        tested per endpoint.
        """
        backend = views.CustomDjangoFilterBackend()
        for name, model in models.all_models.items():
            with self.subTest(model=name):
                view = getattr(views, name + "ViewSet")()
                filterset = backend.get_filterset_class(view, model.objects.all())
                self.assertEqual(
                    set(model.filter_field_names()) - set(filterset.base_filters), set()
                )


class CodeRunAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("coderun-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("coderun-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json()["description"],
            "Script run to upload and process scottish coronavirus-covid-19-management-information",
        )

    def test_filter_by_run_date(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("coderun-list")
        response = client.get(
            url, data={"run_date": "2020-07-17T18:21:11Z"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["description"],
            "Script run to upload and process scottish coronavirus-covid-19-management-information",
        )

    def test_filter_by_description(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("coderun-list")
        response = client.get(
            url,
            data={
                "description": "Script run to upload and process scottish coronavirus-covid-19-management-information"
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["description"],
            "Script run to upload and process scottish coronavirus-covid-19-management-information",
        )


class ExternalObjectAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("externalobject-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 2)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("externalobject-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json()["alternate_identifier"],
            "scottish deaths-involving-coronavirus-covid-19",
        )

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("externalobject-list")
        response = client.get(
            url,
            data={
                "alternate_identifier": "scottish coronavirus-covid-19-management-information"
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["alternate_identifier"],
            "scottish coronavirus-covid-19-management-information",
        )

    def test_filter_by_title(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("externalobject-list")
        response = client.get(
            url,
            data={"title": "scottish deaths-involving-coronavirus-covid-19"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["alternate_identifier"],
            "scottish deaths-involving-coronavirus-covid-19",
        )

    def _url(self, view, pk):
        return f"http://testserver{reverse(view, kwargs={'pk': pk})}"

    def _register(self, client, data_product_pk, **extra):
        """Register a source for a data product as a released CLI does: one POST."""
        data = {
            "data_product": self._url("dataproduct-detail", data_product_pk),
            "identifier": "https://doi.org/10.5281/zenodo.99",
            "title": "A deposit",
            "release_date": "2020-07-10T18:38:00Z",
            "primary_not_supplement": True,
        }
        data.update(extra)
        return client.post(reverse("externalobject-list"), data, format="json")

    def test_one_source_shared_by_two_registrations(self):
        # two data products registered from one source share one row; the second
        # registration fills what the first left empty, and both are 201
        client = APIClient()
        client.force_authenticate(user=self.user)
        before = models.ExternalObject.objects.count()
        first = self._register(client, 1)
        self.assertEqual(first.status_code, 201, first.content)
        store = self._url("storagelocation-detail", 1)
        second = self._register(client, 2, original_store=store, description="found")
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(first.json()["url"], second.json()["url"])
        self.assertEqual(models.ExternalObject.objects.count(), before + 1)

        row = second.json()
        self.assertEqual(row["original_store"], store)
        self.assertEqual(row["description"], "found")
        # read, data_product is the first linked data product; data_products all of them
        self.assertEqual(row["data_product"], self._url("dataproduct-detail", 1))
        self.assertEqual(
            set(row["data_products"]),
            {self._url("dataproduct-detail", 1), self._url("dataproduct-detail", 2)},
        )
        for pk in (1, 2):
            product = client.get(reverse("dataproduct-detail", kwargs={"pk": pk}))
            self.assertEqual(product.json()["external_object"], row["url"])

    def test_first_registration_wins(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        store = self._url("storagelocation-detail", 1)
        self._register(client, 1, original_store=store, description="first")
        other = self._url("storagelocation-detail", 2)
        second = self._register(client, 2, original_store=other, description="second")
        row = second.json()
        self.assertEqual(row["original_store"], store)
        self.assertEqual(row["description"], "first")

    def test_titles_tell_sources_apart(self):
        # the same identifier with another title is another source; the same title
        # with another version too; and a direct duplicate is merged, not refused
        client = APIClient()
        client.force_authenticate(user=self.user)
        before = models.ExternalObject.objects.count()
        self._register(client, 1)
        self._register(client, 2, title="One file of the deposit")
        self._register(client, 2, version="2.0.0")
        self.assertEqual(models.ExternalObject.objects.count(), before + 3)
        plain = {k: v for k, v in self._register(client, 1).json().items()}
        self.assertEqual(models.ExternalObject.objects.count(), before + 3)
        self.assertEqual(plain["version"], "1.0.0")

    def test_lookup_by_data_product(self):
        # a released CLI looks a registration up by the data product and its version
        client = APIClient()
        client.force_authenticate(user=self.user)
        self._register(client, 1)
        product = models.DataProduct.objects.get(pk=1)
        url = reverse("externalobject-list")
        found = client.get(url, {"data_product": 1, "version": product.version}).json()
        self.assertEqual(len(found["results"]), 1)
        self.assertEqual(
            found["results"][0]["data_product"], self._url("dataproduct-detail", 1)
        )
        wrong = client.get(url, {"data_product": 1, "version": "9.9.9"}).json()
        self.assertEqual(len(wrong["results"]), 0)
        self.assertEqual(len(client.get(url, {"data_product": 1}).json()["results"]), 1)
        unlinked = models.DataProduct.objects.filter(external_object=None).first()
        self.assertEqual(
            len(client.get(url, {"data_product": unlinked.pk}).json()["results"]), 0
        )

    def test_identity_is_unique_in_the_database(self):
        # the constraints hold for each kind of identifier, nulls notwithstanding
        from django.db import IntegrityError, transaction

        common = {"updated_by": self.user, "title": "t", "release_date": "2020-07-10T18:38:00Z"}
        models.ExternalObject.objects.create(identifier="https://doi.org/10.5281/zenodo.1", **common)
        with self.assertRaises(IntegrityError), transaction.atomic():
            models.ExternalObject.objects.create(identifier="https://doi.org/10.5281/zenodo.1", **common)
        models.ExternalObject.objects.create(
            alternate_identifier="local", alternate_identifier_type="name", **common
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            models.ExternalObject.objects.create(
                alternate_identifier="local", alternate_identifier_type="name", **common
            )

class QualityControlledAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("qualitycontrolled-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("qualitycontrolled-detail", kwargs={"pk": 1})
        response = client.get(url, format="json", HTTP_HOST="localhost")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["object"], "http://localhost/api/object/16/")
        self.assertEqual(response.json()["document"], "http://localhost/api/object/18/")


class KeywordAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("keyword-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 5)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("keyword-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["keyphrase"], "treatment")

    def test_filter_by_keyphrase(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("keyword-list")
        response = client.get(
            url, data={"keyphrase": "monoclonal antibodies"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["keyphrase"], "monoclonal antibodies")

    def test_filter_by_keyphrase_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("keyword-list")
        response = client.get(url, data={"keyphrase": "co*"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 2)

    def test_one_identifier_on_many_objects(self):
        # the same ontology term applies to many objects, but to one object once
        client = APIClient()
        client.force_authenticate(user=self.user)
        term = "http://purl.obolibrary.org/obo/NCIT_C16960"

        def post(pk):
            obj = reverse("object-detail", kwargs={"pk": pk})
            return client.post(
                reverse("keyword-list"),
                {
                    "object": f"http://testserver{obj}",
                    "keyphrase": "patient",
                    "identifier": term,
                },
                format="json",
            )

        self.assertEqual(post(1).status_code, 201)
        self.assertEqual(post(2).status_code, 201)
        self.assertEqual(post(1).status_code, 409)


class AuthorAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("author-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("author-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["name"], "Ivana Valenti")

    def test_filter_by_family_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("author-list")
        response = client.get(url, data={"name": "*ti"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 2)

    def test_filter_by_family_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("author-list")
        response = client.get(url, data={"name": "*Cipriani"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Maria Cipriani")

    def test_filter_by_given_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("author-list")
        response = client.get(url, data={"name": "Rosanna*"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Rosanna Massabeti")


class LicenceAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("licence-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("licence-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("Copyright 2020 SCRC", response.json()["licence_info"])

    def test_one_url_on_many_objects(self):
        # the same licence applies to many objects, but to one object once
        client = APIClient()
        client.force_authenticate(user=self.user)
        cc_by = "https://creativecommons.org/licenses/by/4.0/"

        def post(pk):
            obj = reverse("object-detail", kwargs={"pk": pk})
            return client.post(
                reverse("licence-list"),
                {
                    "object": f"http://testserver{obj}",
                    "licence_info": "CC BY 4.0",
                    "identifier": cc_by,
                },
                format="json",
            )

        self.assertEqual(post(1).status_code, 201)
        self.assertEqual(post(2).status_code, 201)
        self.assertEqual(post(1).status_code, 409)


class NamespaceAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("namespace-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 2)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("namespace-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["name"], "FAIR")

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("namespace-list")
        response = client.get(url, data={"name": "simple_network_sim"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "simple_network_sim")

    def test_filter_by_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("namespace-list")
        response = client.get(url, data={"name": "[fF]*"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)


class DataProductAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("dataproduct-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 14)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("dataproduct-detail", kwargs={"pk": 3})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.json()["name"], "human/infection/SARS-CoV-2/symptom-probability"
        )

    def test_filter_by_namespace(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("dataproduct-list")
        response = client.get(url, data={"namespace": "1"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 10)

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("dataproduct-list")
        response = client.get(
            url,
            data={"name": "human/infection/SARS-CoV-2/latent-period"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "human/infection/SARS-CoV-2/latent-period")

    def test_filter_by_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("dataproduct-list")
        response = client.get(
            url, data={"name": "human/infection/SARS-CoV-2/*"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 7)

    def test_filter_by_version(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("dataproduct-list")
        response = client.get(url, data={"version": "0.1.0"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 13)


class CodeRepoReleaseAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("codereporelease-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("codereporelease-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["name"], "ScottishCovidResponse/SCRCdata")

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("codereporelease-list")
        response = client.get(
            url, data={"name": "ScottishCovidResponse/SCRCdata"}, format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "ScottishCovidResponse/SCRCdata")

    def test_filter_by_version(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("codereporelease-list")
        response = client.get(url, data={"version": "0.1.0"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "ScottishCovidResponse/SCRCdata")


class KeyvalueAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("keyvalue-list")
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 4)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("keyvalue-detail", kwargs={"pk": 1})
        response = client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()["key"], "TestKey1")

    def test_filter_by_key(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("keyvalue-list")
        response = client.get(url, data={"key": "TestKey2"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["key"], "TestKey2")


class ProvAPITests(TestCase):

    APPLICATION_JSON = "application/json"
    DCAT_DATASET = "dcat:Dataset"
    DCAT_HAS_VERSION = "dcat:hasVersion"
    DCTERMS_CREATOR = "dcterms:creator"
    DCTERMS_DESCRIPTION = "dcterms:description"
    DCTERMS_FORMAT = "dcterms:format"
    DCTERMS_IDENTIFIER = "dcterms:identifier"
    DCTERMS_ISSUED = "dcterms:issued"
    DCTERMS_MODIFIED = "dcterms:modified"
    DCTERMS_TITLE = "dcterms:title"
    FOAF_NAME = "foaf:name"
    ID4 = "_:id4"
    ID9 = "_:id9"
    ID11 = "_:id11"
    ID19 = "_:id19"
    ID24 = "_:id24"
    LREG_AUTHOR = "lreg:api/author/"
    LREG_CODE_RUN = "lreg:api/code_run/"
    LREG_DATA_PRODUCT = "lreg:api/data_product/"
    LREG_OBJECT = "lreg:api/object/"
    LREG_USER = "lreg:api/users/"
    FAIR_HASH = "fair:hash"
    FAIR_INPUT_DATA = "fair:input_data"
    FAIR_NAMESPACE = "fair:namespace"
    PROV_AGENT = "prov:agent"
    PROV_ACTIVITY = "prov:activity"
    PROV_AT_LOCATION = "prov:atLocation"
    PROV_ENTITY = "prov:entity"
    PROV_GENERAL_ENTITY = "prov:generalEntity"
    PROV_GENERATED_ENTITY = "prov:generatedEntity"
    PROV_PERSON = "prov:Person"
    PROV_SPECIFIC_ENTITY = "prov:specificEntity"
    PROV_ROLE = "prov:role"
    PROV_USED_ENTITY = "prov:usedEntity"
    XSD_QNAME = "xsd:QName"
    RDF_TYPE = "rdf:type"
    TEXT_FILE = "text file"
    XSD_DATE_TIME = "xsd:dateTime"

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_prov_db()

    def test_get_json(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        url = reverse("prov_report", kwargs={"pk": 2})
        response = client.get(url, format="json", HTTP_ACCEPT=self.APPLICATION_JSON)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], self.APPLICATION_JSON)

        results = response.json()

        expected_result = {
            self.RDF_TYPE: {"$": self.DCAT_DATASET, "type": self.XSD_QNAME},
            self.PROV_AT_LOCATION: "https://data.fairdatapipeline.org/api/text_file/input/1",
            self.FAIR_HASH: "5b6fafc594cdb619104ceeef7a4802f4086e90a1",
            self.DCTERMS_DESCRIPTION: "input 1 object",
            self.FAIR_NAMESPACE: "prov",
            self.DCTERMS_TITLE: "this/is/cr/test/input/1",
            self.DCAT_HAS_VERSION: "0.2.0",
        }
        prov_out = results["entity"][f"{self.LREG_DATA_PRODUCT}1"]
        del prov_out[self.DCTERMS_MODIFIED]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            self.RDF_TYPE: {"$": self.DCAT_DATASET, "type": self.XSD_QNAME},
            self.PROV_AT_LOCATION: "https://data.fairdatapipeline.org/api/text_file/output/1",
            self.FAIR_HASH: "5b6fafc594cdb619104ceeef7a4802f4086e90b1",
            self.DCTERMS_DESCRIPTION: "output 1 object",
            self.FAIR_NAMESPACE: "prov",
            self.DCTERMS_TITLE: "this/is/cr/test/output/1",
            self.DCAT_HAS_VERSION: "0.2.0",
        }
        prov_out = results["entity"][f"{self.LREG_DATA_PRODUCT}2"]
        del prov_out[self.DCTERMS_MODIFIED]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            self.RDF_TYPE: {"$": self.DCAT_DATASET, "type": self.XSD_QNAME},
            self.PROV_AT_LOCATION: "https://data.fairdatapipeline.org/api/text_file/input/2",
            self.FAIR_HASH: "5b6fafc594cdb619104ceeef7a4802f4086e90a2",
            self.DCTERMS_DESCRIPTION: "input 2 object",
            self.DCTERMS_FORMAT: self.TEXT_FILE,
            self.FAIR_NAMESPACE: "prov",
            self.DCTERMS_TITLE: "this/is/cr/test/input/2",
            self.DCAT_HAS_VERSION: "0.2.0",
        }
        prov_out = results["entity"][f"{self.LREG_DATA_PRODUCT}4"]
        del prov_out[self.DCTERMS_MODIFIED]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            self.RDF_TYPE: {"$": self.DCAT_DATASET, "type": self.XSD_QNAME},
            self.PROV_AT_LOCATION: "https://data.fairdatapipeline.org/api/text_file/input/3",
            self.FAIR_HASH: "5b6fafc594cdb619104ceeef7a4802f4086e90a3",
            self.DCTERMS_DESCRIPTION: "input 3 object",
            self.DCTERMS_FORMAT: self.TEXT_FILE,
            self.FAIR_NAMESPACE: "prov",
            self.DCTERMS_TITLE: "this/is/cr/test/input/3",
            self.DCAT_HAS_VERSION: "0.2.0",
        }
        prov_out = results["entity"][f"{self.LREG_DATA_PRODUCT}5"]
        del prov_out[self.DCTERMS_MODIFIED]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            self.RDF_TYPE: {"$": self.DCAT_DATASET, "type": self.XSD_QNAME},
            self.DCTERMS_TITLE: "this is cr test input 1",
            self.DCTERMS_ISSUED: {
                "$": "2020-07-10T18:38:00+00:00",
                "type": self.XSD_DATE_TIME,
            },
            self.PROV_AT_LOCATION: "https://example.org/file_strore/1.txt",
            self.DCAT_HAS_VERSION: "0.2.0",
            "fair:alternate_identifier": "this_is_cr_test_input_1",
            "fair:alternate_identifier_type": "text",
            self.DCTERMS_DESCRIPTION: "this is code run test input 1",
        }
        self.assertEqual(
            results["entity"]["lreg:api/external_object/1"], expected_result
        )

        expected_result = {
            self.RDF_TYPE: {"$": self.DCAT_DATASET, "type": self.XSD_QNAME},
            self.DCTERMS_TITLE: "this is cr test output 1",
            self.DCTERMS_ISSUED: {
                "$": "2021-07-10T18:38:00+00:00",
                "type": self.XSD_DATE_TIME,
            },
            self.PROV_AT_LOCATION: "https://example.org/file_strore/2.txt",
            self.DCAT_HAS_VERSION: "0.2.0",
            "fair:alternate_identifier": "this_is_cr_test_output_1",
            "fair:alternate_identifier_type": "text",
            self.DCTERMS_DESCRIPTION: "this is code run test output 1",
            self.DCTERMS_IDENTIFIER: "this_is_cr_test_output_1_id",
        }
        self.assertEqual(
            results["entity"]["lreg:api/external_object/2"], expected_result
        )

        expected_result = {
            self.PROV_AT_LOCATION: "https://github.com/ScottishCovidResponse/SCRCdata repository",
            self.DCTERMS_TITLE: "ScottishCovidResponse/SCRCdata",
            self.DCAT_HAS_VERSION: "0.1.0",
            "fair:commit": "b98782baaaea3bf6cc2882ad7d1c5de7aece362a",
            "fair:website": "https://github.com/ScottishCovidResponse/SCRCdata",
            self.RDF_TYPE: {
                "$": "dcmitype:Software",
                "type": self.XSD_QNAME,
            },
        }
        prov_out = results["entity"]["lreg:api/code_repo_release/1"]
        del prov_out[self.DCTERMS_MODIFIED]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            self.PROV_AT_LOCATION: "https://data.fairdatapipeline.org/api/text_file/15/?format=text",
            self.FAIR_HASH: "5b6fafc594cdb619104ceeef7a4802f4086e90e8",
        }
        prov_out = results["entity"][f"{self.LREG_OBJECT}3"]
        del prov_out[self.DCTERMS_MODIFIED]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            self.DCTERMS_FORMAT: self.TEXT_FILE,
            self.PROV_AT_LOCATION: "https://data.fairdatapipeline.org/api/text_file/16/?format=text",
            self.FAIR_HASH: "5b6fafc594cdb619104ceeef7a4802f4086e90e9",
            self.RDF_TYPE: {
                "$": "dcmitype:Software",
                "type": self.XSD_QNAME,
            },
        }
        prov_out = results["entity"][f"{self.LREG_OBJECT}4"]
        del prov_out[self.DCTERMS_MODIFIED]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            f"{self.LREG_CODE_RUN}1": {
                "prov:startTime": "2021-07-17T18:21:11+00:00",
                self.RDF_TYPE: {"$": "fair:Run", "type": self.XSD_QNAME},
                self.DCTERMS_DESCRIPTION: "Test run",
            }
        }
        self.assertEqual(results["activity"], expected_result)
        expected_result = {
            f"{self.LREG_AUTHOR}3": {
                self.RDF_TYPE: {
                    "$": self.PROV_PERSON,
                    "type": self.XSD_QNAME,
                },
                self.FOAF_NAME: "Rosanna Massabeti",
            },
            f"{self.LREG_USER}1": {
                self.RDF_TYPE: {
                    "$": self.PROV_PERSON,
                    "type": self.XSD_QNAME,
                },
                self.FOAF_NAME: "User Not Found",
            },
            f"{self.LREG_AUTHOR}1": {
                self.RDF_TYPE: {
                    "$": self.PROV_PERSON,
                    "type": self.XSD_QNAME,
                },
                self.FOAF_NAME: "Ivana Valenti",
            },
            f"{self.LREG_AUTHOR}2": {
                self.RDF_TYPE: {
                    "$": self.PROV_PERSON,
                    "type": self.XSD_QNAME,
                },
                self.FOAF_NAME: "Maria Cipriani",
            },
        }
        self.assertEqual(results["agent"], expected_result)

        expected_result = {
            "_:id2": {
                self.PROV_SPECIFIC_ENTITY: f"{self.LREG_DATA_PRODUCT}2",
                self.PROV_GENERAL_ENTITY: "lreg:api/external_object/2",
            },
            "_:id8": {
                self.PROV_SPECIFIC_ENTITY: f"{self.LREG_DATA_PRODUCT}1",
                self.PROV_GENERAL_ENTITY: "lreg:api/external_object/1",
            },
        }
        self.assertEqual(results["specializationOf"], expected_result)

        expected_result = {
            "_:id5": {
                self.PROV_ACTIVITY: f"{self.LREG_CODE_RUN}1",
                self.PROV_ENTITY: "lreg:api/code_repo_release/1",
                self.PROV_ROLE: {
                    "$": "fair:software",
                    "type": self.XSD_QNAME,
                },
            },
            "_:id6": {
                self.PROV_ACTIVITY: f"{self.LREG_CODE_RUN}1",
                self.PROV_ENTITY: f"{self.LREG_OBJECT}3",
                self.PROV_ROLE: {
                    "$": "fair:model_configuration",
                    "type": self.XSD_QNAME,
                },
            },
            "_:id7": {
                self.PROV_ACTIVITY: f"{self.LREG_CODE_RUN}1",
                self.PROV_ENTITY: f"{self.LREG_OBJECT}4",
                self.PROV_ROLE: {
                    "$": "fair:submission_script",
                    "type": self.XSD_QNAME,
                },
            },
            "_:id10": {
                self.PROV_ACTIVITY: f"{self.LREG_CODE_RUN}1",
                self.PROV_ENTITY: f"{self.LREG_DATA_PRODUCT}1",
                self.PROV_ROLE: {
                    "$": self.FAIR_INPUT_DATA,
                    "type": self.XSD_QNAME,
                },
            },
            "_:id13": {
                self.PROV_ACTIVITY: f"{self.LREG_CODE_RUN}1",
                self.PROV_ENTITY: f"{self.LREG_DATA_PRODUCT}4",
                self.PROV_ROLE: {
                    "$": self.FAIR_INPUT_DATA,
                    "type": self.XSD_QNAME,
                },
            },
            "_:id16": {
                self.PROV_ACTIVITY: f"{self.LREG_CODE_RUN}1",
                self.PROV_ENTITY: f"{self.LREG_DATA_PRODUCT}5",
                self.PROV_ROLE: {
                    "$": self.FAIR_INPUT_DATA,
                    "type": self.XSD_QNAME,
                },
            },
        }
        self.assertEqual(results["used"], expected_result)

        expected_result = {
            "_:id1": {
                self.PROV_ENTITY: f"{self.LREG_DATA_PRODUCT}2",
                self.PROV_AGENT: f"{self.LREG_AUTHOR}3",
                self.PROV_ROLE: {
                    "$": self.DCTERMS_CREATOR,
                    "type": self.XSD_QNAME,
                },
            },
            self.ID9: {
                self.PROV_ENTITY: f"{self.LREG_DATA_PRODUCT}1",
                self.PROV_AGENT: f"{self.LREG_AUTHOR}1",
                self.PROV_ROLE: {
                    "$": self.DCTERMS_CREATOR,
                    "type": self.XSD_QNAME,
                },
            },
            "_:id12": {
                self.PROV_ENTITY: f"{self.LREG_DATA_PRODUCT}4",
                self.PROV_AGENT: f"{self.LREG_AUTHOR}2",
                self.PROV_ROLE: {
                    "$": self.DCTERMS_CREATOR,
                    "type": self.XSD_QNAME,
                },
            },
            "_:id15": {
                self.PROV_ENTITY: f"{self.LREG_DATA_PRODUCT}5",
                self.PROV_AGENT: f"{self.LREG_AUTHOR}3",
                self.PROV_ROLE: {
                    "$": self.DCTERMS_CREATOR,
                    "type": self.XSD_QNAME,
                },
            },
        }
        self.assertEqual(results["wasAttributedTo"], expected_result)

        expected_result = {
            self.ID11: {
                self.PROV_GENERATED_ENTITY: f"{self.LREG_DATA_PRODUCT}2",
                self.PROV_USED_ENTITY: f"{self.LREG_DATA_PRODUCT}1",
            },
            "_:id14": {
                self.PROV_GENERATED_ENTITY: f"{self.LREG_DATA_PRODUCT}2",
                self.PROV_USED_ENTITY: f"{self.LREG_DATA_PRODUCT}4",
            },
            "_:id17": {
                self.PROV_GENERATED_ENTITY: f"{self.LREG_DATA_PRODUCT}2",
                self.PROV_USED_ENTITY: f"{self.LREG_DATA_PRODUCT}5",
            },
        }
        self.assertEqual(results["wasDerivedFrom"], expected_result)

        expected_result = {
            "_:id3": {
                self.PROV_ENTITY: f"{self.LREG_DATA_PRODUCT}2",
                self.PROV_ACTIVITY: f"{self.LREG_CODE_RUN}1",
            },
        }
        self.assertEqual(results["wasGeneratedBy"], expected_result)

        expected_result = {
            self.ID4: {
                self.PROV_ACTIVITY: f"{self.LREG_CODE_RUN}1",
                "prov:trigger": f"{self.LREG_USER}1",
                "prov:time": "2021-07-17T18:21:11+00:00",
                self.PROV_ROLE: {
                    "$": "fair:code_runner",
                    "type": self.XSD_QNAME,
                },
            }
        }
        self.assertEqual(results["wasStartedBy"], expected_result)

    def test_get_provn(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 1})
        response = client.get(
            url,
            format="provn",
            HTTP_ACCEPT="text/provenance-notation",
            HTTP_HOST="localhost",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], "text/provenance-notation; charset=utf8"
        )

        result_bits = response.data.split(self.DCTERMS_MODIFIED)
        result_end = result_bits[1].split("xsd:dateTime, ", 1)[1]
        result = result_bits[0] + result_end
        expected_result = """document
  prefix lreg <http://localhost/>
  prefix fair <https://data.fairdatapipeline.org/vocab/#>
  prefix dcat <http://www.w3.org/ns/dcat#>
  prefix dcmitype <http://purl.org/dc/dcmitype/>
  prefix dcterms <http://purl.org/dc/terms/>
  prefix foaf <http://xmlns.com/foaf/spec/#>
  prefix rdf <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
  
  entity(lreg:api/data_product/1, [rdf:type='dcat:Dataset', prov:atLocation="https://data.fairdatapipeline.org/api/text_file/input/1", fair:hash="5b6fafc594cdb619104ceeef7a4802f4086e90a1", dcterms:description="input 1 object", fair:namespace="prov", dcterms:title="this/is/cr/test/input/1", dcat:hasVersion="0.2.0"])
  agent(lreg:api/author/1, [rdf:type='prov:Person', foaf:name="Ivana Valenti"])
  wasAttributedTo(lreg:api/data_product/1, lreg:api/author/1, [prov:role='dcterms:creator'])
  entity(lreg:api/external_object/1, [rdf:type='dcat:Dataset', dcterms:title="this is cr test input 1", dcterms:issued="2020-07-10T18:38:00+00:00" %% xsd:dateTime, dcat:hasVersion="0.2.0", fair:alternate_identifier="this_is_cr_test_input_1", fair:alternate_identifier_type="text", dcterms:description="this is code run test input 1", prov:atLocation="https://example.org/file_strore/1.txt"])
  specializationOf(lreg:api/data_product/1, lreg:api/external_object/1)
endDocument"""
        self.assertEqual(result, expected_result)

    def test_get_json_ld(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 1})
        response = client.get(url, format="json-ld", HTTP_ACCEPT="application/ld+json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/ld+json; charset=utf8")

    def test_get_xml(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 1})
        response = client.get(url, format="xml", HTTP_ACCEPT="text/xml")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/xml; charset=utf8")

    def test_get_jpg(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 1})
        response = client.get(url, format="jpg", HTTP_ACCEPT="image/jpeg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/jpeg")

    def test_get_svg(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 1})
        response = client.get(url, format="svg", HTTP_ACCEPT="image/svg+xml")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")

    def test_get_no_repo(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 7})
        response = client.get(url, format="xml", HTTP_ACCEPT="text/xml")
        self.assertEqual(response["Content-Type"], "text/xml; charset=utf8")
        self.assertNotContains(response, "lreg:api/code_repo/", 200)
        self.assertNotContains(response, "lreg:api/code_repo_release/", 200)

    def test_get_no_repo_release(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 6})
        response = client.get(url, format="xml", HTTP_ACCEPT="text/xml")
        self.assertEqual(response["Content-Type"], "text/xml; charset=utf8")
        self.assertContains(response, f"{self.LREG_OBJECT}", status_code=200)

    def test_get_multi_run(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 9})
        response = client.get(
            url, data={"depth": 5}, format="json", HTTP_ACCEPT=self.APPLICATION_JSON
        )
        results = response.json()

        for dp in [
            f"{self.LREG_DATA_PRODUCT}1",
            f"{self.LREG_DATA_PRODUCT}6",
            f"{self.LREG_DATA_PRODUCT}7",
            f"{self.LREG_DATA_PRODUCT}8",
            f"{self.LREG_DATA_PRODUCT}9",
        ]:
            self.assertIn(dp, results["entity"].keys())

        for cr in [
            f"{self.LREG_CODE_RUN}2",
            f"{self.LREG_CODE_RUN}3",
            f"{self.LREG_CODE_RUN}4",
            f"{self.LREG_CODE_RUN}5",
        ]:
            self.assertIn(cr, results["activity"].keys())

        self.assertIn(
            results["used"][self.ID19][self.PROV_ACTIVITY], f"{self.LREG_CODE_RUN}2"
        )
        self.assertIn(
            results["used"][self.ID19][self.PROV_ENTITY], f"{self.LREG_DATA_PRODUCT}1"
        )

        self.assertIn(
            results["used"][self.ID24][self.PROV_ACTIVITY], f"{self.LREG_CODE_RUN}3"
        )
        self.assertIn(
            results["used"][self.ID24][self.PROV_ENTITY], f"{self.LREG_DATA_PRODUCT}1"
        )

        self._check_code_runs_present(results)

    def test_get_multi_run_limited(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 9})
        response = client.get(
            url, data={"depth": 2}, format="json", HTTP_ACCEPT=self.APPLICATION_JSON
        )
        results = response.json()

        for dp in [
            f"{self.LREG_DATA_PRODUCT}6",
            f"{self.LREG_DATA_PRODUCT}7",
            f"{self.LREG_DATA_PRODUCT}8",
            f"{self.LREG_DATA_PRODUCT}9",
        ]:
            self.assertIn(dp, results["entity"].keys())

        for dp in [f"{self.LREG_DATA_PRODUCT}1"]:
            self.assertNotIn(dp, results["entity"].keys())

        for cr in [f"{self.LREG_CODE_RUN}4", f"{self.LREG_CODE_RUN}5"]:
            self.assertIn(cr, results["activity"].keys())

        for cr in [f"{self.LREG_CODE_RUN}2", f"{self.LREG_CODE_RUN}3"]:
            self.assertNotIn(cr, results["activity"].keys())

        self.assertNotIn(self.ID19, results["used"].keys())
        self.assertNotIn(self.ID24, results["used"].keys())

        self._check_code_runs_present(results)

    def _check_code_runs_present(self, results):
        self.assertIn(
            results["used"][self.ID9][self.PROV_ACTIVITY], f"{self.LREG_CODE_RUN}4"
        )
        self.assertIn(
            results["used"][self.ID9][self.PROV_ENTITY], f"{self.LREG_DATA_PRODUCT}6"
        )

        self.assertIn(
            results["used"][self.ID11][self.PROV_ACTIVITY], f"{self.LREG_CODE_RUN}4"
        )
        self.assertIn(
            results["used"][self.ID11][self.PROV_ENTITY], f"{self.LREG_DATA_PRODUCT}7"
        )

        self.assertIn(
            results["used"][self.ID4][self.PROV_ACTIVITY], f"{self.LREG_CODE_RUN}5"
        )
        self.assertIn(
            results["used"][self.ID4][self.PROV_ENTITY], f"{self.LREG_DATA_PRODUCT}8"
        )


def run_final_from_another_commit():
    """
    Move the shared ancestry's final code run to a second commit of the same repo.

    @return the first commit, and the second

    """
    final = models.CodeRun.objects.get(description="final")
    location = final.code_repo.storage_location
    commit = "f" * 40
    final.code_repo = models.Object.objects.create(
        updated_by=final.updated_by,
        storage_location=models.StorageLocation.objects.create(
            updated_by=final.updated_by,
            path=location.path,
            hash=commit,
            storage_root=location.storage_root,
        ),
    )
    final.save()
    return location.hash, commit


class ProvSharedAncestryTests(TestCase):
    """
    The provenance report of a data product whose ancestry is shared: everything in
    it is reported once, however many routes lead to it.

    The expected content is written out from the fixture, so these tests also fail
    if something that belongs in the report is left out. The fixture has no code
    repo release and no component that is the output of two code runs, so they say
    nothing about those. `extra`, an output of `prepare` that nothing in `end`'s
    ancestry reads, is not in the report.
    """

    APPLICATION_JSON = "application/json"
    RUNS = ["final", "left", "pair", "prepare", "right"]

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_shared_ancestry_db(self)

    def _data_product(self, name):
        return f"lreg:api/data_product/{models.DataProduct.objects.get(name=name).id}"

    def _code_run(self, description):
        code_run = models.CodeRun.objects.get(description=description)
        return f"lreg:api/code_run/{code_run.id}"

    def _object(self, path):
        return f"lreg:api/object/{models.Object.objects.get(storage_location__path=path).id}"

    def _get(self, depth):
        client = APIClient()
        client.force_authenticate(user=self.user)
        end = models.DataProduct.objects.get(name="end")
        url = reverse("prov_report", kwargs={"pk": end.id})
        response = client.get(
            url, data={"depth": depth}, format="json", HTTP_ACCEPT=self.APPLICATION_JSON
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _pairs(self, results, relation, first, second):
        # sorted lists, not sets, so that a repeated relation fails the comparison
        return sorted((r[first], r[second]) for r in results[relation].values())

    def test_supplementary_source(self):
        # a data product requested or derived from its source was derived from it,
        # where one that is the identified item is a specialisation of it
        extra = models.DataProduct.objects.get(name="extra")
        extract = models.ExternalObject.objects.get(title="An extract of the deposit")
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": extra.id})
        response = client.get(url, format="json", HTTP_ACCEPT=self.APPLICATION_JSON)
        self.assertEqual(response.status_code, 200)
        results = response.json()

        source = f"lreg:api/external_object/{extract.id}"
        dp = self._data_product
        self.assertEqual(results["entity"][source]["dcterms:title"], "An extract of the deposit")
        # derived from its source as well as from what the run that wrote it read
        self.assertEqual(
            self._pairs(results, "wasDerivedFrom", "prov:generatedEntity", "prov:usedEntity"),
            sorted([(dp("extra"), source), (dp("extra"), dp("source")), (dp("extra"), dp("deposit"))]),
        )
        specialised = self._pairs(
            results, "specializationOf", "prov:specificEntity", "prov:generalEntity"
        )
        self.assertNotIn(dp("extra"), [specific for specific, _ in specialised])

    def test_whole_ancestry(self):
        results = self._get(100)
        dp = self._data_product
        cr = self._code_run
        user = f"lreg:api/users/{self.user.id}"
        author = f"lreg:api/author/{models.Author.objects.get(name='Ivana Valenti').id}"
        organisation = models.Author.objects.get(identifier__contains="ror.org")
        organisation = f"lreg:api/author/{organisation.id}"
        script = self._object("script")
        repo = self._object("FAIRDataPipeline/shared")
        model_config = self._object("model_config")

        # an identifier described more than once has a list of descriptions
        for kind in ("entity", "activity", "agent"):
            for identifier, description in results[kind].items():
                self.assertIsInstance(description, dict, identifier)

        names = ["end", "first", "second", "twin", "raw", "alias", "left", "right"]
        names += ["source", "source-copy", "deposit"]
        source_row = models.ExternalObject.objects.get(title="The source data")
        deposit_row = models.ExternalObject.objects.get(title="The deposit")
        sources = {f"lreg:api/external_object/{row.id}" for row in (source_row, deposit_row)}
        self.assertEqual(
            set(results["entity"]),
            {script, repo, model_config, *sources, *(dp(name) for name in names)},
        )
        # source and source-copy were registered from one source row, described once
        self.assertEqual(
            self._pairs(results, "specializationOf", "prov:specificEntity", "prov:generalEntity"),
            sorted(
                [
                    (dp("source"), f"lreg:api/external_object/{source_row.id}"),
                    (dp("source-copy"), f"lreg:api/external_object/{source_row.id}"),
                    (dp("deposit"), f"lreg:api/external_object/{deposit_row.id}"),
                ]
            ),
        )
        self.assertEqual(set(results["activity"]), {cr(run) for run in self.RUNS})
        self.assertEqual(set(results["agent"]), {user, author, organisation})

        self.assertEqual(
            self._pairs(results, "wasGeneratedBy", "prov:entity", "prov:activity"),
            sorted(
                [
                    (dp("end"), cr("final")),
                    (dp("first"), cr("pair")),
                    (dp("second"), cr("pair")),
                    (dp("twin"), cr("pair")),
                    (dp("raw"), cr("prepare")),
                    (dp("alias"), cr("prepare")),
                    (dp("left"), cr("left")),
                    (dp("right"), cr("right")),
                ]
            ),
        )
        # a run that reads raw's object reads both of its names, raw and alias; the
        # fetch run prepare reads the deposit, which has no file
        self.assertEqual(
            self._pairs(results, "used", "prov:activity", "prov:entity"),
            sorted(
                [
                    (cr("final"), dp("first")),
                    (cr("final"), dp("second")),
                    (cr("final"), dp("twin")),
                    (cr("final"), dp("raw")),
                    (cr("final"), dp("alias")),
                    (cr("final"), dp("source-copy")),
                    (cr("pair"), dp("left")),
                    (cr("pair"), dp("right")),
                    (cr("prepare"), dp("source")),
                    (cr("prepare"), dp("deposit")),
                    (cr("left"), dp("raw")),
                    (cr("left"), dp("alias")),
                    (cr("right"), dp("raw")),
                    (cr("right"), dp("alias")),
                    *((cr(run), script) for run in self.RUNS),
                    *((cr(run), repo) for run in self.RUNS),
                    *((cr(run), model_config) for run in ("prepare", "left", "right")),
                ]
            ),
        )
        self.assertEqual(
            self._pairs(
                results, "wasDerivedFrom", "prov:generatedEntity", "prov:usedEntity"
            ),
            sorted(
                [
                    (dp("end"), dp("first")),
                    (dp("end"), dp("second")),
                    (dp("end"), dp("twin")),
                    (dp("end"), dp("raw")),
                    (dp("end"), dp("alias")),
                    (dp("end"), dp("source-copy")),
                    (dp("first"), dp("left")),
                    (dp("first"), dp("right")),
                    (dp("second"), dp("left")),
                    (dp("second"), dp("right")),
                    (dp("twin"), dp("left")),
                    (dp("twin"), dp("right")),
                    (dp("raw"), dp("source")),
                    (dp("raw"), dp("deposit")),
                    (dp("alias"), dp("source")),
                    (dp("alias"), dp("deposit")),
                    (dp("left"), dp("raw")),
                    (dp("left"), dp("alias")),
                    (dp("right"), dp("raw")),
                    (dp("right"), dp("alias")),
                ]
            ),
        )
        self.assertEqual(
            self._pairs(results, "wasStartedBy", "prov:activity", "prov:trigger"),
            sorted((cr(run), user) for run in self.RUNS),
        )
        self.assertEqual(
            self._pairs(results, "wasAttributedTo", "prov:entity", "prov:agent"),
            sorted(
                [
                    *((entity, author) for entity in (script, repo, model_config)),
                    (dp("source"), organisation),
                ]
            ),
        )

    def test_organisation_author(self):
        # an author identified by a ROR id is an organisation, the others people
        results = self._get(100)
        organisation = models.Author.objects.get(identifier__contains="ror.org")
        person = models.Author.objects.get(name="Ivana Valenti")
        qname = {"type": "xsd:QName"}
        self.assertEqual(
            results["agent"][f"lreg:api/author/{organisation.id}"]["rdf:type"],
            {"$": "prov:Organization", **qname},
        )
        self.assertEqual(
            results["agent"][f"lreg:api/author/{person.id}"]["rdf:type"],
            {"$": "prov:Person", **qname},
        )

    def test_depth(self):
        cr = self._code_run

        self.assertEqual(set(self._get(1)["activity"]), {cr("final")})
        # raw is an input of the final run, so the run that made it is at depth 2
        self.assertEqual(
            set(self._get(2)["activity"]), {cr("final"), cr("pair"), cr("prepare")}
        )
        whole_ancestry = self._get(3)
        self.assertEqual(
            set(whole_ancestry["activity"]), {cr(run) for run in self.RUNS}
        )
        # raw is reached again at depth 4, through left and right
        self.assertEqual(self._get(4), whole_ancestry)
        self.assertEqual(self._get(100), whole_ancestry)

    def test_no_record_is_repeated(self):
        end = models.DataProduct.objects.get(name="end")
        request = RequestFactory().get("/")

        for depth in (1, 2, 3, 4, 100):
            doc = prov.generate_prov_document(end, depth, request)
            records = doc.get_records()
            self.assertEqual(len(records), len(set(records)), f"depth {depth}")

    def test_commit(self):
        first_commit, second_commit = run_final_from_another_commit()
        final = models.CodeRun.objects.get(description="final")
        pair = models.CodeRun.objects.get(description="pair")
        results = self._get(100)
        repo = f"lreg:api/object/{pair.code_repo.id}"
        second_repo = f"lreg:api/object/{final.code_repo.id}"

        self.assertEqual(results["entity"][repo]["fair:commit"], first_commit)
        self.assertEqual(results["entity"][second_repo]["fair:commit"], second_commit)
        used = self._pairs(results, "used", "prov:activity", "prov:entity")
        self.assertIn((self._code_run("final"), second_repo), used)
        self.assertNotIn((self._code_run("final"), repo), used)
        self.assertIn((self._code_run("pair"), repo), used)
        # only a repo has a commit
        for identifier, description in results["entity"].items():
            if identifier not in (repo, second_repo):
                self.assertNotIn("fair:commit", description, identifier)

    def test_hash(self):
        # every file carries its hash as a field; the repo's is its commit
        results = self._get(100)
        names = ["end", "first", "second", "twin", "raw", "alias", "left", "right"]
        for name in (*names, "source"):
            location = models.DataProduct.objects.get(name=name).object.storage_location
            entity = results["entity"][self._data_product(name)]
            self.assertEqual(entity["fair:hash"], location.hash, name)
        for path in ("script", "model_config"):
            location = models.Object.objects.get(storage_location__path=path)
            entity = results["entity"][self._object(path)]
            self.assertEqual(entity["fair:hash"], location.storage_location.hash, path)
        repo = results["entity"][self._object("FAIRDataPipeline/shared")]
        self.assertNotIn("fair:hash", repo)
        self.assertIn("fair:commit", repo)

    def test_names_paired(self):
        # an object with two names is two entities, each with its own name alone
        results = self._get(100)
        for name in ("raw", "alias"):
            entity = results["entity"][self._data_product(name)]
            self.assertEqual(entity["dcterms:title"], name)
            self.assertEqual(entity["dcat:hasVersion"], "1.0.0")
            self.assertEqual(entity["fair:namespace"], "shared")

    def test_object_with_two_roles(self):
        # an object that is the model config of one code run and the submission
        # script of another is described as each, because the descriptions differ
        script = models.Object.objects.get(storage_location__path="script")
        final = models.CodeRun.objects.get(description="final")
        final.model_config = script
        final.save()

        results = self._get(100)
        descriptions = results["entity"][self._object("script")]

        self.assertEqual(len(descriptions), 2)
        self.assertEqual(
            sorted("rdf:type" in description for description in descriptions),
            [False, True],
        )
        # its author is attributed to the object, not to each description of it
        attributed = self._pairs(
            results, "wasAttributedTo", "prov:entity", "prov:agent"
        )
        self.assertEqual(len(attributed), len(set(attributed)))


class RoCrateAPITest(TestCase):

    APPLICATION_JSON_LD = "application/ld+json"
    CHARSET_UTF8 = "charset=utf8"

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_prov_db()

    def test_get_json_ld_cr(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("code_run_ro_crate", kwargs={"pk": 1})
        response = client.get(
            url, format="json-ld", HTTP_ACCEPT=self.APPLICATION_JSON_LD
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], f"{self.APPLICATION_JSON_LD}; {self.CHARSET_UTF8}"
        )

    def test_get_json_ld_cr2(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("code_run_ro_crate", kwargs={"pk": 6})
        response = client.get(
            url, format="json-ld", HTTP_ACCEPT=self.APPLICATION_JSON_LD
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], f"{self.APPLICATION_JSON_LD}; {self.CHARSET_UTF8}"
        )

    def test_get_json_ld_cr_with_depth(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("code_run_ro_crate", kwargs={"pk": 6})
        response = client.get(
            url,
            data={"depth": 5},
            format="json-ld",
            HTTP_ACCEPT=self.APPLICATION_JSON_LD,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], f"{self.APPLICATION_JSON_LD}; {self.CHARSET_UTF8}"
        )

    def test_get_zip_cr(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("code_run_ro_crate", kwargs={"pk": 1})
        response = client.get(url, format="zip", HTTP_ACCEPT="application/zip")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")

    def test_get_json_ld_dp(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("data_product_ro_crate", kwargs={"pk": 2})
        response = client.get(
            url, format="json-ld", HTTP_ACCEPT=self.APPLICATION_JSON_LD
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], f"{self.APPLICATION_JSON_LD}; {self.CHARSET_UTF8}"
        )

    def test_get_json_ld_dp_with_depth(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("data_product_ro_crate", kwargs={"pk": 2})
        response = client.get(
            url,
            data={"depth": 5},
            format="json-ld",
            HTTP_ACCEPT=self.APPLICATION_JSON_LD,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], f"{self.APPLICATION_JSON_LD}; {self.CHARSET_UTF8}"
        )


class RoCrateSharedAncestryTests(TestCase):
    """
    The RO Crate of a data product or code run whose ancestry is shared: each data
    product is walked once, and the crate still holds every code run.

    Only the code runs are looked for in the crate; the rest of its content is not
    checked here.
    """

    APPLICATION_JSON_LD = "application/ld+json"

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_shared_ancestry_db(self)

    def _get(self, view, pk, depth, level=None):
        """Return the crate, and the names of the data products walked to make it."""
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse(view, kwargs={"pk": pk})
        data = {"depth": depth} if level is None else {"depth": depth, "level": level}
        with mock.patch.object(
            rocrate,
            "_generate_ro_crate_from_dp",
            wraps=rocrate._generate_ro_crate_from_dp,
        ) as walk:
            response = client.get(
                url,
                data=data,
                format="json-ld",
                HTTP_ACCEPT=self.APPLICATION_JSON_LD,
            )
        self.assertEqual(response.status_code, 200)
        walked = sorted(call.args[0].name for call in walk.call_args_list)
        return response.json(), walked

    def _code_runs(self, crate):
        return {
            entity["@id"]
            for entity in crate["@graph"]
            if entity["@type"] == "CreateAction"
        }

    def _ids(self, *descriptions):
        code_runs = models.CodeRun.objects.filter(description__in=descriptions)
        return {f"urn:uuid:{code_run.uuid}" for code_run in code_runs}

    def test_data_product(self):
        end = models.DataProduct.objects.get(name="end")
        # extra, prepare's other output, is in nobody's ancestry and is never walked
        names = ["alias", "deposit", "end", "first", "left", "raw", "right", "second"]
        names += ["source", "source-copy", "twin"]

        crate, walked = self._get("data_product_ro_crate", end.id, 100)
        self.assertEqual(walked, names)
        self.assertEqual(
            self._code_runs(crate),
            self._ids("final", "pair", "prepare", "left", "right"),
        )

        crate, walked = self._get("data_product_ro_crate", end.id, 2)
        self.assertEqual(
            walked, ["alias", "end", "first", "raw", "second", "source-copy", "twin"]
        )
        self.assertEqual(self._code_runs(crate), self._ids("final", "pair", "prepare"))

    def test_commit(self):
        first_commit, second_commit = run_final_from_another_commit()
        end = models.DataProduct.objects.get(name="end")
        url = "https://github.com/FAIRDataPipeline/shared"

        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}

        # the repo at each commit is an entity of its own
        software = {
            identifier: entity
            for identifier, entity in graph.items()
            if entity["@type"] == "SoftwareApplication"
        }
        self.assertEqual(
            set(software), {f"{url}#{first_commit}", f"{url}#{second_commit}"}
        )
        # with no release the commit stands as the version; the id carries it anyway
        for commit in (first_commit, second_commit):
            self.assertEqual(software[f"{url}#{commit}"]["version"], commit)
            self.assertNotIn("softwareVersion", software[f"{url}#{commit}"])
            self.assertEqual(software[f"{url}#{commit}"]["url"], url)
            self.assertEqual(
                software[f"{url}#{commit}"]["name"], "FAIRDataPipeline/shared"
            )

        # and each code run points at the commit it was run from
        instruments = {
            code_run.description: graph[f"urn:uuid:{code_run.uuid}"]["instrument"][
                "@id"
            ]
            for code_run in models.CodeRun.objects.all()
        }
        self.assertEqual(instruments.pop("final"), f"{url}#{second_commit}")
        self.assertEqual(set(instruments.values()), {f"{url}#{first_commit}"})

    def test_data_product_identity(self):
        # give one data product a version and a namespace of its own
        raw = models.DataProduct.objects.get(name="raw")
        raw.version = "2.3.4"
        raw.namespace = models.Namespace.objects.create(
            updated_by=self.user, name="other / one"
        )
        raw.save()
        end = models.DataProduct.objects.get(name="end")

        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}

        vocab = "https://data.fairdatapipeline.org/vocab/#"
        self.assertEqual(crate["@context"][1]["namespace"], f"{vocab}namespace")
        self.assertEqual(crate["@context"][1]["Namespace"], f"{vocab}Namespace")

        # a namespace is identified by its name, whichever registry it is in
        shared_id = "#namespace-shared"
        other_id = "#namespace-other%20%2F%20one"
        self.assertEqual(
            graph[shared_id],
            {
                "@id": shared_id,
                "@type": "Namespace",
                "name": "shared",
                "alternateName": "Shared Ancestry",
                "url": "https://example.org/shared",
            },
        )
        # a namespace need not have a full name or a website
        self.assertEqual(
            graph[other_id],
            {"@id": other_id, "@type": "Namespace", "name": "other / one"},
        )

        # the files with a hash are the data products; the external source has none
        identities = {
            entity["name"]: (entity["version"], entity["namespace"]["@id"])
            for entity in graph.values()
            if entity["@type"] == "File" and "sha1" in entity
        }
        # alias is a data product of its own on raw's object, so it keeps its own
        # version and namespace
        names = ("end", "first", "second", "twin", "left", "right", "alias", "source")
        expected = {name: ("1.0.0", shared_id) for name in (*names, "extra")}
        expected["raw"] = ("2.3.4", other_id)
        expected["source-copy"] = ("1.0.0", "#namespace-other")
        self.assertEqual(identities, expected)

        # the config and the script are files, but not data products
        software = [
            entity
            for entity in graph.values()
            if entity["@type"] == ["File", "SoftwareSourceCode"]
        ]
        self.assertEqual(len(software), 2)
        for entity in software:
            self.assertNotIn("version", entity)
            self.assertNotIn("namespace", entity)

    def test_file_paths(self):
        # a data product's file is at its namespace, name and version, whether or
        # not it is packed: identical bytes under two data products are two files
        # with one hash, and two names for one object two files with one identifier
        end = models.DataProduct.objects.get(name="end")
        raw = models.DataProduct.objects.get(name="raw")
        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        files = {
            identifier: entity
            for identifier, entity in graph.items()
            if entity["@type"] == "File" and identifier.startswith("shared/")
        }

        names = ["alias", "deposit", "end", "extra", "first", "left", "raw", "right"]
        names += ["second", "source", "twin"]
        self.assertEqual(set(files), {f"shared/{name}/1.0.0.txt" for name in names})
        self.assertNotIn("sha1", files["shared/deposit/1.0.0.txt"])
        second, twin = files["shared/second/1.0.0.txt"], files["shared/twin/1.0.0.txt"]
        self.assertEqual(twin["sha1"], second["sha1"])
        self.assertNotEqual(twin["identifier"], second["identifier"])
        self.assertEqual(
            files["shared/alias/1.0.0.txt"]["identifier"], str(raw.object.uuid)
        )
        self.assertEqual(
            files["shared/raw/1.0.0.txt"]["identifier"], str(raw.object.uuid)
        )
        self.assertEqual(
            files["shared/raw/1.0.0.txt"]["encodingFormat"], "text/plain"
        )

        software = {
            identifier
            for identifier, entity in graph.items()
            if entity["@type"] == ["File", "SoftwareSourceCode"]
        }
        self.assertEqual(
            software, {"model_config/model_config", "submission_script/script"}
        )
        # a file is neither an input nor an output: at any depth above one it is both
        self.assertFalse(
            [i for i in graph if i.startswith(("inputs/", "outputs/"))]
        )

    def test_files_listed_once(self):
        # a run that writes or reads several components of first lists it once
        pair = models.CodeRun.objects.get(description="pair")
        final = models.CodeRun.objects.get(description="final")

        crate, _ = self._get("code_run_ro_crate", pair.id, 1)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        results = [ref["@id"] for ref in graph[f"urn:uuid:{pair.uuid}"]["result"]]
        self.assertEqual(
            sorted(results),
            [f"shared/{name}/1.0.0.txt" for name in ("first", "second", "twin")],
        )
        # and its root lists first's licence and second's once each
        first = models.Object.objects.get(storage_location__path="first")
        cc_by = "https://creativecommons.org/licenses/by/4.0/"
        self.assertEqual(
            {ref["@id"] for ref in graph["./"]["license"]},
            {f"#licence-{first.uuid}", cc_by},
        )

        crate, _ = self._get("code_run_ro_crate", final.id, 1)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        objects = [ref["@id"] for ref in graph[f"urn:uuid:{final.uuid}"]["object"]]
        self.assertEqual(objects.count("shared/first/1.0.0.txt"), 1)

    def test_object_without_storage_location(self):
        # a data product whose object has no file is recorded, with nothing to pack
        raw = models.DataProduct.objects.get(name="raw")
        models.Object.objects.filter(pk=raw.object.pk).update(storage_location=None)
        end = models.DataProduct.objects.get(name="end")

        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        for name in ("raw", "alias"):
            self.assertIn(f"shared/{name}/1.0.0.txt", graph)
            self.assertNotIn("sha1", graph[f"shared/{name}/1.0.0.txt"])
        self.assertIn("sha1", graph["shared/end/1.0.0.txt"])

    def test_file_paths_without_a_file_type(self):
        # an object may have no file type; its path then has no extension
        raw = models.DataProduct.objects.get(name="raw")
        # not save(), which would try to create the object's whole_object again
        models.Object.objects.filter(pk=raw.object.pk).update(file_type=None)
        end = models.DataProduct.objects.get(name="end")

        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        self.assertIn("shared/raw/1.0.0", graph)
        self.assertNotIn("encodingFormat", graph["shared/raw/1.0.0"])
        self.assertIn("shared/alias/1.0.0", graph)

    def test_zip(self):
        # the zip holds each public file at its path, identical bytes twice over
        end = models.DataProduct.objects.get(name="end")
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("data_product_ro_crate", kwargs={"pk": end.id})
        response = client.get(
            url, data={"depth": 100}, format="zip", HTTP_ACCEPT="application/zip"
        )
        self.assertEqual(response.status_code, 200)

        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            names = set(archive.namelist())
            self.assertEqual(archive.read("shared/raw/1.0.0.txt"), b"raw\n")
            self.assertEqual(archive.read("shared/twin/1.0.0.txt"), b"second\n")
            self.assertEqual(archive.read("shared/second/1.0.0.txt"), b"second\n")
            self.assertEqual(
                archive.read("model_config/model_config"), b"model_config\n"
            )
            self.assertEqual(archive.read("submission_script/script"), b"script\n")
        products = ["alias", "end", "first", "left", "raw", "right", "second", "twin"]
        expected = {f"shared/{name}/1.0.0.txt" for name in products}
        self.assertTrue(expected <= names, names)
        # extra is outside end's provenance: described, not packaged; and at level
        # 3, a zip's default, source's primary source stands for its bytes
        self.assertNotIn("shared/extra/1.0.0.txt", names)
        self.assertNotIn("shared/source/1.0.0.txt", names)

    def _zip_names(self, level):
        """The paths a zip of end's crate holds at a level."""
        end = models.DataProduct.objects.get(name="end")
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("data_product_ro_crate", kwargs={"pk": end.id})
        response = client.get(
            url,
            data={"depth": 100, "level": level},
            format="zip",
            HTTP_ACCEPT="application/zip",
        )
        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            return set(archive.namelist())

    def test_zip_levels(self):
        # every level packs the config and script; level 3 adds the public files
        # that no primary source stands for, and level 4 those too
        level_1 = self._zip_names(1)
        self.assertTrue(
            {"model_config/model_config", "submission_script/script"} <= level_1
        )
        self.assertFalse([name for name in level_1 if name.startswith("shared/")])
        self.assertEqual(self._zip_names(2), level_1)

        level_3 = self._zip_names(3)
        self.assertIn("shared/raw/1.0.0.txt", level_3)
        self.assertNotIn("shared/source/1.0.0.txt", level_3)
        self.assertNotIn("shared/extra/1.0.0.txt", level_3)
        self.assertEqual(
            self._zip_names(4) - level_3,
            {"shared/source/1.0.0.txt", "other/source-copy/1.0.0.txt"},
        )
        self.assertNotIn("shared/deposit/1.0.0.txt", self._zip_names(4))

    def test_levels(self):
        # level 1, the JSON-LD default, gives no address; level 2 gives every public
        # file in the crate's provenance the address of the registry's copy
        end = models.DataProduct.objects.get(name="end")
        raw = models.DataProduct.objects.get(name="raw")
        source = models.ExternalObject.objects.get(title="The source data")

        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        addressed = [i for i, e in graph.items() if "contentUrl" in e]
        # the source's own address, where the registry fetched it from, is metadata
        # about the source and travels at every level
        self.assertEqual(addressed, ["#source-https%3A%2F%2Fdoi.org%2F10.5281%2Fzenodo.1234567%3AThe%20source%20data%401.0.0"])
        self.assertEqual(
            graph["#source-https%3A%2F%2Fdoi.org%2F10.5281%2Fzenodo.1234567%3AThe%20source%20data%401.0.0"]["contentUrl"],
            "https://example.org/downloads/source.txt",
        )

        crate, _ = self._get("data_product_ro_crate", end.id, 100, level=2)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        self.assertEqual(
            graph["shared/raw/1.0.0.txt"]["contentUrl"],
            str(raw.object.storage_location),
        )
        self.assertTrue(
            graph["shared/raw/1.0.0.txt"]["contentUrl"].startswith("file://")
        )
        self.assertIn("contentUrl", graph["submission_script/script"])
        self.assertIn("contentUrl", graph["shared/source/1.0.0.txt"])
        self.assertNotIn("contentUrl", graph["shared/extra/1.0.0.txt"])

    def test_bad_level(self):
        end = models.DataProduct.objects.get(name="end")
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("data_product_ro_crate", kwargs={"pk": end.id})
        for level in (0, 5, "three"):
            response = client.get(
                url,
                data={"level": level},
                format="json-ld",
                HTTP_ACCEPT=self.APPLICATION_JSON_LD,
            )
            self.assertEqual(response.status_code, 400, level)

    def test_conformance(self):
        # the crate declares Process Run Crate, and every run has an instrument
        end = models.DataProduct.objects.get(name="end")
        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        profile = "https://w3id.org/ro/wfrun/process/0.6"
        self.assertEqual(graph["./"]["conformsTo"], {"@id": profile})
        self.assertEqual(graph[profile]["@type"], "CreativeWork")
        runs = [
            entity
            for entity in graph.values()
            if entity.get("@type") == "CreateAction" and "identifier" in entity
        ]
        self.assertEqual(len(runs), 5)
        for run in runs:
            self.assertIn("instrument", run)

    def test_software_roles(self):
        # the run says which of its objects is the config and which the script
        prepare = models.CodeRun.objects.get(description="prepare")
        final = models.CodeRun.objects.get(description="final")
        end = models.DataProduct.objects.get(name="end")
        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        vocab = "https://data.fairdatapipeline.org/vocab/#"
        for term in ("model_configuration", "submission_script"):
            self.assertEqual(crate["@context"][1][term], f"{vocab}{term}")

        run = graph[f"urn:uuid:{prepare.uuid}"]
        self.assertEqual(
            run["model_configuration"], {"@id": "model_config/model_config"}
        )
        self.assertEqual(run["submission_script"], {"@id": "submission_script/script"})
        objects = [ref["@id"] for ref in run["object"]]
        self.assertIn("model_config/model_config", objects)
        self.assertIn("submission_script/script", objects)

        run = graph[f"urn:uuid:{final.uuid}"]
        self.assertNotIn("model_configuration", run)
        self.assertEqual(run["submission_script"], {"@id": "submission_script/script"})

    def test_run_without_repo(self):
        # a run with no repo has its submission script as its instrument
        final = models.CodeRun.objects.get(description="final")
        final.code_repo = None
        final.save()

        crate, _ = self._get("code_run_ro_crate", final.id, 1)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        self.assertEqual(
            graph[f"urn:uuid:{final.uuid}"]["instrument"],
            {"@id": "submission_script/script"},
        )

    def test_registered_input(self):
        # a data product registered from an external source is a file like any
        # other, the same as the source it was registered from, which the run did
        # not read directly
        end = models.DataProduct.objects.get(name="end")
        prepare = models.CodeRun.objects.get(description="prepare")
        source = models.ExternalObject.objects.get(title="The source data")
        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}

        product = graph["shared/source/1.0.0.txt"]
        self.assertIn("sha1", product)
        # the source is named by its identity in the registry, since one identifier
        # may have several files under it, each with its own title; the DOI is a
        # property of it
        self.assertEqual(product["sameAs"], {"@id": "#source-https%3A%2F%2Fdoi.org%2F10.5281%2Fzenodo.1234567%3AThe%20source%20data%401.0.0"})
        described = graph["#source-https%3A%2F%2Fdoi.org%2F10.5281%2Fzenodo.1234567%3AThe%20source%20data%401.0.0"]
        self.assertEqual(described["@type"], "Dataset")
        self.assertEqual(described["identifier"], source.identifier)
        self.assertEqual(described["name"], "The source data")
        self.assertEqual(described["version"], "1.0.0")
        self.assertNotIn("isPartOf", described)
        # every date in the crate is ISO 8601, with a T
        self.assertEqual(described["datePublished"], "2020-07-10T18:38:00+00:00")
        self.assertEqual(described["alternate_identifier"], "source-2020")
        self.assertEqual(described["alternate_identifier_type"], "project name")
        vocab = "https://data.fairdatapipeline.org/vocab/#"
        self.assertEqual(
            crate["@context"][1]["alternate_identifier"], f"{vocab}alternate_identifier"
        )
        objects = [ref["@id"] for ref in graph[f"urn:uuid:{prepare.uuid}"]["object"]]
        self.assertIn("shared/source/1.0.0.txt", objects)
        self.assertNotIn(source.identifier, objects)

    def test_all_outputs_listed(self):
        # a data product's crate lists every output of each run; one outside the
        # crate's provenance is described, with its hash, but not packaged (test_zip)
        end = models.DataProduct.objects.get(name="end")
        prepare = models.CodeRun.objects.get(description="prepare")
        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}

        results = [ref["@id"] for ref in graph[f"urn:uuid:{prepare.uuid}"]["result"]]
        self.assertEqual(
            sorted(results),
            [f"shared/{name}/1.0.0.txt" for name in ("alias", "extra", "raw")],
        )
        extra = graph["shared/extra/1.0.0.txt"]
        self.assertEqual(extra["name"], "extra")
        self.assertEqual(extra["version"], "1.0.0")
        self.assertEqual(extra["namespace"], {"@id": "#namespace-shared"})
        self.assertIn("sha1", extra)

    def test_identities(self):
        # nothing is identified by its row in this registry: an author without an
        # identifier by uuid, a user by a local id, a licence given as text by the
        # file it applies to
        end = models.DataProduct.objects.get(name="end")
        author = models.Author.objects.get(name="Ivana Valenti")
        first = models.Object.objects.get(storage_location__path="first")
        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}

        person = graph[f"urn:uuid:{author.uuid}"]
        self.assertEqual(person["@type"], "Person")
        self.assertEqual(person["name"], "Ivana Valenti")
        self.assertEqual(person["identifier"], str(author.uuid))
        self.assertEqual(
            graph["submission_script/script"]["author"],
            [{"@id": f"urn:uuid:{author.uuid}"}],
        )

        runs = [e for e in graph.values() if "identifier" in e and "agent" in e]
        self.assertEqual(len(runs), 5)
        for run in runs:
            self.assertEqual(run["agent"], {"@id": "#user-Test%20User"})
        self.assertEqual(graph["#user-Test%20User"]["name"], "User Not Found")

        licence = graph[f"#licence-{first.uuid}"]
        self.assertEqual(licence["name"], "For project use only")
        self.assertNotIn("identifier", licence)
        self.assertEqual(
            graph["shared/first/1.0.0.txt"]["license"],
            {"@id": f"#licence-{first.uuid}"},
        )
        cc_by = "https://creativecommons.org/licenses/by/4.0/"
        self.assertEqual(graph[cc_by]["identifier"], cc_by)
        self.assertEqual(graph[cc_by]["name"], "Creative Commons Attribution 4.0")

        rows = ("api/author/", "api/users/", "api/license/", "api/external_object/")
        for row in rows:
            self.assertNotIn(row, str(crate))

    def test_organisation_author(self):
        # an author identified by a ROR id is an organisation, the others people
        end = models.DataProduct.objects.get(name="end")
        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        organisation = graph["https://ror.org/00vtgdb53"]
        self.assertEqual(organisation["@type"], "Organization")
        self.assertEqual(organisation["name"], "University of Glasgow")
        self.assertEqual(
            graph["shared/source/1.0.0.txt"]["author"],
            [{"@id": "https://ror.org/00vtgdb53"}],
        )
        person = models.Author.objects.get(name="Ivana Valenti")
        self.assertEqual(graph[f"urn:uuid:{person.uuid}"]["@type"], "Person")

    def test_supplementary_source(self):
        # a file requested or derived from a source, which no identifier yields again,
        # is based on it; the run that wrote it is the step between them, and the
        # source of a file under a deposit's identifier is part of the deposit
        deposit_row = models.ExternalObject.objects.get(title="The deposit")
        end = models.DataProduct.objects.get(name="end")
        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}

        extract_id = (
            "#source-https%3A%2F%2Fdoi.org%2F10.5281%2Fzenodo.7654321"
            "%3AAn%20extract%20of%20the%20deposit%401.0.0"
        )
        extra = graph["shared/extra/1.0.0.txt"]
        self.assertEqual(extra["isBasedOn"], {"@id": extract_id})
        self.assertNotIn("sameAs", extra)
        described = graph[extract_id]
        self.assertEqual(described["@type"], "Dataset")
        self.assertEqual(described["name"], "An extract of the deposit")
        self.assertEqual(described["identifier"], deposit_row.identifier)
        self.assertEqual(described["description"], "Requested from the deposit")
        self.assertEqual(described["isPartOf"], {"@id": "#source-https%3A%2F%2Fdoi.org%2F10.5281%2Fzenodo.7654321%3AThe%20deposit%401.0.0"})
        deposit = graph["#source-https%3A%2F%2Fdoi.org%2F10.5281%2Fzenodo.7654321%3AThe%20deposit%401.0.0"]
        self.assertEqual(deposit["name"], "The deposit")
        self.assertNotIn("isPartOf", deposit)
        self.assertEqual(graph["shared/deposit/1.0.0.txt"]["sameAs"], {"@id": "#source-https%3A%2F%2Fdoi.org%2F10.5281%2Fzenodo.7654321%3AThe%20deposit%401.0.0"})
        self.assertNotIn("extraction", str(crate))
        self.assertNotIn("FAIR-CLI", str(crate))

    def test_issues(self):
        # an issue is a line on each file it was raised against: its uuid, then its
        # severity, then its description, so that a reader can parse it
        end = models.DataProduct.objects.get(name="end")
        bad_row = models.Issue.objects.get(severity=7)
        disagree = models.Issue.objects.get(severity=2)
        repo = models.Object.objects.get(
            storage_location__path="FAIRDataPipeline/shared"
        )
        dirty = models.Issue.objects.create(
            updated_by=self.user, severity=1, description="run from a dirty tree"
        )
        dirty.component_issues.set([repo.components.get(whole_object=True)])

        crate, _ = self._get("data_product_ro_crate", end.id, 100)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}
        vocab = "https://data.fairdatapipeline.org/vocab/#"
        self.assertEqual(crate["@context"][1]["issue"], f"{vocab}issue")

        bad_row_line = f"{bad_row.uuid} severity 7: raw has a bad row"
        self.assertEqual(graph["shared/raw/1.0.0.txt"]["issue"], [bad_row_line])
        # a second name for the same object carries its issues too
        self.assertEqual(graph["shared/alias/1.0.0.txt"]["issue"], [bad_row_line])
        disagree_line = f"{disagree.uuid} severity 2: left and right disagree"
        for name in ("left", "right"):
            entity = graph[f"shared/{name}/1.0.0.txt"]
            self.assertEqual(entity["issue"], [disagree_line])
        self.assertNotIn("issue", graph["shared/end/1.0.0.txt"])
        self.assertNotIn("issue", graph["submission_script/script"])
        software = [
            e for e in graph.values() if e.get("@type") == "SoftwareApplication"
        ]
        self.assertEqual(
            software[0]["issue"], [f"{dirty.uuid} severity 1: run from a dirty tree"]
        )

    def test_run_built_once(self):
        # a run reached through several of its outputs has its files added once: the
        # first visit lists every output, and a walked output's own entity is rebuilt
        # before the run is reached
        end = models.DataProduct.objects.get(name="end")
        with mock.patch.object(
            rocrate, "_add_code_run_files", wraps=rocrate._add_code_run_files
        ) as files:
            self._get("data_product_ro_crate", end.id, 100)
        runs = sorted(call.args[2].description for call in files.call_args_list)
        self.assertEqual(runs, ["final", "left", "pair", "prepare", "right"])

    def test_code_run_identity(self):
        final = models.CodeRun.objects.get(description="final")

        crate, _ = self._get("code_run_ro_crate", final.id, 1)
        graph = {entity["@id"]: entity for entity in crate["@graph"]}

        # a code run is identified by its uuid, whichever registry it is in
        code_run = graph[f"urn:uuid:{final.uuid}"]
        self.assertEqual(code_run["identifier"], str(final.uuid))
        self.assertEqual(code_run["name"], f"code run {final.uuid}")
        self.assertEqual(graph["./"]["name"], f"RO Crate for code run {final.uuid}")
        # and nothing names it by its row in this registry
        self.assertNotIn(f"api/code_run/{final.id}", str(crate))
        # by name, not by substring: a uuid may begin with the row's digits
        names = [entity.get("name") for entity in graph.values()]
        self.assertNotIn(f"code run {final.id}", names)

    def test_code_run(self):
        final = models.CodeRun.objects.get(description="final")
        names = ["alias", "deposit", "first", "left", "raw", "right", "second", "source"]
        names += ["source-copy", "twin"]

        crate, walked = self._get("code_run_ro_crate", final.id, 100)
        self.assertEqual(walked, names)
        self.assertEqual(
            self._code_runs(crate),
            self._ids("final", "pair", "prepare", "left", "right"),
        )

        crate, walked = self._get("code_run_ro_crate", final.id, 2)
        self.assertEqual(walked, ["alias", "first", "raw", "second", "source-copy", "twin"])
        self.assertEqual(self._code_runs(crate), self._ids("final", "pair", "prepare"))
