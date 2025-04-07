import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    def handle(self, **options):
        user_model = get_user_model()
        user = user_model.objects.get_by_natural_key("admin")
        token = Token.objects.get_or_create(user=user)
        print(token[0])
