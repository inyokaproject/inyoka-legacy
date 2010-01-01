# -*- coding: utf-8 -*-
"""
    inyoka.core.serializer
    ~~~~~~~~~~~~~~~~~~~~~~

    Serializer framework commonly used for our services.

    This is mostly based on the API framework `Solace`_ uses.

    .. _Solace: http://opensource.plurk.com/Solace/

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import inspect
import simplejson
from xml.sax.saxutils import quoteattr
from datetime import datetime
from functools import update_wrapper
from babel import Locale, UnknownLocaleError
from werkzeug.exceptions import MethodNotAllowed, BadRequest
from werkzeug import Response, escape
from inyoka.core.context import ctx


XML_NS = 'http://ubuntuusers.de/inyoka/'

_escaped_newline_re = re.compile(r'(?:(?:\\r)?\\n)')


def _recursive_getattr(obj, key):
    for attr in key.split('.'):
        obj = getattr(obj, attr, None)
    return obj


def primitive(obj):
    """Convert a object to a primitive representation"""
    if isinstance(obj, SerializableObject):
        return obj.serializable_export()
    if isinstance(obj, datetime):
        return {'#type': 'inyoka.datetime',
                'value': obj.strftime('%Y-%m-%dT%H:%M:%SZ')}
    if isinstance(obj, Locale):
        return unicode(str(obj))
    if isinstance(obj, dict):
        return dict((key, primitive(value)) for key, value in obj.iteritems())
    if hasattr(obj, '__iter__'):
        return map(primitive, obj)
    return obj


class SerializableObject(object):
    """Baseclass for serializable objects."""

    #: the type of the object
    object_type = None

    #: subclasses have to provide this as a list
    public_fields = None

    def serializable_export(self):
        """Exports the object into a data structure ready to be
        serialized.  This is always a dict with string keys and
        the values are safe for pickeling.
        """
        result = {'#type': self.object_type}
        for key in self.public_fields:
            if isinstance(key, tuple):
                alias, key = key
            else:
                alias = key.rsplit('.', 1)[-1]
            value = _recursive_getattr(self, key)
            if callable(value):
                value = value()
            result[alias] = primitive(value)
        return result


def debug_dump(obj):
    """Dumps the data into a HTML page for debugging."""
    from inyoka.core.templating import render_template
    dump = _escaped_newline_re.sub('\n',
        simplejson.dumps(obj, ensure_ascii=False, indent=2))
    return render_template('_debug_dump.html', dict(dump=dump))


def dump_xml(obj):
    """Dumps data into a simple XML format."""
    def _dump(obj):
        if isinstance(obj, dict):
            d = dict(obj)
            obj_type = d.pop('#type', None)
            key = start = 'dict'
            if obj_type is not None:
                if obj_type.startswith('inyoka.'):
                    key = start = obj_type[7:]
                else:
                    start += ' type=%s' % quoteattr(obj_type)
            value = u''.join((u'<%s>%s</%s>' % (key, _dump(value), key)
                             for key, value in d.iteritems()))
            return u'<%s>%s</%s>' % (start, value, key)

        if isinstance(obj, (tuple, list)):
            def _item_dump(obj):
                if not isinstance(obj, (tuple, list, dict)):
                    return u'<item>%s</item>' % _dump(obj)
                return _dump(obj)
            return u'<list>%s</list>' % (u''.join(map(_item_dump, obj)))
        if isinstance(obj, bool):
            return obj and u'yes' or u'no'
        return escape(unicode(obj))

    return (
        u'<?xml version="1.0" encoding="utf-8"?>'
        u'<result xmlns="%s">%s</result>'
    ) % (XML_NS, _dump(obj))


def get_serializer(request_or_format):
    """Returns the serializer for the given API request."""
    def _search_for_accepted(req):
        best_match = (None, 0)
        for mimetype, serializer in _serializer_for_mimetypes.iteritems():
            quality = req.accept_mimetypes[mimetype]
            if quality > best_match[1]:
                best_match = (serializer, quality)

        if best_match[0] is None:
            raise BadRequest(_(u'Could not detect format.  You have to specify '
                               u'the format as query argument or in the accept '
                               u'HTTP header.'))

        # special case.  If the best match is not html and the quality of
        # text/html is the same as the best match, we prefer HTML.
        if best_match[0] != 'text/html' and \
           best_match[1] == req.accept_mimetypes['text/html']:
            return _serializer_map['debug']
        return _serializer_map[best_match[0]]

    if not isinstance(request_or_format, basestring):
        # we got no string so we assume that we got a proper
        # request object and search for the format.
        format = request_or_format.args.get('format')
        if format is not None:
            rv = _serializer_map.get(format)
            if rv is None:
                raise BadRequest(_(u'Unknown format "%s"') % escape(format))
            return rv
        return _search_for_accepted(request_or_format)

    # we got a string so we assume we got a proper format applied.
    return _serializer_map[request_or_format]


def send_service_response(request_or_format, result):
    """Sends the API response."""
    ro =primitive(result)
    serializer, mimetype = get_serializer(request_or_format)
    return Response(serializer(ro), mimetype=mimetype)


def list_api_methods():
    """List all API methods."""
    result = []
    rule_iter = ctx.dispatcher.url_map.iter_rules()
    for rule in rule_iter:
        if rule.build_only:
            continue
        view = ctx.dispatcher.get_view(rule.endpoint)
        if not getattr(view, 'is_service', False):
            continue
        handler = view.__name__
        if 'api/' in handler:
            handler = handler[handler.index('api/')+4:]
        result.append(dict(
            handler=handler,
            valid_methods=view.valid_methods,
            #TODO: support formatting the docs
            doc=(inspect.getdoc(view) or '').decode('utf-8'),
            url=unicode(rule)
        ))
    result.sort(key=lambda x: (x['url'], x['handler']))
    return result


_serializer_for_mimetypes = {
    'application/json':     'json',
    'application/xml':      'xml',
    'text/xml':             'xml',
    'text/html':            'debug',
}
_serializer_map = {
    'json':     (simplejson.dumps, 'application/json'),
    'xml':      (dump_xml, 'application/xml'),
    'debug':    (debug_dump, 'text/html'),
}
