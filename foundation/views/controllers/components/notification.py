# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.utils.encoding import force_text
from django.utils.translation import override as translation_override


__all__ = 'NotificationMixin',


class NotificationMixin(object):
    """ NOT YET INTEGRATED """

    @translation_override(None)
    def construct_change_message(self, request, form, formsets, add=False):
        """
        Construct a JSON structure describing changes from a changed object.
        Translations are deactivated so that strings are stored untranslated.
        Translation happens later on LogEntry access.
        """
        change_message = []
        if add:
            change_message.append({'added': {}})
        elif form.changed_data:
            change_message.append({'changed': {'fields': form.changed_data}})

        if formsets:
            for formset in formsets:
                for added_object in formset.new_objects:
                    change_message.append({
                        'added': {
                            'name': force_text(added_object._meta.verbose_name),
                            'object': force_text(added_object),
                        }
                    })
                for changed_object, changed_fields in formset.changed_objects:
                    change_message.append({
                        'changed': {
                            'name': force_text(changed_object._meta.verbose_name),
                            'object': force_text(changed_object),
                            'fields': changed_fields,
                        }
                    })
                for deleted_object in formset.deleted_objects:
                    change_message.append({
                        'deleted': {
                            'name': force_text(deleted_object._meta.verbose_name),
                            'object': force_text(deleted_object),
                        }
                    })
        return change_message

    def message_user(self, request, message, level=messages.INFO, extra_tags='',
                     fail_silently=False):
        """
        Send a message to the user. The default implementation
        posts a message using the django.contrib.messages backend.

        Exposes almost the same API as messages.add_message(), but accepts the
        positional arguments in a different order to maintain backwards
        compatibility. For convenience, it accepts the `level` argument as
        a string rather than the usual level number.
        """
        if not isinstance(level, int):
            # attempt to get the level if passed a string
            try:
                level = getattr(messages.constants, level.upper())
            except AttributeError:
                levels = messages.constants.DEFAULT_TAGS.values()
                levels_repr = ', '.join('`%s`' % l for l in levels)
                raise ValueError(
                    'Bad message level string: `%s`. Possible values are: %s'
                    % (level, levels_repr)
                )

        messages.add_message(request, level, message, extra_tags=extra_tags, fail_silently=fail_silently)
