from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

from data_management.management.commands._example_data import init_db
from data_management.models import Object


class Command(BaseCommand):

    help = "Add example data to the registry"

    def add_arguments(self, parser):
        """
        Define the options.

        """
        parser.add_argument(
            "--force",
            action="store_true",
            help="Add the example data even if the database is not empty",
        )

    def handle(self, **options):

        force = options["force"]

        try:
            user = get_user_model().objects.all()
            group = Group.objects.all()
            objects = Object.objects.all()

            if (len(user) > 0 or len(group) > 0 or len(objects) > 0) and not force:
                self.stderr.write(
                    "This command will only run if the database is empty. "
                    "Use the '--force' option to override this behaviour."
                )
                return

        except OperationalError as ex:
            self.stderr.write(f"ERROR: {ex}")
            self.stderr.write(
                "It looks like the database may not have been initialised"
            )
            self.stderr.write("You could try:")
            self.stderr.write("python manage.py makemigrations custom_user")
            self.stderr.write("python manage.py makemigrations data_management")
            self.stderr.write("python manage.py migrate")
            return

        init_db()

        self.stdout.write("The example data has been added to the database")
