# -*- coding: utf-8 -*-
"""
    inyoka.core.routing
    ~~~~~~~~~~~~~~~~~~~

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
import sre_constants
from os.path import join
from inspect import getmembers, ismethod
from datetime import datetime
from werkzeug.routing import Submount, Subdomain, EndpointPrefix, \
    Rule, BaseConverter, ValidationError
from werkzeug import url_quote
from werkzeug.routing import Map as BaseMap
from inyoka import Interface
from inyoka.core.context import ctx
from inyoka.utils.decorators import make_decorator


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


class UrlMixin(object):
    """Mixin to make components able to implement own url rules."""

    #: The name of the component. Used for `href`.
    #: If `None` the url rules will be mounted to the root
    #: of the domain.
    name = None

    # The url objects, without Subdomain or EndpointPrefix,
    # inyoka takes care of it.
    url_rules = []

    # all rules are for build only, they never match
    build_only = False

    # if `True` we don't set a `EndpointPrefix`
    ignore_prefix = False

    special_prefix = None

    @classmethod
    def get_urlmap(cls):
        cls._endpoint_map = {}
        urls = []

        for comp in ctx.get_implementations(cls, instances=True):

            # check if url rules are for build only
            if comp.build_only:
                new_map = []
                for rule in comp.url_rules:
                    rule.build_only = True
                    new_map.append(rule)
                comp.url_rules = new_map

            name = comp.name
            if name:
                domain, mount = ctx.cfg['routing.urls.' + name].split(':', 1)
                if comp.ignore_prefix:
                    rules = comp.url_rules
                else:
                    if cls.special_prefix:
                        mount = join(special_prefix, mount)
                    rules = [EndpointPrefix('%s/' % name, comp.url_rules)]
                val = Subdomain(domain, [Submount(mount, rules)])
                urls.append(val)
            else:
                val = comp.url_rules
                urls.extend(val)

            cls._endpoint_map.setdefault(name, {}).update(
                comp.get_endpoint_map()
            )

        return urls

    def get_endpoint_map(self):
        """This method returns a dictionary with a mapping out of
        endpoint name -> bound method
        """

        def _predicate(value):
            return (ismethod(value) and
                    getattr(value, 'endpoint', None) is not None)

        members = tuple(x[1] for x in getmembers(self, _predicate))
        endpoint_map = dict((m.endpoint, m) for m in members)
        return endpoint_map


class IController(Interface, UrlMixin):
    """Interface for controllers.

    A controller is some kind of wrapper around differend
    methods handling various routing endpoints.

    Example controller implementation::

        class DummyController(IController):

            url_rules = [
                Rule('/', endpoint='index'),
                Rule('/news/<int:id>', endpoint='news')
            ]

            @view('index')
            def index_handler(self, request):
                return Response('index view')

            @view('news')
            def news_handler(self, request, id=None):
                return Response('News %s' % (id is None and 'index' or id))

    All “handlers” are registered with :func:`view` as endpoint handlers.

    """

    @classmethod
    def get_view(cls, endpoint):
        """Return the proper view for :attr:`endpoint`"""
        if '/' not in endpoint:
            # we assume that we have url_sections that point
            # to no name but to an empty string
            endpoint = '/' + endpoint
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

    register_view = staticmethod(make_decorator('endpoint'))


class IServiceProvider(Interface, UrlMixin):
    """Interface for services.

    A controller is some kind of wrapper around differend
    methods handling various routing endpoints.

    Example controller implementation::

        class DummyService(IServiceProvider):

            url_rules = [
                Rule('/', endpoint='get_dummy'),
                Rule('/<int:id>', endpoint='get_dummy'),
            ]

            @service('get_dummy')
            def get_dummy(self, id=None):
                # ...

    All “handlers” are registered with :func:`service` as endpoint handlers.

    """

    special_prefix = '_api'

    @classmethod
    def get_service(cls, endpoint):
        """Return the proper service for :attr:`endpoint`"""
        if '/' not in endpoint:
            # we assume that we have url_sections that point
            # to no name but to an empty string
            endpoint = '/' + endpoint
        parts = endpoint.split('/', 1)
        return cls._endpoint_map[parts[0]][parts[1]]

    register_service = staticmethod(make_decorator('endpoint'))

view = IController.register_view
service = IServiceProvider.register_service


def href(endpoint, **values):
    """Get the URL to an endpoint.  The keyword arguments provided are used
    as URL values.  Unknown URL values are used as keyword argument.
    Additionally there are some special keyword arguments:

    `_anchor`
        This string is used as URL anchor.

    `_external`
        If set to `True` the URL will be generated with the full server name
        and `http://` prefix.
    """
    _external = values.pop('_external', False)
    if hasattr(endpoint, 'get_url_values'):
        endpoint, values = endpoint.get_url_values(**values)
    _anchor = values.pop('_anchor', None)
    url = ctx.dispatcher.url_adapter.build(endpoint, values,
                                           force_external=_external)
    if _anchor is not None:
        url += '#' + url_quote(_anchor)
    return url


class DateConverter(BaseConverter):
    """
    Converter for the werkzeug routing that converts date strings in URLs to
    :class:`~datetime.date` objects.

    :param map:     A :class:`werkzeug.Map` instance passed by Werkzeug.
    :param format:  A string as expected by the strftime methods. Note that only
                    date related format characters such as m and d are supported.
    """
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
        super(DateConverter, self).__init__(map)

    def to_python(self, value):
        """Convert `value` to a python `date` type.

        Raises :exc:`ValidationError` if a invalid format is applied.
        :param value: A valid date for :meth:`~datetime.datetime.strptime`.
        """
        try:
            return datetime.strptime(value, self.format).date()
        except (ValueError, sre_constants.error):
            raise ValidationError('strptime failed. Either you supplied an '
                                  'invalid format string or invalid data.')

    def to_url(self, value):
        """Convert to a valid quoted URL value.

        Raises :exc:`ValidationError` if a invalid object is applied.
        :param value: A valid :class:`~datetime.date` instance.
        """
        try:
            return url_quote(value.strftime(self.format))
        except sre_constants.error:
            raise ValidationError('strftime failed. Format string seems to '
                                  'be invalid.')


class Map(BaseMap):
    """Our own map implementation for hooking in some custom converters"""
    import werkzeug.routing
    werkzeug.routing.DEFAULT_CONVERTERS['date'] = DateConverter
