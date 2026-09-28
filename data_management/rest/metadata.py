from rest_framework import metadata


class CustomMetadata(metadata.SimpleMetadata):

    def determine_metadata(self, request, view):
        data = super().determine_metadata(request, view)
        try:
            data["filter_fields"] = view.model.filter_field_names()
        except AttributeError:
            pass
        return data
