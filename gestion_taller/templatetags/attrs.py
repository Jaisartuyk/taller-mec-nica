from django import template

default_attrs = {
    'class': 'form-control',
    'autocomplete': 'off',
}

register = template.Library()

@register.filter(name='as_widget')
def as_widget(field, attrs=None):
    final_attrs = default_attrs.copy()
    if attrs:
        final_attrs.update(attrs)
    return field.as_widget(attrs=final_attrs)
