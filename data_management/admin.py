from django.contrib import admin

from . import models

admin.site.site_header = "FAIR Data Management"


class BaseAdmin(admin.ModelAdmin):
    """
    Base model for admin views.
    """

    readonly_fields = ("updated_by", "last_updated")
    list_display = ("last_updated",)

    def save_model(self, request, obj, form, change):
        """
        Customising the admin save behaviour to add the current user as the updated_by user on the model.
        """
        obj.updated_by = request.user
        return super().save_model(request, obj, form, change)


class IssueAdmin(BaseAdmin):
    """
    Admin view for the Issue model.
    """

    readonly_fields = ("updated_by", "last_updated", "linked_objects")
    list_display = ("short_desc", "severity", "last_updated")

    @classmethod
    def linked_objects(cls, issue):
        """
        Return all the Objects and ObjectComponents that this Issue has been assigned to.
        """
        return list(issue.object_issues.all()) + list(issue.component_issues.all())


for name, cls in models.all_models.items():
    if issubclass(cls, models.Issue):
        admin.site.register(cls, IssueAdmin)
    else:
        data = {"list_display": cls.ADMIN_LIST_FIELDS + ("updated_by", "last_updated")}
        admin_cls = type(name + "Admin", (BaseAdmin,), data)
        admin.site.register(cls, admin_cls)
