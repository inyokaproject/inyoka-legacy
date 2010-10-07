# -*- coding: utf-8 -*-
"""
    inyoka.core.tasks
    ~~~~~~~~~~~~~~~~~

    Tasks of the inyoka core.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.decorators import task, periodic_task
from collections import defaultdict
from datetime import timedelta
from sqlalchemy.orm.exc import NoResultFound
from xappy import SearchConnection, IndexerConnection, UnprocessedDocument, \
    Field, errors
from inyoka.context import ctx
from inyoka.core.auth.models import User
from inyoka.core.resource import IResourceManager
from inyoka.core.search import create_search_document
from inyoka.core.subscriptions import SubscriptionAction
from inyoka.core.subscriptions.models import Subscription
from inyoka.core.templating import render_template
from inyoka.utils.mail import send_mail
from inyoka.core.api import _


# set up the connections to the search index
search_database = ctx.cfg['search.database']
indexer = IndexerConnection(search_database)
searcher = SearchConnection(search_database)
search_providers = IResourceManager.get_search_providers()


@task
def send_activation_mail(user_id, activation_url):
    user = User.query.get(user_id)
    website_title = ctx.cfg['website_title']
    send_mail(_(u'Registration at %s') % website_title, render_template('mails/registration', {
        'user':             user,
        'activation_url':   activation_url,
        'website_title':    website_title,
    }), ctx.cfg['mail_address'], user.email)


@task
def send_notifications(object, action_name, subscriptions):
    action = SubscriptionAction.by_name(action_name)
    if action is None:
        raise ValueError('no action found with %r' % action_name)
    notifications = defaultdict(lambda: defaultdict(list))

    for s in subscriptions:
        try:
            s = Subscription.query.get(s)
        except NoResultFound:
            raise ValueError('no subscription found with id %r' % s)
        notifications[s.user][s.type.name].append(s.subject)

    for user in notifications:
        action.notify(user, object, notifications[user])


@task
def update_search_index(provider, doc_id):
    """
    Add, update or delete a single item of the search index.

    It's two parameters are:
        - The name of the provider the document belongs to
        - The document id

    It tries to fetch the document's data from the database. If this fails,
    the corresponding search index entry (if there's one) will be deleted.
    Otherwise the existing entry will be updated or a new one will be created.

    Note that for performance reasons the data is not directly written to the
    search index but with a delay of some minutes (the periodic task
    `flush_indexer` is responsible for this). As a result it may take some
    time for your document to appear when searching.
    """
    id = '%s-%s' % (provider, doc_id)
    # get the document data from the database
    obj = search_providers[provider].prepare([doc_id]).next()

    if obj is None:
        # the document was deleted in the database, delete the search index
        # entry too
        indexer.delete(id)
    else:
        doc = create_search_document(id, obj)
        try:
            # try to create a new search entry
            indexer.add(doc)
        except errors.IndexerError:
            # there's already an exising one, replace it
            indexer.replace(doc)

    # XXX: THIS IS ONLY FOR TESTING!!! REMOVE IT!!!
    indexer.flush()


@task
def search_query(q, page):
    """
    Searches for the query `q` in the search index.

    It returns:
        - An amount of search result ids specified of the config value
          `search.count`
        - The estimated total count of search results
    """
    count = ctx.cfg['search.count']
    offset = (page - 1) * count
    query = searcher.query_parse(q, allow=['tag', 'author'])
    results = searcher.search(query, offset, offset + count)
    total = results.matches_estimated
    return [result.id.split('-', 1) for result in results], total


@task
def spell_correct(q):
    """
    Uses the search index to return a spelling-corrected version of `q`.
    """
    return searcher.spell_correct(q)


@periodic_task(run_every=timedelta(minutes=5))
def flush_indexer():
    indexer.flush()
    searcher.reopen()
