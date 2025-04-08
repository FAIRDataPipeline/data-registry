import re
from django.core.management.base import BaseCommand
from django.conf import settings
from data_management import settings as dm_settings
from django.contrib.sites.models import Site

from data_management.models import StorageRoot
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    def handle(self, **options):
        if settings.DOMAIN_URL:
            domain = re.sub(r"http.*:\/\/", "", settings.DOMAIN_URL)
            if domain[-1] == "/":
                domain = domain.rstrip(domain[-1])
            this_site = Site.objects.all()[0]
            this_site.domain = domain
            this_site.name = domain
            this_site.save()

            if dm_settings.REMOTE_REGISTRY:
                user = get_user_model().objects.first()
                if user:
                    domain_url = settings.DOMAIN_URL
                    if domain_url[-1] != "/":
                        domain_url += "/"
                    root = f"{settings.DOMAIN_URL}data/"
                    StorageRoot.objects.create(
                        updated_by=user,
                        root=root,
                    )
