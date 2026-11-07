import html
import re
from unittest import mock

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from data_management import models
from .initdb import init_db
from .init_shared_ancestry_db import init_db as init_shared_ancestry_db


class IndexViewTests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_db()

    def test_index_page_is_displayed(self):
        response = self.client.get(reverse("index"))
        self.assertEqual(response.status_code, 200)

    def test_index_page_displays_data_issues(self):
        response = self.client.get(reverse("index"))
        context = response.context[-1]
        self.assertEqual(len(context["issues"]), 3)

    def test_index_page_displays_data_products(self):
        response = self.client.get(reverse("index"))
        context = response.context[-1]
        self.assertEqual(len(context["data_products"]), 14)

    def test_index_page_displays_external_objects(self):
        response = self.client.get(reverse("index"))
        context = response.context[-1]
        self.assertEqual(len(context["external_objects"]), 2)

    def test_index_page_displays_code_repo_releases(self):
        response = self.client.get(reverse("index"))
        context = response.context[-1]
        self.assertEqual(len(context["code_repo_release"]), 1)


@override_settings(AUTH_METHOD="GitHub")
@mock.patch("data_management.settings.REMOTE_REGISTRY", True)
class SocialLoginTests(TestCase):

    def setUp(self):
        get_user_model().objects.create(username="Test User")
        init_db()

    def test_github_login_button_posts_to_social_begin(self):
        # social-auth-app-django only accepts POST on its begin view, so a
        # plain link to it gets a 405
        client = Client(enforce_csrf_checks=True)
        response = client.get(reverse("index"))
        begin_url = reverse("social:begin", args=["github"])
        match = re.search(
            r'<form[^>]*method="post"[^>]*action="(' + re.escape(begin_url) + r'[^"]*)"[^>]*>(.*?)</form>',
            response.content.decode(),
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        action, form_body = match.groups()
        # submit the form's fields as a browser would
        fields = {
            name: html.unescape(value)
            for name, value in re.findall(r'<input[^>]*name="([^"]+)"[^>]*value="([^"]*)"', form_body)
        }

        response = client.post(html.unescape(action), fields)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://github.com/login/oauth/authorize"))
        # where to return to after GitHub sends the user back
        self.assertEqual(client.session["next"], reverse("index"))


# The detail pages are cached by address, and SQLite gives a rolled-back test's ids
# out again, so a cached page could be another test's
@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class RecordPageTests(TestCase):
    """
    Every kind of record has a page, listed and on its own, and a page shows a
    record's related records as links: a namespace its data products, a code run
    its inputs and outputs by the data products they belong to.
    """

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")

    def _assert_every_page_answers(self):
        for name, model in models.all_models.items():
            with self.subTest(model=name):
                response = self.client.get(reverse(name.lower() + "s"))
                self.assertEqual(response.status_code, 200)
                for pk in model.objects.values_list("pk", flat=True):
                    response = self.client.get(reverse(name.lower(), args=[pk]))
                    self.assertEqual(response.status_code, 200, f"{name} {pk}")

    def test_every_record_of_the_shared_ancestry_has_a_page(self):
        init_shared_ancestry_db(self)
        self._assert_every_page_answers()

    def test_every_record_of_the_original_example_has_a_page(self):
        init_db()
        self._assert_every_page_answers()

    def test_a_namespace_lists_its_data_products(self):
        init_shared_ancestry_db(self)
        namespace = models.Namespace.objects.get(name="shared")
        page = self.client.get(reverse("namespace", args=[namespace.pk])).content.decode()
        for product in namespace.data_products.all():
            self.assertIn(f'href="{reverse("dataproduct", args=[product.pk])}"', page)

    def test_a_code_run_names_its_inputs_and_outputs_by_data_product(self):
        init_shared_ancestry_db(self)
        run = models.CodeRun.objects.get(description="final")
        page = self.client.get(reverse("coderun", args=[run.pk])).content.decode()
        for component in (*run.inputs.all(), *run.outputs.all()):
            for product in component.object.data_products.all():
                self.assertIn(f'href="{reverse("dataproduct", args=[product.pk])}"', page)
                self.assertIn(f"{product.namespace.name}:{product.name}@{product.version}", page)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class SourceAndTablePageTests(TestCase):
    """
    A source's page links what it names: the data products registered from it, its
    identifier, its origin (the original store), and the registry's own copy, which
    only a source whose file the registry holds has. The index's tables link each
    row from its name and show free text as text.
    """

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_shared_ancestry_db(self)

    def _page(self, view, pk):
        response = self.client.get(reverse(view, args=[pk]))
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def _download(self, product):
        return reverse(
            "get_data_product",
            kwargs={
                "namespace": product.namespace.name,
                "data_product_name": product.name,
                "version": product.version,
            },
        )

    def test_a_source_links_its_products_identifier_origin_and_copy(self):
        source = models.ExternalObject.objects.get(title="The source data")
        page = self._page("externalobject", source.pk)
        for product in source.data_products.all():
            self.assertIn(f'href="{reverse("dataproduct", args=[product.pk])}"', page)
        self.assertIn(f'href="{source.identifier}"', page)
        self.assertIn(f'href="{source.original_store.full_uri()}"', page)
        first = source.data_products.order_by("pk").first()
        self.assertIn(f'href="{self._download(first)}"', page)
        self.assertNotIn('href="/data_product/"', page)
        self.assertNotIn("<dt class=\"col-sm-3\">Source</dt>", page)

    def test_a_source_whose_file_the_registry_lacks_has_no_download(self):
        deposit = models.ExternalObject.objects.get(title="The deposit")
        page = self._page("externalobject", deposit.pk)
        self.assertIn(f'href="{deposit.identifier}"', page)
        self.assertNotIn("Download", page)
        self.assertNotIn("None", page)
        extract = models.ExternalObject.objects.get(title="An extract of the deposit")
        page = self._page("externalobject", extract.pk)
        product = extract.data_products.get()
        self.assertIn(f'href="{self._download(product)}"', page)

    def test_a_sources_description_links_its_addresses(self):
        source = models.ExternalObject.objects.get(title="The source data")
        source.description = "Fetched from https://example.org/fetched as described"
        source.save()
        page = self._page("externalobject", source.pk)
        self.assertIn('href="https://example.org/fetched"', page)

    def test_a_data_product_with_no_file_offers_no_download(self):
        deposit = models.DataProduct.objects.get(name="deposit")
        page = self._page("dataproduct", deposit.pk)
        self.assertNotIn(self._download(deposit), page)
        raw = models.DataProduct.objects.get(name="raw")
        self.assertIn(self._download(raw), self._page("dataproduct", raw.pk))

    def test_the_index_tables_link_each_row_by_name_and_escape_text(self):
        markup = models.ExternalObject.objects.create(
            updated_by=self.user,
            identifier="https://doi.org/10.5281/zenodo.42",
            title="<b>bold</b> title",
            release_date="2020-07-10T18:38:00Z",
        )
        rows = self.client.get(
            "/tables/externalobjects", {"limit": 100, "offset": 0}
        ).json()["rows"]
        self.assertEqual(len(rows), models.ExternalObject.objects.count())
        for row in rows:
            self.assertNotIn("None", str(row))
            self.assertIn('<a href="https://doi.org/', row["identifier"])
        titles = {row["title"] for row in rows}
        for source in models.ExternalObject.objects.exclude(pk=markup.pk):
            link = f'<a href="{reverse("externalobject", args=[source.pk])}">{source.title}</a>'
            self.assertIn(link, titles)
        escaped = f'<a href="{reverse("externalobject", args=[markup.pk])}">&lt;b&gt;bold&lt;/b&gt; title</a>'
        self.assertIn(escaped, titles)

        product = models.DataProduct.objects.get(name="raw")
        product.name = "<i>raw</i>"
        product.save()
        rows = self.client.get(
            "/tables/dataproducts", {"limit": 100, "offset": 0}
        ).json()["rows"]
        names = {row["name"] for row in rows}
        self.assertIn(f'<a href="/data_product/{product.pk}">&lt;i&gt;raw&lt;/i&gt;</a>', names)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
)
class DataProductPageTests(TestCase):
    """
    A data product's page is where a reader starts: it says what the product is, who
    made it, where it came from, the run that made it from which inputs and the runs
    that used it, draws its provenance and offers its report and its RO-Crate - the
    crate's zip with the product's file or without, with it unless the file is over
    100 MB.
    """

    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_shared_ancestry_db(self)

    def _page(self, name, **params):
        product = models.DataProduct.objects.get(name=name)
        response = self.client.get(reverse("dataproduct", args=[product.pk]), params)
        self.assertEqual(response.status_code, 200)
        return product, response.content.decode()

    def _href(self, view, pk):
        return f'href="{reverse(view, args=[pk])}"'

    def test_what_it_is_and_who_made_it(self):
        product, page = self._page("end")
        obj = product.object
        if obj.description:
            self.assertIn(obj.description, page)
        for author in obj.authors.all():
            self.assertIn(author.name, page)
        for licence in obj.licences.all():
            self.assertIn(licence.licence_info, page)
        self.assertIn(self._href("namespace", product.namespace.pk), page)
        self.assertNotIn("None", page)

    def test_its_source_and_issues(self):
        product, page = self._page("source")
        self.assertIn(self._href("externalobject", product.external_object.pk), page)
        self.assertIn(product.external_object.title, page)
        raw, page = self._page("raw")
        issues = models.Issue.objects.filter(component_issues__object=raw.object)
        self.assertTrue(issues)
        for issue in issues:
            self.assertIn(self._href("issue", issue.pk), page)
            self.assertIn(issue.description, page)

    def test_the_run_that_made_it_its_inputs_and_the_runs_that_used_it(self):
        product, page = self._page("raw")
        made_by = models.CodeRun.objects.get(outputs__object=product.object)
        self.assertIn(self._href("coderun", made_by.pk), page)
        for component in made_by.inputs.all():
            for source in component.object.data_products.all():
                self.assertIn(self._href("dataproduct", source.pk), page)
        for run in models.CodeRun.objects.filter(inputs__object=product.object):
            self.assertIn(self._href("coderun", run.pk), page)

    def test_its_provenance_drawn_and_offered(self):
        product, page = self._page("end")
        report = reverse("prov_report", args=[product.pk])
        self.assertIn(f'src="{report}?format=svg&amp;depth=1&amp;attributes=False"', page)
        for format_ in ("json-ld", "provn", "xml"):
            self.assertIn(f'href="{report}?format={format_}&amp;depth=1"', page)
        _, page = self._page("end", depth="all")
        self.assertIn(f'src="{report}?format=svg&amp;depth=100&amp;attributes=False"', page)

    def test_its_crate_with_the_file_below_100_mb(self):
        product, page = self._page("end")
        crate = reverse("data_product_ro_crate", args=[product.pk])
        self.assertIn(f'href="{crate}?format=json-ld&amp;depth=1"', page)
        self.assertIn(f'action="{crate}"', page)
        self.assertRegex(page, r'name="pack" value="roots"[^>]*checked')
        self.assertNotRegex(page, r'name="pack" value="none"[^>]*checked')

    def test_its_crate_without_the_file_above_100_mb(self):
        with mock.patch("data_management.views.file_size", return_value=101 * 1024**2):
            product, page = self._page("end")
        self.assertRegex(page, r'name="pack" value="none"[^>]*checked')
        self.assertNotRegex(page, r'name="pack" value="roots"[^>]*checked')
        self.assertIn("101.0", page)

    def test_the_size_of_a_file_in_the_registrys_store_comes_from_the_store(self):
        from django.contrib.sites.models import Site
        from data_management import views

        domain = Site.objects.get_current().domain
        root = models.StorageRoot.objects.create(
            updated_by=self.user, root=f"https://{domain}/data/"
        )
        held = models.StorageLocation.objects.create(
            updated_by=self.user, path="abc123", hash="abc123", storage_root=root
        )
        elsewhere = models.StorageLocation.objects.get(
            path="downloads/source.txt"
        )
        with mock.patch.object(views.settings, "REMOTE_REGISTRY", True):
            with mock.patch.object(views.object_storage, "size", return_value=42) as size:
                self.assertEqual(views.file_size(held), 42)
                self.assertIsNone(views.file_size(elsewhere))
        size.assert_called_once_with("abc123")
        local = models.DataProduct.objects.get(name="end").object.storage_location
        self.assertEqual(views.file_size(local), len(b"end\n"))

    def test_a_product_with_no_file_offers_its_crate_without_one(self):
        product, page = self._page("deposit")
        self.assertNotIn('value="roots"', page)
        self.assertIn('value="none"', page)
