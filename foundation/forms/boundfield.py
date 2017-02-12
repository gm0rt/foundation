from django.forms import boundfield, fields
from django.utils import six
from django.utils.encoding import force_text, smart_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields.reverse_related import ManyToManyRel
from django.template.defaultfilters import linebreaksbr
from django.utils.deprecation import RemovedInDjango20Warning
import warnings

from ..utils import lookup_field, display_for_field

__all__ = ('BoundField',)


class BoundField(boundfield.BoundField):
    """ Based on django.contrib.admin.helpers 1.10 """
    is_first = True
    is_readonly = False
    controller = None

    @property
    def empty_value_display(self):
        return self.controller.get_empty_value_display() \
            if self.controller else ''

    @property
    def is_checkbox(self):
        return isinstance(self.field.widget, fields.CheckboxInput)

    def label_tag(self, contents=None, attrs=None, label_suffix=None):
        classes = []
        if not contents:
            contents = mark_safe(conditional_escape(force_text(self.label)))
        if self.is_checkbox:
            classes.append('vCheckboxLabel')

        if self.field.required:
            classes.append('required')
        if not self.is_first:
            classes.append('inline')
        attrs = {'class': ' '.join(classes)} if classes else {}
        # checkboxes should not have a label suffix as the checkbox appears
        # to the left of the label.
        return super(BoundField, self).label_tag(
            contents=contents, attrs=attrs,
            label_suffix='' if self.is_checkbox else None
        )

    def contents(self):
        from django.contrib.admin.templatetags.admin_list import _boolean_icon
        field_name, obj, controller = self.name, self.form.instance, self.controller
        try:
            f, attr, value = lookup_field(field_name, obj, controller)
        except (AttributeError, ValueError, ObjectDoesNotExist):
            result_repr = self.empty_value_display
        else:
            if f is None:
                boolean = getattr(attr, "boolean", False)
                if boolean:
                    result_repr = _boolean_icon(value)
                else:
                    if hasattr(value, "__html__"):
                        result_repr = value
                    else:
                        result_repr = smart_text(value)
                        if getattr(attr, "allow_tags", False):
                            warnings.warn(
                                "Deprecated allow_tags attribute used on %s. "
                                "Use django.utils.safestring.format_html(), "
                                "format_html_join(), or mark_safe() instead." % attr,
                                RemovedInDjango20Warning
                            )
                            result_repr = mark_safe(value)
                        else:
                            result_repr = linebreaksbr(result_repr)
            else:
                if isinstance(f.remote_field, ManyToManyRel) and value is not None:
                    result_repr = ", ".join(map(six.text_type, value.all()))
                else:
                    result_repr = display_for_field(value, f, self.empty_value_display)
                result_repr = linebreaksbr(result_repr)
        return conditional_escape(result_repr)

    """
    Clashes with errors in Fieldline
    @property
    def errors(self):
        return mark_safe(super(BoundField, self).errors.as_ul())
    """


"""
Integrate these behaviors conditionally above:
class ReadonlyBoundField(BoundField):
    def __init__(self, form, field, is_first, model_admin=None):
        # Make self.field look a little bit like a field. This means that
        # {{ field.name }} must be a useful class name to identify the field.
        # For convenience, store other field-related data here too.
        if callable(field):
            class_name = field.__name__ if field.__name__ != '<lambda>' else ''
        else:
            class_name = field

        if form._meta.labels and class_name in form._meta.labels:
            label = form._meta.labels[class_name]
        else:
            label = label_for_field(field, form._meta.model, model_admin)

        if form._meta.help_texts and class_name in form._meta.help_texts:
            help_text = form._meta.help_texts[class_name]
        else:
            help_text = help_text_for_field(class_name, form._meta.model)

        # make this looks like a Field
        self.name = class_name
        self.label = label
        self.help_text = help_text
        self.field = field

        self.form = form
        self.model_admin = model_admin
        self.is_first = is_first
        self.is_checkbox = False
        self.is_readonly = True
        self.empty_value_display = model_admin.get_empty_value_display()

    def label_tag(self):
        attrs = {}
        if not self.is_first:
            attrs["class"] = "inline"
        label = self.field['label']
        return format_html('<label{}>{}:</label>',
                           flatatt(attrs),
                           capfirst(force_text(label)))


"""
