# -*- coding: utf-8 -*-
"""
    inyoka.core.tasks
    ~~~~~~~~~~~~~~~~~

    Tasks of the inyoka core.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from celery.task import task, periodic_task, Task
from collections import defaultdict
from datetime import timedelta
from sqlalchemy.orm.exc import NoResultFound
from xappy import errors
from inyoka.i18n import _
from inyoka.context import ctx
from inyoka.core.auth.models import User
from inyoka.core.resource import IResourceManager
from inyoka.core.search import create_search_document, SearchIndex
from inyoka.core.subscriptions import SubscriptionAction
from inyoka.core.subscriptions.models import Subscription
from inyoka.core.templating import render_template
from inyoka.core.mail import send_email


def get_index_implementation(name):
    if isinstance(name, SearchIndex):
        return name
    return IResourceManager.get_search_indexes()[name]


@task(ignore_result=True)
def send_activation_mail(user_id, activation_url):
    user = User.query.get(user_id)
    website_title = ctx.cfg['website_title']
    send_email(_(u'Registration at %s') % website_title, render_template('mails/registration', {
        'user':             user,
        'activation_url':   activation_url,
        'website_title':    website_title,
    }), ctx.cfg['mail_address'], user.email)


@task(ignore_result=True)
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


class UpdateSearchTask(Task):
    """
    Add, update or delete a single item of the search index `index`.

    It's three parameters are:
        - The name of the search index the provider belongs to
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

    ignore_result = True
    countdown = 5

    def run(self, index, provider, doc_id, **kwargs):
        id = '%s-%s' % (provider, doc_id)
        index = get_index_implementation(index)

        try:
            # get the document data from the database
            obj = index.providers[provider].prepare([doc_id]).next()
        except StopIteration:
            # There's no document that matches the doc_id, abort
            return

        try:
            with index.indexer_connection() as indexer:
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
        except errors.XapianDatabaseLockError as exc:
            # Retry to index that object in 30 seconds
            self.retry([index, provider, doc_id], kwargs,
                       countdown=30, exc=exc)

@task
def search_query(index, q, page=1, **filters):
    """
    Searches for the query `q` in the search index `index`.

    It takes two optional arguments:
        - page: An integer determining the page
        - filters: A dictionary used for filtering the search results.
            Normally, results are filtert by equality with the value.
            You can change this behaviour by appending an ending to the key:
                - _list: Items match if all of the objects items match
                - _range: Items match if the value is between the first and the
                    second item of the object (usually a tuple)

            Values that are None, an empty list, tuple or string are ignored.

    It returns:
        - An amount of search result ids specified of the config value
          `search.count`
        - The estimated total count of search results
    """
    count = ctx.cfg['search.count']
    offset = (page - 1) * count
    with get_index_implementation(index).searcher_connection() as searcher:

        qry = searcher.query_parse(q, allow=get_index_implementation(index).direct_search_allowed)

        for key, val in filters.iteritems():
            # ignore senseless filters
            if val in (None, [], (), ''):
                continue

            # determine the type of query to execute
            key, type = key.split('_') if '_' in key else (key, None)

            if type == 'list':
                for v in val:
                    qry = searcher.query_filter(qry, searcher.query_field(key, v))
            elif type == 'range':
                qry = searcher.query_filter(qry, searcher.query_range(key, *val))
            else:
                qry = searcher.query_filter(qry, searcher.query_field(key, val))

        results = searcher.search(qry, offset, offset + count)
        total = results.matches_estimated
        ret = [result.id.split('-', 1) for result in results], total
        return ret


@task
def spell_correct(index, q):
    """
    Uses the search index `index` to return a spelling-corrected version of `q`.
    """
    with get_index_implementation(index).searcher_connection() as searcher:
        return searcher.spell_correct(q)


@task
def find_similar_docs(index, doc):
    """
    Find documents imilar to `doc` in the search index `index`.
    """
    with get_index_implementation(index).searcher_connection() as searcher:
        searcher = get_index_implementation(index).searcher
        results = searcher.search(searcher.query_similar(doc), 0, 10)
        # sometimes xapian returns the document itself; ignore this
        return [result.id.split('-', 1) for result in results if result.id != doc]


@periodic_task(run_every=timedelta(minutes=5))
def flush_indexer():
    """
    Flush all indexer connections.
    """
    logger = flush_indexer.get_logger()
    indexes = IResourceManager.get_search_indexes()
    for index in indexes.itervalues():
        with index.indexer_connection() as indexer:
            logger.debug('Flush search index: %s' % index.name)
            indexer.flush()
