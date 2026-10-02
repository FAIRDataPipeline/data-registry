import html
import re
from unittest import mock

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from .initdb import init_db


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
