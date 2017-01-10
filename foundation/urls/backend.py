# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from collections import OrderedDict
from django.conf import settings
from django.core.exceptions import ViewDoesNotExist
from django.forms.widgets import MediaDefiningClass
from django.urls.resolvers import LocaleRegexURLResolver, RegexURLResolver,\
    RegexURLPattern
from django.utils import six, translation
from django.utils.functional import cached_property

from .. import utils
from .registry import Registry, NotRegistered

__all__ = 'Backend', 'backends', 'get_backend'

logger = logging.getLogger(__name__)


def render(urlpatterns, base='', namespace=None, depth=0):

    views = {'patterns': {}, 'resolvers': {}}
    for p in urlpatterns:
        if isinstance(p, RegexURLPattern):
            try:
                if not p.name:
                    name = p.name
                elif namespace:
                    name = '{0}:{1}'.format(namespace, p.name)
                else:
                    name = p.name
                print('{}({}) {}'.format(('| '*(depth-1) + '|-') if depth else '', name, p.regex.pattern))
            except ViewDoesNotExist:
                continue
        elif isinstance(p, RegexURLResolver):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            if namespace and p.namespace:
                _namespace = '{0}:{1}'.format(namespace, p.namespace)
            else:
                _namespace = (p.namespace or namespace)
            print('{}({}) {}'.format(('| '*(depth-1) + '|-') if depth else '', _namespace, p.regex.pattern))
            if isinstance(p, LocaleRegexURLResolver):
                for langauge in settings.LANGUAGES:
                    with translation.override(langauge[0]):
                        render(patterns, base + p.regex.pattern, namespace=_namespace, depth=depth+1)
            else:
                render(patterns, base + p.regex.pattern, namespace=_namespace, depth=depth+1)

    return views


