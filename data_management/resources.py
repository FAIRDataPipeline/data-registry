from import_export import resources
from .models import DataProduct

class DataProductResource(resources.ModelResource):
    class Meta:
        model = DataProduct
