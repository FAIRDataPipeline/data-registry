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