class Backend(six.with_metaclass(MediaDefiningClass, Registry)):
    '''
    # Text to put at the top of the admin index page.
    index_title = ugettext_lazy('Site administration')

    # URL for the "View site" link at the top of each admin page.
    site_url = '/'

    _empty_value_display = '-'

    login_form = None
    index_template = None
    app_index_template = None
    login_template = None
    logout_template = None
    password_change_template = None
    password_change_done_template = None
    '''

    create_permissions = False

    @property
    def site(self):
        """
        It may seem like this should need the request but the plan is to make
        a SiteBackend registry at some point... for now we will assume one site.
        """
        from django.contrib.sites.models import Site
        return Site.objects.get(pk=settings.SITE_ID)

    @property
    def site_title(self):
        return self.site.name

    def __init__(self, *args, **kwargs):
        '''
        self.name = name
        self._actions = {'delete_selected': actions.delete_selected}
        self._global_actions = self._actions.copy()
        '''
        super(Backend, self).__init__(*args, **kwargs)

    def register(self, model_or_iterable, controller_class=None, **options):
        """
        Registers the given model(s) with the given controller class.

        The model(s) should be Model classes, not instances.

        If a controller class isn't given, it will use Controller (the default
        options). If keyword arguments are given -- e.g., list_display --
        they'll be applied as options to the controller class.

        If a model is already registered, this will raise AlreadyRegistered.

        If a model is abstract, this will raise ImproperlyConfigured.
        """
        from django.db.models.base import ModelBase
        if not controller_class:
            from .controller import Controller
            controller_class = Controller
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            super(Backend, self).register(controller_class, model, **options)



    '''
    def add_action(self, action, name=None):
        """
        Register an action to be available globally.
        """
        name = name or action.__name__
        self._actions[name] = action
        self._global_actions[name] = action

    def disable_action(self, name):
        """
        Disable a globally-registered action. Raises KeyError for invalid names.
        """
        del self._actions[name]

    def get_action(self, name):
        """
        Explicitly get a registered global action whether it's enabled or
        not. Raises KeyError for invalid names.
        """
        return self._global_actions[name]

    @property
    def actions(self):
        """
        Get all the enabled actions as an iterable of (name, func).
        """
        return six.iteritems(self._actions)

    @property
    def empty_value_display(self):
        return self._empty_value_display

    @empty_value_display.setter
    def empty_value_display(self, empty_value_display):
        self._empty_value_display = empty_value_display

    def has_permission(self, request):
        """
        Returns True if the given HttpRequest has permission to view
        *at least one* page in the admin site.
        """
        return request.user.is_active and request.user.is_staff

    def check_dependencies(self):
        """
        Check that all things needed to run the admin have been correctly installed.

        The default implementation checks that admin and contenttypes apps are
        installed, as well as the auth context processor.
        """
        if not apps.is_installed('django.contrib.admin'):
            raise ImproperlyConfigured(
                "Put 'django.contrib.admin' in your INSTALLED_APPS "
                "setting in order to use the admin application.")
        if not apps.is_installed('django.contrib.contenttypes'):
            raise ImproperlyConfigured(
                "Put 'django.contrib.contenttypes' in your INSTALLED_APPS "
                "setting in order to use the admin application.")
        try:
            default_template_engine = Engine.get_default()
        except Exception:
            # Skip this non-critical check:
            # 1. if the user has a non-trivial TEMPLATES setting and Django
            #    can't find a default template engine
            # 2. if anything goes wrong while loading template engines, in
            #    order to avoid raising an exception from a confusing location
            # Catching ImproperlyConfigured suffices for 1. but 2. requires
            # catching all exceptions.
            pass
        else:
            if ('django.contrib.auth.context_processors.auth'
                    not in default_template_engine.context_processors):
                raise ImproperlyConfigured(
                    "Enable 'django.contrib.auth.context_processors.auth' "
                    "in your TEMPLATES setting in order to use the admin "
                    "application.")

    def admin_view(self, view, cacheable=False):
        """
        Decorator to create an admin view attached to this ``AdminSite``. This
        wraps the view and provides permission checking by calling
        ``self.has_permission``.

        You'll want to use this from within ``AdminSite.get_urls()``:

            class MyAdminSite(AdminSite):

                def get_urls(self):
                    from django.conf.urls import url

                    urls = super(MyAdminSite, self).get_urls()
                    urls += [
                        url(r'^my_view/$', self.admin_view(some_view))
                    ]
                    return urls

        By default, admin_views are marked non-cacheable using the
        ``never_cache`` decorator. If the view can be safely cached, set
        cacheable=True.
        """
        def inner(request, *args, **kwargs):
            if not self.has_permission(request):
                if request.path == reverse('admin:logout', current_app=self.name):
                    index_path = reverse('admin:index', current_app=self.name)
                    return HttpResponseRedirect(index_path)
                # Inner import to prevent django.contrib.admin (app) from
                # importing django.contrib.auth.models.User (unrelated model).
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(
                    request.get_full_path(),
                    reverse('admin:login', current_app=self.name)
                )
            return view(request, *args, **kwargs)
        if not cacheable:
            inner = never_cache(inner)
        # We add csrf_protect here so this function can be used as a utility
        # function for any view, without having to repeat 'csrf_protect'.
        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)
        return update_wrapper(inner, view)
    '''
    def get_urls(self, urlpatterns=None):
        """
        May be linked to ROOT_URLCONF directly or used to extend URLs from an
        existing urls.py file.  If it is extending patterns, auto-loading
        of urls.py files is disabled since that should have been done already.
        """
        existing_patterns = urlpatterns is not None
        if not existing_patterns:
            urlpatterns = []
        from django.conf.urls import url, include
        # Since this module gets imported in the application's root package,
        # it cannot import models from other applications at the module level,
        # and django.contrib.contenttypes.views imports ContentType.
        from django.contrib.contenttypes import views as contenttype_views

        def urlpatterns_in_namespace(urlpatterns, namespace):
            """ Given a list of url patterns and a namespace to look for,
            return a reference to the list of url patterns attached to the
            namespace (if found) or an empty list, and a boolean indicating
            whether the namespace already existed. """
            namespace_urlpatterns = []
            namespace_exists = False
            for resolver in urlpatterns:
                if getattr(resolver, 'namespace', None) == namespace:
                    namespace_urlpatterns = resolver.url_patterns
                    namespace_exists = True
                    break
            return namespace_urlpatterns, namespace_exists

        # URL auto-loader traverses all installed apps
        for app_config in utils.get_project_app_configs():
            app_namespace = getattr(app_config,
                                    'url_namespace',
                                    app_config.label)
            app_urlpatterns, app_namespace_exists = \
                urlpatterns_in_namespace(urlpatterns, app_namespace)

            # only auto-load app URLs if defined
            if not existing_patterns:
                # attempt to append from the app's URLs
                try:
                    app_urlpatterns.append(
                        url(r'', include(r'{}.urls'.format(app_config.name)))
                    )
                except ImportError:
                    pass

            for model in app_config.get_models():
                model_name = model._meta.model_name
                model_urlpatterns, model_namespace_exists = \
                    urlpatterns_in_namespace(app_urlpatterns, model_name)
                try:
                    controller = self.get_registered_controller(model)
                except NotRegistered:
                    controller = None
                else:
                    controller.url_app_namespace = app_namespace
                    model_urlpatterns.extend(controller.urls)

                # if the namespace exists we already appended/extended in place
                if model_urlpatterns and not model_namespace_exists:
                    if controller:
                        model_namespace = controller.model_namespace
                        model_prefix = controller.url_prefix
                    else:
                        model_namespace = model._meta.model_name
                        model_prefix = model._meta.verbose_name_plural.lower(
                            ).replace(' ', '-')
                    app_urlpatterns.append(
                        url(('^{}'.format(model_prefix)
                             if model_prefix else ''), include(
                                (model_urlpatterns, model_namespace)
                            )),
                    )

            # create an app index view if a named view is not provided
            # TODO: this is being added unconditionally right now... what we
            # really want to do is see if an index was specified (naturally or
            # explcitly) and only add this if we do not have one
            from .. import views
            AppIndex = getattr(app_config, 'AppIndexView', views.AppIndexView)
            app_index = AppIndex.as_view(app_config=app_config, backend=self)
            app_urlpatterns.append(url(r'^$', app_index, name='index'))


            # if the namespace exists we already appended/extended in place
            if app_urlpatterns and not app_namespace_exists:
                urlprefix = getattr(app_config, 'url_prefix', app_config.label)
                urlprefix = (r'^{}/'.format(urlprefix)
                             if urlprefix is not None and urlprefix != ''
                             else r'')
                urlpatterns.append(
                    url(urlprefix, include(
                        (app_urlpatterns, app_namespace)))
                )

        SiteIndex = getattr(self, 'SiteIndex', None)
        if SiteIndex:
            urlpatterns.append(
                url(r'^$',
                    SiteIndex.as_view(backend=self),
                    name='home')
            )

        # render(urlpatterns)

        return urlpatterns

    @cached_property
    def urls(self):
        return self.get_urls()  # , 'admin', 'admin'

    #@property
    #def media(self):
    #    return Media(css=self.css, js=self.js)

    def get_available_apps(self, request):
        """
        Returns a sorted list of all the installed apps that have been
        registered in this site.
        """

        user = request.user
        available_apps = OrderedDict()
        for app_config in sorted(utils.get_project_app_configs(),
                                 key=lambda app_config: app_config.label):
            app_label = None
            if getattr(app_config, 'is_public', False):
                app_label = app_config.label
            elif user.has_module_perms(app_config.label):
                app_label = app_config.label
            if app_label:
                available_apps[app_config] = '{}:index'.format(app_config.label)

        return available_apps

    def each_context(self, request):
        """
        Returns a dictionary of variables to put in the template context for
        *every* page in the admin site.
        """

        return {
            'site_title': self.site_title,
            # 'site_header': self.site_header,
            # 'site_url': self.site_url,
            # 'has_permission': self.has_permission(view),
            'available_apps': self.get_available_apps(request),
        }
    '''

    def i18n_javascript(self, request):
        """
        Displays the i18n JavaScript that the Django admin requires.

        This takes into account the USE_I18N setting. If it's set to False, the
        generated JavaScript will be leaner and faster.
        """
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog
        return javascript_catalog(request, packages=['django.conf', 'django.contrib.admin'])

    def _build_app_dict(self, request, label=None):
        """
        Builds the app dictionary. Takes an optional label parameters to filter
        models of a specific app.
        """
        app_dict = {}

        if label:
            models = {
                m: m_a for m, m_a in self._registry.items()
                if m._meta.app_label == label
            }
        else:
            models = self._registry

        for model, model_admin in models.items():
            app_label = model._meta.app_label

            has_module_perms = model_admin.has_module_permission(request)
            if not has_module_perms:
                if label:
                    raise PermissionDenied
                continue

            perms = model_admin.get_model_perms(request)

            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True not in perms.values():
                continue

            info = (app_label, model._meta.model_name)
            model_dict = {
                'name': capfirst(model._meta.verbose_name_plural),
                'object_name': model._meta.object_name,
                'perms': perms,
            }
            if perms.get('change'):
                try:
                    model_dict['admin_url'] = reverse('admin:%s_%s_changelist' % info, current_app=self.name)
                except NoReverseMatch:
                    pass
            if perms.get('add'):
                try:
                    model_dict['add_url'] = reverse('admin:%s_%s_add' % info, current_app=self.name)
                except NoReverseMatch:
                    pass

            if app_label in app_dict:
                app_dict[app_label]['models'].append(model_dict)
            else:
                app_dict[app_label] = {
                    'name': apps.get_app_config(app_label).verbose_name,
                    'app_label': app_label,
                    'app_url': reverse(
                        'admin:app_list',
                        kwargs={'app_label': app_label},
                        current_app=self.name,
                    ),
                    'has_module_perms': has_module_perms,
                    'models': [model_dict],
                }

        if label:
            return app_dict.get(label)
        return app_dict

    @never_cache
    def index(self, request, extra_context=None):
        """
        Displays the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        app_list = self.get_app_list(request)

        context = dict(
            self.each_context(request),
            title=self.index_title,
            app_list=app_list,
        )
        context.update(extra_context or {})

        request.current_app = self.name

        return TemplateResponse(request, self.index_template or
                                'admin/index.html', context)

    def app_index(self, request, app_label, extra_context=None):
        app_dict = self._build_app_dict(request, app_label)
        if not app_dict:
            raise Http404('The requested admin page does not exist.')
        # Sort the models alphabetically within each app.
        app_dict['models'].sort(key=lambda x: x['name'])
        app_name = apps.get_app_config(app_label).verbose_name
        context = dict(self.each_context(request),
            title=_('%(app)s administration') % {'app': app_name},
            app_list=[app_dict],
            app_label=app_label,
        )
        context.update(extra_context or {})

        request.current_app = self.name

        return TemplateResponse(request, self.app_index_template or [
            'admin/%s/app_index.html' % app_label,
            'admin/app_index.html'
        ], context)
    '''

# For now, a singleton list acting as a Backend Registry
backends = []

def get_backend():
    """
    Allow invocation of a Site elsewhere, fallback to a default Backend.
    TODO: We probably want a Site-Backend Registry.
    """
    global backends
    if not backends:
        backends.append(Backend())
    return backends[0]
