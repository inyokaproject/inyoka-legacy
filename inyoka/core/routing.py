#-*- coding: utf-8 -*-
"""
    inyoka.core.routing
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import os
import re
import mimetypes
import sre_constants
from datetime import datetime
from sqlalchemy.exc import InvalidRequestError
from werkzeug.routing import Submount, Subdomain, EndpointPrefix, \
    Rule as BaseRule, BaseConverter, ValidationError
from werkzeug import append_slash_redirect, url_quote, wrap_file
from werkzeug.exceptions import NotFound, Forbidden
from inyoka import Component
from inyoka.core.api import get_application
from inyoka.core.environment import PACKAGE_CONTENTS
from inyoka.core.http import Response

#XXX: temporary to check if the routing stuff works until ente has finished
#     working on config ;-)
#from inyoka.core.config import config

_date_formatter_split_re = re.compile('(%.)')
_date_formatter_mapping = {
    'd': r'\d\d',
    'j': r'\d{3}',
    'm': r'\d\d',
    'U': r'\d\d',
    'w': r'\d',
    'W': r'\d\d',
    'y': r'\d\d',
    'Y': r'\d{4}',
    '%': r'%',
}

config = {
    'routing.portal.subdomain': '',
    'routing.portal.submount': '/',
    'routing.news.subdomain': 'news',
    'routing.news.submount': '/',
    'routing.calendar.subdomain': '',
    'routing.calendar.submount': '/calendar',
    'routing.static.subdomain': 'static',
    'routing.static.submount': '/',
    'routing.media.subdomain': 'media',
    'routing.media.submount': '/',
    'base_domain_name': 'inyoka.local:5000',
    'static_path': 'static',
    'media_path': 'media',
}


class IController(Component):
    # The name of the component. Used for `href`.
    name = ''

    # The url objects, without Subdomain or Endpointprefix,
    # inyoka takes care of it.
    url_rules = []

    @classmethod
    def get_urlmap(cls):
        cls._endpoint_map = {}

        urls = []

        for comp in cls.get_components():
            url_map = {}
            for method in dir(comp):
                method = getattr(comp, method)
                endpoint = getattr(method, 'endpoint', None)
                if endpoint is not None and endpoint not in url_map:
                    url_map[endpoint] = method

            urls.append(Subdomain(config['routing.%s.subdomain' % comp.name], [
                Submount(config.get('routing.%s.submount' % comp.name, '/'), [
                    EndpointPrefix('%s/' % comp.name, comp.url_rules)
                ])
            ]))

            cls._endpoint_map.setdefault(comp.name, {}).update(url_map)

        return urls

    @classmethod
    def get_view(cls, endpoint):
        if not '/' in endpoint:
            # we assume that we have url_sections that point
            # to no name but to an empty string
            endpoint = '/' + endpoint
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

    @staticmethod
    def register(endpoint_name):
        def wrap(func):
            func.endpoint = endpoint_name
            return func
        return wrap

register = IController.register


def href(endpoint, **values):
    adapter = get_application().url_adapter
    return adapter.build(endpoint, values, force_external=True)


class Rule(BaseRule):
    def __gt__(self, endpoint):
        self.endpoint = endpoint
        return self


class DateConverter(BaseConverter):
    def __init__(self, map, format='%Y/%m/%d'):
        # convert format string to a regex so that we don't have to be greedy.
        regex = []
        for part in _date_formatter_split_re.split(format):
            if part.startswith('%'):
                if part[1] not in _date_formatter_mapping:
                    raise ValidationError('formatter not allowed for dates: %s'
                                          % part)
                regex.append(_date_formatter_mapping[part[1]])
            else:
                regex.append(re.escape(part))
        self.regex = ''.join(regex)
        self.format = format

    def to_python(self, value):
        try:
            return datetime.strptime(value, self.format).date()
        except (ValueError, sre_constants.error):
            raise ValidationError('strptime failed. Either you supplied an '
                                  'invalid format string or invalid data.')

    def to_url(self, value):
        try:
            return url_quote(value.strftime(self.format))
        except sre_constants.error:
            raise ValidationError('strftime failed. Format string seems to '
                                  'be invalid.')


class ModelConverter(BaseConverter):
    """
    A converter for werkzeug routing that directly uses the input data to
    query the database. Returns a model, requires a model as input for
    building.

    :param model: Absolute import path to the model.
    :param column: Name of the column. Defaults to `id`.
    :param regex: Regex the url part has to match in order for the converter
                  to match. Required if `column` is set.
    """
    def __init__(self, model, column=None, regex=None):
        try:
            self.model = import_string(model)
        except ImportError:
            raise ValidationError

        #TODO: find out the regex from the column.
        #TODO: don't use `id` per default but use .get with the primary key.
        if column is None:
            self.column = 'id'
            self.regex = '\d+'
        elif regex is None:
            raise TypeError('If a column is specified, a regex is required.')
        else:
            self.column = column
            self.regex = regex

    def to_python(self, value):
        try:
            return session.query(self.model).filter_by(**{self.column: value}).one()
        except InvalidRequestError:
            raise ValidationError

    def to_url(self, value):
        return getattr(self.model, column)


class StaticDataProxy(object):
    def __init__(self, basedir, index=True):
        """
        Provides access to files on the local filesystem. It can be used like
        a usual view (e.g. supplied as endpoint for routing).

        :param basedir: Location of the directory files shall be searched in.
        :param index: Print a directory index when a directory is called.
        """
        if not os.path.isabs(basedir):
            basedir = os.path.join(PACKAGE_CONTENTS, basedir)
        if not basedir.endswith('/'):
            basedir += '/'
        self.basedir = basedir
        self.index = index

    def __call__(self, request, path):
        has_slash = path.endswith('/')

        print `path`
        path = [x for x in path.split('/') if x and x != '..']
        full_path = os.path.join(self.basedir, *path)
        print `full_path`

        mimetype = mimetypes.guess_type(full_path)[0] or 'text/plain'

        if has_slash and os.path.isfile(full_path):
            raise NotFound()
        if not has_slash and os.path.isdir(full_path):
            return append_slash_redirect(request.environ)

        try:
            f = wrap_file(request.environ, open(full_path, 'rb'))
        except IOError, e:
            if e.errno == 2:
                raise NotFound()
            if e.errno == 13:
                raise Forbidden()
            if e.errno == 21:
                if not self.index:
                    raise Forbidden()
                return Response('\n'.join(os.listdir(full_path)) + '\n',
                                mimetype='text/plain')
        headers = {
            'Content-Length': os.path.getsize(full_path),
        }
        return Response(f, mimetype=mimetype, direct_passthrough=True)


#TODO: this is just plain ugly, look at the definition below and think of
#      href('static/file', path='style/main.css')
#      - introduce a special handling in href? (but there might be other places
#        where there are problems)
#      - make StaticDataProxy behave like a rule/ruleset?
#      - other ideas?

class StaticController(IController):
    name = 'static'

    url_rules = [
        Rule('/<path:path>') > 'file',
        Rule('/', {'path': '/'}) > 'file',
    ]

    proxy = register('file')(StaticDataProxy(config['static_path']))


class MediaController(IController):
    name = 'media'

    url_rules = [
        Rule('/<path:path>') > 'file',
        Rule('/', {'path': '/'}) > 'file',
    ]

    proxy = register('file')(StaticDataProxy(config['media_path']))
