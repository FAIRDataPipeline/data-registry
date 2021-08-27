from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from .initdb import init_db
from .init_prov_db import init_db as init_prov_db


class UsersAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

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
        url = reverse('user-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json(), {'detail': 'Authentication credentials were not provided.'})

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('user-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 4)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('user-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['username'], 'Test User')

    def test_filter_by_username(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('user-list')
        response = client.get(url, data={'username': 'testuserb'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['username'], 'testuserb')


class GroupsAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('group-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 0)


class StorageRootAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storageroot-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 7)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storageroot-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['root'], 'https://jptcp.com/')

    def test_filter_by_root(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storageroot-list')
        response = client.get(url, data={'root': 'https://github.com'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['root'], 'https://github.com')

class StorageLocationAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storagelocation-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 18)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storagelocation-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['path'], 'master/SCRC/human/infection/SARS-CoV-2/symptom-probability/0.1.0.toml')

    def test_filter_by_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storagelocation-list')
        response = client.get(url, data={'path': 'master/SCRC/human/infection/SARS-CoV-2/latent-period/0.1.0.toml'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['path'], 'master/SCRC/human/infection/SARS-CoV-2/latent-period/0.1.0.toml')

    def test_filter_by_hash(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('storagelocation-list')
        response = client.get(url, data={'hash': '43faf6d048b92ed1820db2e662ba403eb0e371fb'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['path'], 'human/infection/SARS-CoV-2/scotland/cases_and_management/v0.1.0.h5')


class ObjectAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('object-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 16)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('object-detail', kwargs={'pk': 3})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['storage_location'], 'http://testserver/api/storage_location/2/')

    def test_filter_by_storage_location(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('object-list')
        response = client.get(url, data={'storage_location': '3'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['storage_location'], 'http://testserver/api/storage_location/3/')


class ObjectComponentAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('objectcomponent-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 48)

    def test_get_detail_whole_object(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('objectcomponent-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'whole_object')

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('objectcomponent-detail', kwargs={'pk': 17})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'symptom-probability')

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('objectcomponent-list')
        response = client.get(url, data={'name': 'nhs_health_board/per_location/all_deaths'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'nhs_health_board/per_location/all_deaths')


class IssueAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('issue-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('issue-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['description'], 'Test Issue 1')

    def test_filter_by_severity(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('issue-list')
        response = client.get(url, data={'severity': '6'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['description'], 'Test Issue 2')


class CodeRunAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('coderun-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('coderun-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['description'], 'Script run to upload and process scottish coronavirus-covid-19-management-information')

    def test_filter_by_run_date(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('coderun-list')
        response = client.get(url, data={'run_date': '2020-07-17T18:21:11Z'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['description'], 'Script run to upload and process scottish coronavirus-covid-19-management-information')

    def test_filter_by_description(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('coderun-list')
        response = client.get(url, data={'description': 'Script run to upload and process scottish coronavirus-covid-19-management-information'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['description'], 'Script run to upload and process scottish coronavirus-covid-19-management-information')

class ExternalObjectAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('externalobject-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 2)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('externalobject-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['alternate_identifier'], 'scottish deaths-involving-coronavirus-covid-19')

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('externalobject-list')
        response = client.get(url, data={'alternate_identifier': 'scottish coronavirus-covid-19-management-information'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['alternate_identifier'], 'scottish coronavirus-covid-19-management-information')

    def test_filter_by_title(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('externalobject-list')
        response = client.get(url, data={'title': 'scottish deaths-involving-coronavirus-covid-19'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['alternate_identifier'], 'scottish deaths-involving-coronavirus-covid-19')

class QualityControlledAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('qualitycontrolled-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('qualitycontrolled-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['object'], 'http://testserver/api/object/15/')


class KeywordAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyword-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 5)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyword-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['keyphrase'], 'treatment')

    def test_filter_by_keyphrase(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyword-list')
        response = client.get(url, data={'keyphrase': 'monoclonal antibodies'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['keyphrase'], 'monoclonal antibodies')

    def test_filter_by_keyphrase_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyword-list')
        response = client.get(url, data={'keyphrase': 'co*'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 2)


class AuthorAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 3)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'Ivana Valenti')

    def test_filter_by_family_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-list')
        response = client.get(url, data={'name': '*ti'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 2)

    def test_filter_by_family_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-list')
        response = client.get(url, data={'name': '*Cipriani'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Maria Cipriani')

    def test_filter_by_given_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('author-list')
        response = client.get(url, data={'name': 'Rosanna*'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'Rosanna Massabeti')


class LicenceAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('licence-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('licence-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('Copyright 2020 SCRC', response.json()['licence_info'])


class NamespaceAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('namespace-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 2)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('namespace-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'FAIR')

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('namespace-list')
        response = client.get(url, data={'name': 'simple_network_sim'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'simple_network_sim')

    def test_filter_by_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('namespace-list')
        response = client.get(url, data={'name': '[fF]*'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)


class DataProductAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 13)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-detail', kwargs={'pk': 3})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'human/infection/SARS-CoV-2/symptom-probability')

    def test_filter_by_namespace(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, data={'namespace': '1'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 9)

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, data={'name': 'human/infection/SARS-CoV-2/latent-period'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'human/infection/SARS-CoV-2/latent-period')

    def test_filter_by_name_glob(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, data={'name': 'human/infection/SARS-CoV-2/*'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 7)

    def test_filter_by_version(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('dataproduct-list')
        response = client.get(url, data={'version': '0.1.0'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 13)


class CodeRepoReleaseAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('codereporelease-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('codereporelease-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['name'], 'ScottishCovidResponse/SCRCdata')

    def test_filter_by_name(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('codereporelease-list')
        response = client.get(url, data={'name': 'ScottishCovidResponse/SCRCdata'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'ScottishCovidResponse/SCRCdata')

    def test_filter_by_version(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('codereporelease-list')
        response = client.get(url, data={'version': '0.1.0'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'ScottishCovidResponse/SCRCdata')


class KeyvalueAPITests(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='Test User')
        init_db()

    def test_get_list(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyvalue-list')
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 4)

    def test_get_detail(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyvalue-detail', kwargs={'pk': 1})
        response = client.get(url, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.json()['key'], 'TestKey1')

    def test_filter_by_key(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse('keyvalue-list')
        response = client.get(url, data={'key': 'TestKey2'}, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['key'], 'TestKey2')


class ProvAPITests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username="Test User")
        init_prov_db()

    def test_get_json(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        url = reverse("prov_report", kwargs={"pk": 2})
        response = client.get(url, format="json", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        results = response.json()

        expected_result = {
            "prov:type": "file",
            "storage": "https://data.scrc.uk/api/text_file/input/1",
            "description": "input 1 object",
            "namespace": "prov",
            "name": "this/is/cr/test/input/1",
            "version": "0.2.0",
        }
        prov_out = results["entity"]["api/data_product/1"]
        del prov_out["last_updated"]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            "prov:type": "file",
            "storage": "https://data.scrc.uk/api/text_file/output/1",
            "description": "output 1 object",
            "namespace": "prov",
            "name": "this/is/cr/test/output/1",
            "version": "0.2.0",
        }
        prov_out = results["entity"]["api/data_product/2"]
        del prov_out["last_updated"]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            "prov:type": "file",
            "storage": "https://data.scrc.uk/api/text_file/output/2",
            "description": "output 2 object",
            "namespace": "prov",
            "name": "this/is/cr/test/output/2",
            "version": "0.2.0",
        }
        prov_out = results["entity"]["api/data_product/3"]
        del prov_out["last_updated"]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            "prov:type": "file",
            "storage": "https://data.scrc.uk/api/text_file/input/2",
            "description": "input 2 object",
            "namespace": "prov",
            "name": "this/is/cr/test/input/2",
            "version": "0.2.0",
        }
        prov_out = results["entity"]["api/data_product/4"]
        del prov_out["last_updated"]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            "prov:type": "file",
            "storage": "https://data.scrc.uk/api/text_file/input/3",
            "description": "input 3 object",
            "namespace": "prov",
            "name": "this/is/cr/test/input/3",
            "version": "0.2.0",
        }
        prov_out = results["entity"]["api/data_product/5"]
        del prov_out["last_updated"]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            "title": "this is cr test input 1",
            "release_date": {"$": "2020-07-10T18:38:00+00:00", "type": "xsd:dateTime"},
            "original_store": "https://example.org/file_strore/1.txt",
            "version": "0.2.0",
            "alternate_identifier": "this_is_cr_test_input_1",
            "alternate_identifier_type": "text",
            "description": "this is code run test input 1",
        }
        self.assertEqual(results["entity"]["api/external_object/1"], expected_result)

        expected_result = {
            "title": "this is cr test output 1",
            "release_date": {"$": "2021-07-10T18:38:00+00:00", "type": "xsd:dateTime"},
            "original_store": "https://example.org/file_strore/2.txt",
            "version": "0.2.0",
            "alternate_identifier": "this_is_cr_test_output_1",
            "alternate_identifier_type": "text",
            "description": "this is code run test output 1",
            "identifier": "this_is_cr_test_output_1_id",
        }
        self.assertEqual(results["entity"]["api/external_object/2"], expected_result)

        expected_result = {
            "title": "this is cr test output 2",
            "release_date": {"$": "2021-07-10T18:38:00+00:00", "type": "xsd:dateTime"},
            "version": "0.2.0",
            "identifier": "this_is_cr_test_output_2",
        }
        self.assertEqual(results["entity"]["api/external_object/3"], expected_result)

        expected_result = {
            "storage": "https://github.comScottishCovidResponse/SCRCdata repository",
            "name": "ScottishCovidResponse/SCRCdata",
            "version": "0.1.0",
            "website": "https://github.com/ScottishCovidResponse/SCRCdata",
        }
        prov_out = results["entity"]["api/code_repo_release/1"]
        del prov_out["last_updated"]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            "storage": "https://data.scrc.uk/api/text_file/15/?format=text"
        }
        prov_out = results["entity"]["api/object/3"]
        del prov_out["last_updated"]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            "file_type": "text file",
            "storage": "https://data.scrc.uk/api/text_file/16/?format=text",
        }
        prov_out = results["entity"]["api/object/4"]
        del prov_out["last_updated"]
        self.assertEqual(prov_out, expected_result)

        expected_result = {
            "api/code_run/1": {
                "prov:startTime": "2021-07-17T18:21:11+00:00",
                "prov:type": "run",
                "description": "Test run",
            }
        }
        self.assertEqual(results["activity"], expected_result)

        expected_result = {
            "api/author/3": [
                {"prov:type": "prov:Person", "name": "Rosanna Massabeti"},
                {"prov:type": "prov:Person", "name": "Rosanna Massabeti"},
                {"prov:type": "prov:Person", "name": "Rosanna Massabeti"},
            ],
            "api/user/1": {"prov:type": "prov:Person", "name": "User Not Found"},
            "api/author/1": {"prov:type": "prov:Person", "name": "Ivana Valenti"},
            "api/author/2": {"prov:type": "prov:Person", "name": "Maria Cipriani"},
        }
        self.assertEqual(results["agent"], expected_result)

        expected_result = {
            "_:id2": {
                "prov:specificEntity": "api/external_object/2",
                "prov:generalEntity": "api/data_product/2",
            },
            "_:id8": {
                "prov:specificEntity": "api/external_object/1",
                "prov:generalEntity": "api/data_product/1",
            },
            "_:id18": {
                "prov:specificEntity": "api/external_object/3",
                "prov:generalEntity": "api/data_product/3",
            },
        }
        self.assertEqual(results["specializationOf"], expected_result)

        expected_result = {
            "_:id5": {
                "prov:activity": "api/code_run/1",
                "prov:entity": "api/code_repo_release/1",
                "prov:role": "software",
            },
            "_:id6": {
                "prov:activity": "api/code_run/1",
                "prov:entity": "api/object/3",
                "prov:role": "model configuration",
            },
            "_:id7": {
                "prov:activity": "api/code_run/1",
                "prov:entity": "api/object/4",
                "prov:role": "submission script",
            },
            "_:id10": {
                "prov:activity": "api/code_run/1",
                "prov:entity": "api/data_product/1",
                "prov:role": "input data",
            },
            "_:id13": {
                "prov:activity": "api/code_run/1",
                "prov:entity": "api/data_product/4",
                "prov:role": "input data",
            },
            "_:id16": {
                "prov:activity": "api/code_run/1",
                "prov:entity": "api/data_product/5",
                "prov:role": "input data",
            },
        }
        self.assertEqual(results["used"], expected_result)

        expected_result = {
            "_:id1": {
                "prov:entity": "api/data_product/2",
                "prov:agent": "api/author/3",
                "prov:role": "author",
            },
            "_:id9": {
                "prov:entity": "api/data_product/1",
                "prov:agent": "api/author/1",
                "prov:role": "author",
            },
            "_:id12": {
                "prov:entity": "api/data_product/4",
                "prov:agent": "api/author/2",
                "prov:role": "author",
            },
            "_:id15": {
                "prov:entity": "api/data_product/5",
                "prov:agent": "api/author/3",
                "prov:role": "author",
            },
            "_:id19": {
                "prov:entity": "api/data_product/3",
                "prov:agent": "api/author/3",
                "prov:role": "author",
            },
        }
        self.assertEqual(results["wasAttributedTo"], expected_result)

        expected_result = {
            "_:id11": {
                "prov:generatedEntity": "api/data_product/2",
                "prov:usedEntity": "api/data_product/1",
            },
            "_:id14": {
                "prov:generatedEntity": "api/data_product/2",
                "prov:usedEntity": "api/data_product/4",
            },
            "_:id17": {
                "prov:generatedEntity": "api/data_product/2",
                "prov:usedEntity": "api/data_product/5",
            },
        }
        self.assertEqual(results["wasDerivedFrom"], expected_result)

        expected_result = {
            "_:id3": {
                "prov:entity": "api/data_product/2",
                "prov:activity": "api/code_run/1",
            },
            "_:id20": {
                "prov:entity": "api/data_product/3",
                "prov:activity": "api/code_run/1",
            },
        }
        self.assertEqual(results["wasGeneratedBy"], expected_result)

        expected_result = {
            "_:id4": {
                "prov:activity": "api/code_run/1",
                "prov:trigger": "api/user/1",
                "prov:time": "2021-07-17T18:21:11+00:00",
                "prov:role": "code runner",
            }
        }
        self.assertEqual(results["wasStartedBy"], expected_result)

    def test_get_provn(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 1})
        response = client.get(
            url, format="provn", HTTP_ACCEPT="text/provenance-notation"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"], "text/provenance-notation; charset=utf8"
        )

        result_bits = response.data.split("last_updated")
        result_end = result_bits[1].split("xsd:dateTime, ", 1)[1]
        result = result_bits[0] + result_end
        expected_result = """document
  default <http://example.com/>
  
  entity(api/data_product/1, [prov:type="file", storage="https://data.scrc.uk/api/text_file/input/1", description="input 1 object", namespace="prov", name="this/is/cr/test/input/1", version="0.2.0"])
  agent(api/author/1, [prov:type="prov:Person", name="Ivana Valenti"])
  wasAttributedTo(api/data_product/1, api/author/1, [prov:role="author"])
  entity(api/external_object/1, [title="this is cr test input 1", release_date="2020-07-10T18:38:00+00:00" %% xsd:dateTime, version="0.2.0", alternate_identifier="this_is_cr_test_input_1", alternate_identifier_type="text", description="this is code run test input 1", original_store="https://example.org/file_strore/1.txt"])
  specializationOf(api/external_object/1, api/data_product/1)
endDocument"""
        self.assertEqual(result, expected_result)

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
        self.assertNotContains(response, "api/code_repo/", 200)
        self.assertNotContains(response, "api/code_repo_release/", 200)

    def test_get_no_repo_release(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        url = reverse("prov_report", kwargs={"pk": 6})
        response = client.get(url, format="xml", HTTP_ACCEPT="text/xml")
        self.assertEqual(response["Content-Type"], "text/xml; charset=utf8")
        self.assertContains(response, "api/code_repo/", status_code=200)
