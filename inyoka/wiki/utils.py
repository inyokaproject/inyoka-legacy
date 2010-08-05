# -*- coding: utf-8 -*-
"""
    inyoka.wiki.utils
    ~~~~~~~~~~~~~~~~~

    Utilities for the wiki.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from werkzeug import abort
from inyoka.core.api import _, db, redirect_to
from inyoka.core.exceptions import NotFound


def urlify_page_name(name):
    return name.replace(u' ', u'_').strip(u'_')


def deurlify_page_name(name):
    return name.replace(u'_', u' ').strip(u' ')


def find_page(url_name, redirect_view=None, redirect_params=None,
              redirect=True, user=None, redirect_params_page_key='page',
              joinedload=True):
    """
    Find a page with a specific `url_name`.
    Return the page object on success, raise NotFound on failure, redirect to
    the correctly written page name if necessary.

    If the given url_name does not match the page's url_name (for example if
    `/wiki/maIn%20paGe` is requested), the user is redirected to the proper
    name (`/wiki/Main_Page`), unless `redirect` is set to False.
    To define where to redirect, specify `redirect_view` and `redirect_args`.

    :param url_name: The name of the page, in URL form (e.g. with _ not space)
    :param redirect_view: The name of the view to redirect to in case the page
        name is misspelt.  Required if redirect=True.
    :param redirect_params: A dict of url parameters for the redirect.  The
        page name is added to this at the key `page`. Optional.
    :param user: The requesting user.  If the user may view deleted pages,
        the page is shown even if it is deleted.  Optional. #TODO.
    :param redirect: Don't redirect to the canonical page url, but raise a
        NotFound exception if the page name doesn't match.
    :param redirect_params_page_key: Overwrite the default of `page` for the
        key which is used for the page name in redirect_params.
    :param joinedload: Also use the query to fetch the current revision and its
        text.
    """
    from inyoka.wiki.models import Page, Revision

    if redirect and redirect_view is None:
        raise TypeError('Required argument `redirect_view` missing')
    if redirect_params is None:
        redirect_params = {}

    name = deurlify_page_name(url_name)

    #TODO: only add deleted check if user may not view deleted pages
    try:
        page = Page.query.options(db.joinedload_all(Page.current_revision,
            Revision.text)).filter_by(deleted=False).filter_name(name).one()
    except db.NoResultFound:
        raise NotFound(_(u'No such page.'))

    if url_name != page.url_name:
        if redirect:
            redirect_params[redirect_params_page_key] = page.url_name
            abort(redirect_to(redirect_view, **redirect_params))
        else:
            raise NotFound(_(u'No such page.'))

    return page
