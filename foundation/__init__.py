# -*- coding: utf-8 -*-

from django.utils.module_loading import autodiscover_modules
from django.utils.version import get_version

from .decorators import backend_context, register
from .urls import *
from .views.controllers import StackedInline, TabularInline

VERSION = (0, 1, 0, 'alpha', 0)

__version__ = get_version(VERSION)

__all__ = ('Backend', 'Controller', 'StackedInline', 'TabularInline',
           'backends', 'get_backend', 'register')

def autodiscover():
    autodiscover_modules('controllers', register_to=get_backend())


default_app_config = 'foundation.apps.FoundationConfig'
