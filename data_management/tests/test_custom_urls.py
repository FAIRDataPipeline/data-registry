from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .initdb import init_db

class CustomURLTests(TestCase):
    def setUp(self):
        settings.AUTH_METHOD = "GitLab"
        settings.SOCIAL_AUTH_GITLAB_API_URL = "https://test.com"
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_auth_provider_url(self):
        client = APIClient()
        url = reverse('auth-provider')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['auth_provider'], 'GitLab')

    def test_auth_url(self):
        client = APIClient()
        url = reverse('auth-url')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['auth_url'], 'https://test.com')

    def test_auth_url_github(self):
        client = APIClient()
        settings.AUTH_METHOD = "GitHub"
        settings.SOCIAL_AUTH_GITLAB_API_URL = None
        url = reverse('auth-url')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['auth_url'], 'https://github.com')

    def test_auth_url_github_no_api(self):
        client = APIClient()
        settings.AUTH_METHOD = "GitLab"
        settings.SOCIAL_AUTH_GITLAB_API_URL = None
        url = reverse('auth-url')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['auth_url'], 'https://gitlab.com')

    def test_auth_provider_url_github(self):
        client = APIClient()
        settings.AUTH_METHOD = "GitHub"
        url = reverse('auth-provider')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['auth_provider'], 'GitHub')
