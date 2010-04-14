# -*- coding: utf-8 -*-
"""
    inyoka.utils.html
    ~~~~~~~~~~~~~~~~~

    Various html utilities

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from __future__ import division
from xml.sax.saxutils import quoteattr
from werkzeug import escape as wzescape


#: set of tags that don't want child elements.
EMPTY_TAGS = set(['br', 'img', 'area', 'hr', 'param', 'meta', 'link', 'base',
                  'input', 'embed', 'col', 'frame', 'spacer'])


def escape(s, quote=True):
    """Like `werkzeug.escape`, but with `quote` set to True per default."""
    return wzescape(s, quote)


def _build_html_tag(tag, attrs):
    """Build an HTML opening tag."""
    attrs = u' '.join(iter(
        u'%s=%s' % (k, quoteattr(unicode(v)))
        for k, v in attrs.iteritems()
        if v is not None
    ))
    return u'<%s%s%s>' % (
        tag, attrs and ' ' + attrs or '',
        tag in EMPTY_TAGS and ' /' or ''
    ), tag not in EMPTY_TAGS and u'</%s>' % tag or u''


def build_html_tag(tag, class_=None, classes=None, **attrs):
    """Build an HTML opening tag."""
    if classes:
        class_ = u' '.join(x for x in classes if x)
    if class_:
        attrs['class'] = class_
    return _build_html_tag(tag, attrs)[0]
