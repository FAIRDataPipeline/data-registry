from unittest import mock
from urllib.parse import parse_qs, urlparse

from botocore.exceptions import ClientError
from django.test import SimpleTestCase, override_settings

from data_management import object_storage


@override_settings(
    BUCKETS={
        "default": {
            "url": "https://storage.example.org/s3",
            "bucket_name": "fair",
            "access_key": "AccessKey",
            "secret_key": "SecretKey",
            "duration": "600",
        }
    }
)
class CreateUrlTests(SimpleTestCase):

    def assert_signed_with_sigv4(self, url):
        # SeaweedFS behind a proxy that strips a path prefix can only verify
        # SigV4, which honours X-Forwarded-Prefix; SigV2 URLs are rejected
        query = parse_qs(urlparse(url).query)
        self.assertEqual(query["X-Amz-Algorithm"], ["AWS4-HMAC-SHA256"])
        self.assertNotIn("AWSAccessKeyId", query)

    def test_download_url_is_signed_with_sigv4(self):
        url = object_storage.create_url("abc123", "GET", "abc123.png")

        self.assert_signed_with_sigv4(url)
        self.assertTrue(url.startswith("https://storage.example.org/s3/fair/abc123?"))
        self.assertEqual(
            parse_qs(urlparse(url).query)["response-content-disposition"],
            ["attachment; filename = abc123.png"],
        )

    def test_upload_url_is_signed_with_sigv4(self):
        url = object_storage.create_url("abc123", "PUT")

        self.assert_signed_with_sigv4(url)


@override_settings(
    BUCKETS={
        "default": {
            "url": "https://storage.example.org/s3",
            "bucket_name": "fair",
            "access_key": "AccessKey",
            "secret_key": "SecretKey",
            "duration": "600",
        }
    }
)
class HoldsTests(SimpleTestCase):

    def _store(self, head_object):
        client = mock.Mock()
        client.head_object.side_effect = head_object
        return mock.patch.object(object_storage, "_client", return_value=client)

    @staticmethod
    def _missing(**kwargs):
        raise ClientError({"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject")

    def test_a_held_file(self):
        with self._store(lambda **kwargs: {"ContentLength": 12}) as store:
            self.assertTrue(object_storage.holds("abc123"))
        store.return_value.head_object.assert_called_once_with(Bucket="fair", Key="abc123")

    def test_a_missing_file(self):
        with self._store(self._missing):
            self.assertFalse(object_storage.holds("abc123"))

    def test_a_failed_upload_is_not_the_file(self):
        # a PUT that fails part-way leaves a 0-byte object under the key
        with self._store(lambda **kwargs: {"ContentLength": 0}):
            self.assertFalse(object_storage.holds("abc123"))
            self.assertTrue(object_storage.holds(object_storage.EMPTY_FILE_SHA1))

    def test_any_other_refusal_is_raised(self):
        def forbidden(**kwargs):
            raise ClientError({"Error": {"Code": "403", "Message": "Forbidden"}}, "HeadObject")

        with self._store(forbidden):
            with self.assertRaises(ClientError):
                object_storage.holds("abc123")
