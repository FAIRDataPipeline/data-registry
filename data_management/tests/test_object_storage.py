from urllib.parse import parse_qs, urlparse

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
