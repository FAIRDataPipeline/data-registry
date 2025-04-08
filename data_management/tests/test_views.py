from django.test import TestCase
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
