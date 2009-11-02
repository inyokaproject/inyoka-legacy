#-*- coding: utf-8 -*-
"""
    inyoka.core.http
    ~~~~~~~~~~~~~~~~

    This module implements various http helpers
    such as our own request and response classes.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from urlparse import urlparse, urljoin
from werkzeug import Request as BaseRequest, Response as BaseResponse, \
    redirect as _redirect, get_current_url, cached_property
from werkzeug.exceptions import BadRequest
from werkzeug.contrib.securecookie import SecureCookie
from inyoka.core.context import get_application, get_request
from inyoka.core.config import config


class Request(BaseRequest):

    def __init__(self, environ, application):
        self.application = application
        BaseRequest.__init__(self, environ)

    def build_absolute_uri(self):
        return get_current_url(self.environ)

    @cached_property
    def session(self):
        return SecureCookie.load_cookie(self, secret_key=config['cookie_secret'])


class Response(BaseResponse):
    default_mimetype = 'text/html'


class DirectResponse(Exception):

    def __init__(self, response):
        Exception.__init__(self, response)
        self.message = 'direct response %r' % response
        self.response = response


def check_external_url(url):
    """Check if a URL is on the application server and return the canonical
    URL (eg: it externalizes a passed in path)
    """
    base_url = config['base_domain_name']
    check_url = urljoin(base_url, url)
    if urlparse(base_url)[:2] != urlparse(check_url)[:2]:
        raise ValueError('The URL %s is not on the same server' % check_url)
    return check_url


def redirect(url, code=302, allow_external_redirect=False,
             force_scheme_change=False):
    """Return a redirect response.  Like Werkzeug's redirect but this
    one checks for external redirects too.  If a redirect to an external
    target was requested `BadRequest` is raised unless
    `allow_external_redirect` was explicitly set to `True`.

    Leading slashes are ignored which makes it unsuitable to redirect
    to URLs returned from `url_for` and others.  Use `redirect_to`
    to redirect to arbitrary endpoints or `_redirect` to redirect to
    unchecked resources outside the URL root.

    By default the redirect will not change the URL scheme of the current
    request (if there is one).  This behavior can be changed by setting
    the force_scheme_change to False.
    """
    # leading slashes are ignored, if we redirect to "/foo" or "foo"
    # does not matter, in both cases we want to be below our blog root.
    url = url.lstrip('/')

    if not allow_external_redirect:
        #: check if the url is on the same server
        #: and make it an external one
        try:
            url = check_external_url(url)
        except ValueError:
            raise BadRequest()

    # keep the current URL schema if we have an active request if we
    # should.  If https enforcement is set we suppose that the blog_url
    # is already set to an https value.
    request = get_request()
    if request and not force_scheme_change:
        url = request.environ['wsgi.url_scheme'] + ':' + url.split(':', 1)[1]

    return _redirect(url, code)


def redirect_to(*args, **kwargs):
    """Temporarily redirect to an URL rule."""
    # call werkzeug's redirect directly and not the redirect() function
    # from this module because it will strip leading slashes this function
    # returns and thus generate wrong redirects.
    return _redirect(url_for(*args, **kwargs))
