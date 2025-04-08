from rest_framework import metadata


class CustomMetadata(metadata.SimpleMetadata):

    def determine_metadata(self, request, view):
        data = super().determine_metadata(request, view)
        try:
            if view.model.FILTERSET_FIELDS == "__all__":
                filter_fields = view.model.field_names()
            else:
                filter_fields = view.model.FILTERSET_FIELDS
            data["filter_fields"] = filter_fields
        except AttributeError:
            pass
        return data
