#-*- coding: utf-8 -*-
"""
    inyoka.core.http
    ~~~~~~~~~~~~~~~~

    This module implements various http helpers
    such as our own request and response classes.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import Request as BaseRequest, Response as BaseResponse, \
    CommonRequestDescriptorsMixin, CommonResponseDescriptorsMixin, \
    ResponseStreamMixin, redirect as _redirect
from werkzeug.exceptions import NotFound
from inyoka.core.api import get_application, get_request


class Request(BaseRequest):
    def __init__(self, environ, application):
        self.application = application
        BaseRequest.__init__(self, environ)


class Response(BaseResponse):
    default_mimetype = 'text/html'


def get_redirect_target(invalid_targets=(), request=None):
    """Check the request and get the redirect target if possible.
    If not this function returns just `None`.  The return value of this
    function is suitable to be passed to `_redirect`
    """
    if request is None:
        request = get_request()
    check_target = request.values.get('_redirect_target') or \
                   request.values.get('next') or \
                   request.referrer

    # if there is no information in either the form data
    # or the wsgi environment about a jump target we have
    # to use the target url
    if not check_target:
        return

    # otherwise drop the leading slash
    check_target = check_target.lstrip('/')

    root_url = request.url_root
    root_parts = urlparse(root_url)
    check_parts = urlparse(urljoin(root_url, check_target))

    # if the jump target is on a different server we probably have
    # a security problem and better try to use the target url.
    if blog_parts[:2] != check_parts[:2]:
        return

    # if the jump url is the same url as the current url we've had
    # a bad redirect before and use the target url to not create a
    # infinite redirect.
    current_parts = urlparse(urljoin(blog_url, request.path))
    if check_parts[:5] == current_parts[:5]:
        return

    # if the `check_target` is one of the invalid targets we also
    # fall back.
    for invalid in invalid_targets:
        if check_parts[:5] == urlparse(urljoin(blog_url, invalid))[:5]:
            return

    return check_target


def make_external_url(path):
    """Return an external url for the given path."""
    return urljoin(config['base_domain_name'], path.lstrip('/'))


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
            url = check_external_url(get_application(), url)
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
