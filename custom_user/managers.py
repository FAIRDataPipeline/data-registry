from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom user manager that handles the fact that the email address on our custom user is readonly therefore we cannot
    try and set it as part of creating a new superuser, which is the default behaviour.
    """

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError("The given username must be set")
        username = self.model.normalize_username(username)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, password, **extra_fields)

    def create_user(self, password=None, **kwargs):
        """Create and return a `User` with an username"""

        username = kwargs.get("username")

        if username is None:
            raise TypeError("Users must have a username.")

        user = self.model(username=self.model.normalize_username(username))
        user.set_password(password)
        user.save()

        return user
