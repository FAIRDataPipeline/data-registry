from django.contrib.auth.models import AbstractUser, AbstractBaseUser
from django.core.exceptions import ValidationError
from django.conf import settings
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
    _users = _get_users()
    for _user in _users:
        if "username" in _user:
            if username == _user["username"]:
                return _user
    return None

def _is_valid_user(username):
    if _get_user(username):
        return True
    return False

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
    return f'{username}@users.noreply.github.com'

def _get_orgs(username):
    if _get("orgs", username):
        return _get("orgs", username)
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
        if not self.is_superuser:
            if _get_users():
                if not _is_valid_user(self.username):
                    raise ValidationError(
                    {'username': "Username is not in allowed users"})
        AbstractBaseUser.clean(self)
    
    def save(self, *args, **kwargs):
        # This overriding of the save method is necessary because Django by default does not call the
        # full_clean() method and there is where the clean() method is called
        self.full_clean()
        return super().save(*args, **kwargs)
