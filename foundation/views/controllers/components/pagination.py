# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from backend.views.controllers.components.query import MultipleObjectMixin
from django.core.paginator import PageNotAnInteger, EmptyPage

__all__ = 'PaginatedQueryMixin',


class PaginatedQueryMixin(MultipleObjectMixin):

    def get_paginator(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        return self.paginator(queryset, per_page, orphans, allow_empty_first_page)

    def get_page(self, queryset, per_page, orphans=0, allow_empty_first_page=True):
        """
        Only for use on in-focus view.
        """
        paginator = self.get_paginator(queryset, per_page, orphans, allow_empty_first_page)
        page = self.request.GET.get('page', 1)
        try:
            page = paginator.page(page)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)
        return page

    def get_page_queryset(self, queryset, page):

        return queryset.filter(pk__in=[obj.pk for obj in page])
