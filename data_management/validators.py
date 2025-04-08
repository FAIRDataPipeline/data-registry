import semver
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


@deconstructible
class VersionValidator:
    """
    Custom validator to apply semantic versioning validation to a field.
    """

    message = "Version %(value)s is not a valid semantic version."
    code = "invalid_version"

    def __call__(self, value):
        try:
            semver.parse(value)
        except ValueError:
            raise ValidationError(
                self.message,
                code=self.code,
                params={
                    "value": value,
                },
            )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.message == other.message
            and self.code == other.code
        )


@deconstructible
class NameValidator:
    """
    Custom validator to ensure field does not contain characters that might break glob filtering.
    """

    INVALID_CHARS = "[]?*"
    message = "Name %(value)s contains invalid characters (" + INVALID_CHARS + ")."
    code = "invalid_name"

    def __call__(self, value):
        for char in self.INVALID_CHARS:
            if char in value:
                raise ValidationError(
                    self.message,
                    code=self.code,
                    params={
                        "value": value,
                    },
                )

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.message == other.message
            and self.code == other.code
        )
