# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from django.db import models
from django.utils.http import urlencode

from ..forms.models import ALL_VAR, PAGE_VAR, ERROR_FLAG
from .controllers.components import PaginatedQueryMixin, IS_POPUP_VAR, TO_FIELD_VAR
from .edit import MultipleObjectFormsetMixin
from .list import ListView

__all__ = 'ChangeListView',


class ChangeListView(MultipleObjectFormsetMixin, PaginatedQueryMixin, ListView):

    mode = 'list'
    mode_title = 'all'
    template_name = 'change_list.html'

    # get from controller
    # self.list_display = list_display
    # self.list_display_links = list_display_links
    # self.list_filter = list_filter
    # self.date_hierarchy = date_hierarchy
    # self.search_fields = search_fields
    # self.list_select_related = list_select_related
    # self.list_per_page = list_per_page
    # self.list_max_show_all = list_max_show_all
    # self.preserved_filters = controller.get_preserved_filters(view)

    # Get search parameters from the query string.

    def handle_common(self, handler, request, *args, **kwargs):
        handler = super(ChangeListView, self).handle_common(handler, request, *args, **kwargs)

        # carried over from change list processing
        try:
            self.page_num = int(request.GET.get(PAGE_VAR, 0))
        except ValueError:
            self.page_num = 0
        self.show_all = ALL_VAR in request.GET
        self.is_popup = IS_POPUP_VAR in request.GET
        to_field = request.GET.get(TO_FIELD_VAR)
        #if to_field and not model_admin.to_field_allowed(request, to_field):
        #    raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)
        self.to_field = to_field
        self.params = dict(request.GET.items())
        if PAGE_VAR in self.params:
            del self.params[PAGE_VAR]
        if ERROR_FLAG in self.params:
            del self.params[ERROR_FLAG]

        if self.is_popup:
            self.list_editable = ()
        # self.query = request.GET.get(SEARCH_VAR, '')

        # auth-constrained queryset
        self.root_queryset = self.get_queryset()

        # get paginated page
        self.page = self.get_page(self.root_queryset, self.list_per_page)

        # get paginated queryset
        self.queryset = self.get_page_queryset(self.root_queryset, self.page)

        # parent_obj will be needed for non-local roots since they will use FK
        # to build out an inline formset and provide add/edit inline
        parent_obj = (self.parent.get_object()
                      if not self.controller.is_local_root
                      else None)

        # feed the par-reduced queryset to formset, which will in turn FK
        # constrain it, as applicable
        self.formset = self.get_formset(
            obj=parent_obj,
            queryset=self.queryset
        )

        # Get search parameters from the query string.
        #self.get_results(view)
        #if self.is_popup:
        #    title = ugettext('Select %s')
        #else:
        #    title = ugettext('Select %s to change')
        #self.title = title % force_text(self.opts.verbose_name)
        #self.pk_attname = self.lookup_opts.pk.attname

        return handler

    def get_context_data(self, **kwargs):
        kwargs.update(
            formset=self.formset,
        )
        return super(ChangeListView, self).get_context_data(**kwargs)
