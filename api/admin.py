import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import HtmlFormatter

from django.contrib import admin
from django.utils.safestring import mark_safe

from api.models import Activity


def pretty_json(instance, field_name):
    """Function to display pretty version of our data"""
    json_data = getattr(instance, field_name)
    json_string = json.dumps(json_data, ensure_ascii=False, indent=2) if json_data else ''
    formatter = HtmlFormatter(style='colorful')
    response = highlight(json_string, JsonLexer(), formatter)
    scroll_style = ".highlight { height: 20em; overflow: scroll; border: 1px solid lightgray; resize: both; min-width: 30em; } "
    style = "<style>" + scroll_style + formatter.get_style_defs() + "</style><br>"
    return mark_safe(style + response)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    readonly_fields = ['created', 'input_prettified', 'output_prettified']
    exclude = ['input', 'output']

    def input_prettified(self, instance):
        return pretty_json(instance, 'input')
    input_prettified.short_description = 'Input'

    def output_prettified(self, instance):
        return pretty_json(instance, 'output')
    output_prettified.short_description = 'Output'
