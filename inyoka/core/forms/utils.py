# -*- coding: utf-8 -*-
"""
    inyoka.core.forms.utils
    ~~~~~~~~~~~~~~~~~~~~~~~

    Various utilities for the Inyoka form system, based on bureaucracy.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from functools import partial
from bureaucracy.utils import *


def _get_attrs(obj):
    not_underscore = partial(filter, lambda k: not k.startswith('_'))
    attrs = (attr.key for attr in type(obj)._sa_class_manager.attributes)
    return not_underscore(attrs)


def model_to_dict(instance, fields=None, exclude=None):
    """Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    Example Usage::

        form = ContactForm(model_to_dict(user))

    :param fields: This is an optional list of field names.  If provided only
                   the named fields will be included in the returned dict.
    :param exclude:  This is an optional list of field names.  If provided
                     the named fields will be excluded from the returned dict.
    """
    data = {}

    for key in _get_attrs(instance):
        if fields and key not in fields:
            continue
        if exclude and key in exclude:
            continue

        data[key] = getattr(instance, key)
    return data


def update_model(instance, form, includes=None):
    """Update a model with the applied `form`.

    Example Usage::

        if request.method == 'POST' and form.validate(request.form):
            user = update_model(user, form)
            db.session.update(user)
            db.session.commit()

    If `includes` is applied only these fields will be updated.  This function
    fails silently if you applied the wrong include keys or tried to update
    not existing attributes.
    """
    attrs = _get_attrs(instance)
    if not isinstance(form, dict):
        # assume we work with a form instance instead of a dicct
        form = form.data

    for key, value in form.iteritems():
        if key not in attrs:
            continue
        if includes and key not in includes:
            continue

        setattr(instance, key, value)
    return instance
