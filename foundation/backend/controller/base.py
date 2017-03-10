# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.forms import MediaDefiningClass
from django.utils import six
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from .accessor import QueryMixin
from .resolver import Resolver

__all__ = 'BaseController',


class IncorrectLookupParameters(Exception):
    pass

# Defaults for formfield_overrides. ModelAdmin subclasses can change this
# by adding to ModelAdmin.formfield_overrides.

csrf_protect_m = method_decorator(csrf_protect)


class ControllerBase(MediaDefiningClass):

    def __new__(cls, name, bases, attrs):
        attrs['opts'] = ControllerOptions(attrs)
        return super(ControllerBase, cls).__new__(cls, name, bases, attrs)

    def __init__(self, name, bases, attrs):
        super(ControllerBase, self).__init__(name, bases, attrs)


@six.add_metaclass(ControllerBase)
class BaseController(QueryMixin, Resolver):
    """
    Functionality common to all Controllers:

    - Access to the Models as pass-though queries via QueryMixin.
    - Resolution of URLs based on naming conventions via Resolver.

    At the core of our Controller is the ability to resolve a URL pattern to a
    namespaced name given a set of kwargs.  This single component is safe for
    universal inclusion.
    """

    backend = None
    controller = None
    opts = None

    def __init__(self, backend, controller=None, **kwargs):
        """
        One thing all Controller share is the concept of a "registered"
        Controller.  For all but ViewController-instantiated InlineControllers,
        all Controller are guaranteed to have a registered counterpart.  For
        "registered" Controller, the counterpart is self.  For all others, is
        is resolvable in the underlying Registry and stored for convenience.
        For JIT InlineControllers, it may be None, which is a special case
        where that Controller's Options are not overwritten.
        :param registered_controller: an optional Controller instance
        """
        super(BaseController, self).__init__(**kwargs)
        self.backend = backend
        if controller:
            self.controller = controller
            self.opts = controller.opts

    def __getattribute__(self, name):
        """
        When a normal lookup fails, perform a secondary lookup in the attached
        Controller Options.
        """

        super_getattr = super(BaseController, self).__getattribute__

        # make sure we have an "opts"
        opts = super_getattr('opts')
        if not opts:
            raise ImproperlyConfigured('Controller should have opts by now.')

        try:
            return super_getattr(name)
        except AttributeError as e:
            try:
                return getattr(opts, name)
            except AttributeError:
                raise e
