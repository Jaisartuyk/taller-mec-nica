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

@register.filter(name='add_class')
def add_class(field, css):
    # Recupera attrs actuales si existen
    attrs = field.field.widget.attrs.copy()
    # Obtiene la(s) clase(s) existente(s) y agrega la nueva
    existing_classes = attrs.get('class', '')
    classes = f"{existing_classes} {css}".strip()
    attrs['class'] = classes
    return field.as_widget(attrs=attrs)