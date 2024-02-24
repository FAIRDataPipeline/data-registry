from rest_framework import renderers, serializers
from rest_framework.utils.field_mapping import ClassLookupDict
from data_management import settings

class HTMLFormRenderer(renderers.HTMLFormRenderer):
    """
    Subclassing the default HTMLFormRenderer to override some of the default_style options.

    We need to do this as the default style for the relational fields causes a timeout when
    generating the HTML for for very large number of options for the related field.
    """
    default_style = ClassLookupDict({
        serializers.Field: {
            'base_template': 'input.html',
            'input_type': 'text'
        },
        serializers.EmailField: {
            'base_template': 'input.html',
            'input_type': 'email'
        },
        serializers.URLField: {
            'base_template': 'input.html',
            'input_type': 'url'
        },
        serializers.IntegerField: {
            'base_template': 'input.html',
            'input_type': 'number'
        },
        serializers.FloatField: {
            'base_template': 'input.html',
            'input_type': 'number'
        },
        serializers.DateTimeField: {
            'base_template': 'input.html',
            'input_type': 'datetime-local'
        },
        serializers.DateField: {
            'base_template': 'input.html',
            'input_type': 'date'
        },
        serializers.TimeField: {
            'base_template': 'input.html',
            'input_type': 'time'
        },
        serializers.FileField: {
            'base_template': 'input.html',
            'input_type': 'file'
        },
        serializers.BooleanField: {
            'base_template': 'checkbox.html'
        },
        serializers.ChoiceField: {
            'base_template': 'select.html',  # Also valid: 'radio.html'
        },
        serializers.MultipleChoiceField: {
            'base_template': 'select_multiple.html',  # Also valid: 'checkbox_multiple.html'
        },
        serializers.RelatedField: {
            'base_template': 'input.html',
            'input_type': 'text'
        },
        serializers.ManyRelatedField: {
            'base_template': 'input.html',
            'input_type': 'text'
        },
        serializers.Serializer: {
            'base_template': 'fieldset.html'
        },
        serializers.ListSerializer: {
            'base_template': 'list_fieldset.html'
        },
        serializers.ListField: {
            'base_template': 'list_field.html'
        },
        serializers.DictField: {
            'base_template': 'dict_field.html'
        },
        serializers.FilePathField: {
            'base_template': 'select.html',
        },
        serializers.JSONField: {
            'base_template': 'textarea.html',
        },
    })


class BrowsableAPIRenderer(renderers.BrowsableAPIRenderer):
    """
    Subclassing the BrowsableAPIRenderer to use our custom HTMLFormRenderer.
    """
    form_renderer_class = HTMLFormRenderer
    def get_context(self, *args, **kwargs):
        context = super(BrowsableAPIRenderer, self).get_context(*args, **kwargs)
        context["remote_registry"] = settings.REMOTE_REGISTRY
        return(context)
