# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..views import controllers
from .registry import Registry
from .router import Router

__all__ = 'Controller',


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


class Controller(Router, Registry, controllers.BaseController):
    """
    Controllers need the ability to:
    a) generate the URLs needed for the Backend
    b) generate the JIT (View, Inline, and Parent) Controller for each View
    """

    checks_class = None
    children = ()
    inlines = ()
    parent = None
    registrar = None
    force_backend_as_registrar = False

    parent_controller_class = controllers.ParentController
    child_controller_class = controllers.InlineController

    def __init__(self, parent, registrar=None):
        """
        Initializes a Model Controller for eventual registration as a Backend
        controller or a Controller sub-controller.
        :param parent: the Backend or Controller instance from which
            this Controller was created
        :param registrar: the Backend or Controller instance under which
            this Controller is to be registered
        """

        # only registered Controller will be aware of their registered parent
        from .backend import Backend
        if isinstance(parent, Backend):
            if registrar and registrar != parent:
                raise ValueError('"registrar" cannot be set to non-backend when'
                                 ' "backend" is also set.')
            self.registrar = backend = parent
        else:
            if not registrar:
                registrar = parent
            backend = parent.backend
            self.parent = parent
            self.registrar = registrar

        # this Controller will be its own registered controller
        super(Controller, self).__init__(backend=backend, controller=self)

    @property
    def is_root(self):
        return self.parent is None

    @property
    def is_local_root(self):
        return self.registrar is self.backend

    def check(self, **kwargs):
        return (self.checks_class().check(self, **kwargs)
                if self.checks_class else [])

    def get_parent_controller(self, view, kwargs):
        parent_controller = self.parent_controller_class(
            view=view, controller=self, kwargs=kwargs)
        parent_controller.__class__.__name__ =  str('{}ParentController'.format(
            parent_controller.controller.model.__name__
        ))
        return parent_controller

    def get_child_controller(self, view):
        child_controller = self.child_controller_class(view=view,
                                                       controller=self)
        return child_controller
