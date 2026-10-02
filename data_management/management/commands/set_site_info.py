import re
from urllib.parse import urlsplit
from django.core.management.base import BaseCommand, CommandError
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
                    url = urlsplit(domain_url)
                    if url.scheme not in ("http", "https") or not url.netloc:
                        raise CommandError(
                            f"DOMAIN_URL '{settings.DOMAIN_URL}' must be an "
                            "http:// or https:// URL, as it is the root of the "
                            "data store's file URLs"
                        )
                    StorageRoot.objects.get_or_create(
                        root=f"{domain_url}data/",
                        defaults={"updated_by": user},
                    )
