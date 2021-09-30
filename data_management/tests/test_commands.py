from io import StringIO
import sys

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
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
