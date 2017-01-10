# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ... import forms

class ControllerOptions(object):

    fields = None
    exclude = None
    fieldsets = None
    fk_name = None
    model = None
    ordering = None

    modelform_class = forms.ModelForm
    formset_class = forms.BaseModelFormSet
    formset_template = 'inline/tabular.html'

    # unevaluated
    raw_id_fields = ()

    filter_vertical = ()
    filter_horizontal = ()
    radio_fields = {}
    prepopulated_fields = {}
    formfield_overrides = {}
    readonly_fields = ()
    view_on_site = True  # TODO: remove see below
    show_full_result_count = True

    # can_delete = True
    show_change_link = False
    classes = None

    """
    
    '''
    list_display = ('__unicode__',)
    list_display_links = ()
    list_select_related = False
    list_per_page = 100
    list_max_show_all = 200
    list_editable = ()
    date_hierarchy = None
    save_as = False
    save_as_continue = True
    save_on_top = False
    paginator = Paginator
    inlines = []

    # Custom templates (designed to be over-ridden in subclasses)
    add_form_template = None
    change_form_template = None
    change_list_template = None
    delete_confirmation_template = None
    delete_selected_confirmation_template = None
    object_history_template = None

    checks_class = ModelAdminChecks
    """

    def update(self, attrs):
        for key in dir(self):
            if not key.startswith('_'):
                setattr(self, key, attrs.pop(key, getattr(self, key)))

    def __init__(self, attrs):
        super(ControllerOptions, self).__init__()
        self.update(attrs)

    def __getattribute__(self, name):
        """
        When an attribute is not found, attempt to pass-through to the Model
        Meta (Options).
        """

        super_getattr = super(ControllerOptions, self).__getattribute__
        model = super_getattr('model')
        try:
            return super_getattr(name)
        except AttributeError as e:
            try:
                return getattr(model._meta, name)
            except AttributeError:
                raise e
