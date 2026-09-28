from io import StringIO
import sys
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from data_management import settings as dm_settings
from data_management.models import Object, StorageLocation, StorageRoot


class AddExampleDataTests(TestCase):
    def test_command_output(self):
        """
        Test `add_example_data` works in the normal case.

        """
        out = StringIO()
        sys.stdout = out
        call_command("add_example_data", stdout=out)
        self.assertIn("The example data has been added to the database", out.getvalue())

    def test_command_error(self):
        """
        Test `add_example_data` fails if there is data in the db.

        """
        # add some data to the db
        _add_object_to_db()
        out = StringIO()
        sys.stdout = out
        err = StringIO()
        sys.stderr = err
        call_command("add_example_data", stdout=out, stderr=err)
        self.assertEqual("", out.getvalue())
        self.assertIn(
            "This command will only run if the database contains no "
            "'Objects'. Use the '--force' option to override this behaviour.",
            err.getvalue(),
        )

    def test_command_force(self):
        """
        Test `add_example_data` works if there is data in the db and the `--force` "
        "flag is set.

        """
        # add some data to the db
        _add_object_to_db()
        out = StringIO()
        sys.stdout = out
        call_command("add_example_data", stdout=out, force=True)
        self.assertIn("The example data has been added to the database", out.getvalue())

    def test_command_rerun(self):
        """
        Test `add_example_data` works if it is rerun with the `--force` flag set.

        """
        call_command("add_example_data")
        out = StringIO()
        sys.stdout = out
        call_command("add_example_data", stdout=out, force=True)
        self.assertIn("The example data has been added to the database", out.getvalue())

    def test_command_no_db(self):
        """
        Test `add_example_data` works in the normal case.

        """
        call_command("drop_test_database", "--noinput")
        out = StringIO()
        sys.stdout = out
        err = StringIO()
        sys.stderr = err
        call_command("add_example_data", stdout=out, stderr=err)
        # TODO need to get the drop db working
        # self.assertEqual("", out.getvalue())
        # self.assertIn(
        #     "It looks like the database may not have been initialised", err.getvalue()
        # )


class SetSiteInfoTests(TestCase):
    def setUp(self):
        get_user_model().objects.create(username="setSiteInfoTestsUser")

    def test_data_store_root(self):
        """
        Test a remote registry's data store is `<DOMAIN_URL>data/`, with or without a
        trailing slash on `DOMAIN_URL`, and contains the site domain that `get_data`
        looks it up by.

        """
        for domain_url, root in (
            ("https://example.com/", "https://example.com/data/"),
            ("https://example.com", "https://example.com/data/"),
            ("http://127.0.0.1:8001/", "http://127.0.0.1:8001/data/"),
            ("https://example.com/registry", "https://example.com/registry/data/"),
        ):
            with self.subTest(domain_url=domain_url):
                StorageRoot.objects.all().delete()
                _set_site_info(domain_url)
                self.assertEqual(
                    list(StorageRoot.objects.values_list("root", flat=True)), [root]
                )
                self.assertIn(Site.objects.get_current().domain, root)

    def test_rerun(self):
        """
        Test `set_site_info` can be rerun without adding a second data store.

        """
        _set_site_info("https://example.com/")
        _set_site_info("https://example.com/")
        self.assertEqual(StorageRoot.objects.count(), 1)

    def test_no_scheme(self):
        """
        Test `set_site_info` refuses a `DOMAIN_URL` that is not an http(s) URL.

        """
        for domain_url in ("example.com", "localhost:8001/"):
            with self.subTest(domain_url=domain_url):
                with self.assertRaises(CommandError):
                    _set_site_info(domain_url)
                self.assertEqual(StorageRoot.objects.count(), 0)


def _set_site_info(domain_url):
    """
    Run `set_site_info` as a remote registry whose `DOMAIN_URL` is `domain_url`.

    """
    with override_settings(DOMAIN_URL=domain_url), mock.patch.object(
        dm_settings, "REMOTE_REGISTRY", True
    ):
        call_command("set_site_info")


def _add_object_to_db():
    """
    Add minimal data to the db.

    """
    user = get_user_model().objects.create(username="addExampleDataTestsUser")

    sr_example = StorageRoot.objects.create(
        updated_by=user, root="https://example.com/addExampleDataTests/"
    )

    sl_code = StorageLocation.objects.create(
        updated_by=user,
        path="test/addExampleDataTestsUser_repository",
        hash="b98782baaaea3bf6cc2882ad7d1c5de7aece369",
        storage_root=sr_example,
    )

    Object.objects.create(updated_by=user, storage_location=sl_code)
