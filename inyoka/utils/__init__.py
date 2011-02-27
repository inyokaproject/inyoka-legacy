# -*- coding: utf-8 -*-
"""
    inyoka.utils
    ~~~~~~~~~~~~

    Various utilities.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""


def flatten_iterator(iter):
    """Flatten an iterator to one without any sub-elements"""
    for item in iter:
        if hasattr(item, '__iter__'):
            for sub in flatten_iterator(item):
                yield sub
        else:
            yield item


def flatten_list(iter):
    """Same as `flatten_iterator` but returns a list"""
    return list(flatten_iterator(iter))


def confirm_action(request, message, endpoint, **kwargs):
    """Flash a csrf protected "Are you sure?" form."""
    from inyoka.core.api import render_template, href
    from inyoka.core.forms import Form
    form = Form(request.form)
    if form.validate_on_submit():
        if 'cancel' in request.form:
            return False
        return True
    request.flash(render_template('utils/confirm.html', {
        'message': message,
        'form': form,
        'destination': href(endpoint, **kwargs)
    }), html=True)
    return False


class classproperty(object):
    """A mix of the built-in `classmethod` and `property`.

    This is used to achieve a property that is not bound to an instance.
    """

    def __init__(self, func, name=None):
        self.func = func
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__

    def __get__(self, desc, cls):
        value = self.func(cls)
        return value
