from django.contrib.auth.models import AbstractUser, AbstractBaseUser
from django.conf import settings
import mysql.connector as mariadb
import yaml

from .managers import CustomUserManager

def _get_users():
    _authorised_users_file = settings.AUTHORISED_USER_FILE
    if _authorised_users_file:
        try:
            _authorised_users = yaml.safe_load(open(_authorised_users_file))
            if "users" in _authorised_users:
                return _authorised_users["users"]
        except Exception as e:
            return []
    return []

def _get_user(username):
    if username in _get_users():
        return _get_users()[username]
    return None

def _get(key, username):
    _user = _get_user(username)
    if _user:
        if key in _user:
            return _user[key]
    return None

def _get_full_name(username):
    if _get("fullname", username):
        return _get("fullname", username)
    return 'User Not Found'

def _get_email(username):
    _user = _get_user(username)
    if _user:
        if "email" in _user:
            return _user["email"]
    return 'User Not Found'

def _get_orgs(username):
    if _get("orgs", username):
        return _get("fullname", username)
    return []


class User(AbstractUser):
    """
    Custom user that retrieves user details from the SCRC personnel database.
    """
    objects = CustomUserManager()

    REQUIRED_FIELDS = []

    def full_name(self):
        return _get_full_name(self.username)

    def email(self):
        return _get_email(self.username)

    def orgs(self):
        return _get_orgs(self.username)

    def clean(self):
        # Skip the AbstractUser.clean as this tries to set self.email
        AbstractBaseUser.clean(self)
