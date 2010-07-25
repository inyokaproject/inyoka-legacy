# -*- coding: utf-8 -*-
"""
    inyoka.forum.models
    ~~~~~~~~~~~~~~~~~~~

    Database models for the Inyoka Forum application.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from collections import defaultdict
from werkzeug import cached_property
from inyoka.core.api import _, db, SerializableObject
from inyoka.core.models import Tag, TagCounterExtension
from inyoka.core.mixins import TextRendererMixin
from inyoka.core.auth.models import User
from inyoka.portal.api import ILatestContentProvider, ITaggableContentProvider
from inyoka.utils import confidence


question_tag = db.Table('forum_question_tag', db.metadata,
    db.Column('question_id', db.Integer, db.ForeignKey('forum_question.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey(Tag.id))
)

forum_tag = db.Table('forum_forum_tag', db.metadata,
    db.Column('forum_id', db.Integer, db.ForeignKey('forum_forum.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey(Tag.id)),
    db.Column('propose', db.Boolean)
)


class QuestionsContentProvider(ILatestContentProvider, ITaggableContentProvider):
    type = 'forum_questions'
    cache_key = 'forum/latest_questions'
    name = _('Questions')

    def get_latest_content(self):
        return Question.query.order_by(Question.date_active.desc()) \
            .options(db.noload('votes'), db.noload('author'))

    def get_taggable_content(self, tag):
        return Question.query.order_by(Question.score, Question.view_count) \
                             .filter(db.and_(
            question_tag.c.tag_id == tag.id,
            question_tag.c.question_id == Question.id
        )).options(db.noload('votes'), db.noload('author'))


class Forum(db.Model, SerializableObject):
    __tablename__ = 'forum_forum'
    __mapper_args__ = {'extension': db.SlugGenerator('slug', 'name')}

    #: serializer attributes
    object_type = 'forum.forum'
    public_fields = ('id', 'name', 'slug', 'description', 'tags'
                     'position', 'subforums')

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), unique=True, index=True)
    description = db.Column(db.String(200), nullable=False, default=u'')
    parent_id = db.Column(db.Integer, db.ForeignKey(id), nullable=True,
            index=True)
    position = db.Column(db.Integer, nullable=False, default=0,
            index=True)

    subforums = db.relationship('Forum',
            backref=db.backref('parent',remote_side=id),
            lazy='joined')
    tags = db.relationship(Tag, secondary=forum_tag, lazy='dynamic',
                           backref=db.backref('forums', lazy='dynamic'),
                           extension=TagCounterExtension())

    @cached_property
    def all_tags(self):
        """Return all tags for this forum, including those of the subforums."""
        tags = list(self.tags)
        for subforum in self.subforums:
            tags.extend(subforum.tags)
        return tags

    def get_url_values(self, **kwargs):
        kwargs.update({
            'forum': self.slug
        })
        return 'forum/questions', kwargs


class EntryVotesExtension(db.AttributeExtension):

    def append(self, state, vote, initiator):
        entry = state.obj()
        assert vote.score is not None, "vote.score mustn't be null!"
        entry.score = Entry.score + vote.score
        return vote

    def remove(self, state, vote, initiator):
        entry = state.obj()
        entry.score = Entry.score - vote.score


class VoteScoreExtension(db.AttributeExtension):
    active_history = True

    def set(self, state, value, oldvalue, initiator):
        vote = state.obj()
        if vote.entry is not None:
            vote.entry.score += -oldvalue + value
        return value


class EntryQuery(db.Query):
    """Entries can be sorted by their creation date, their last activity or the
    number of votes they have received."""


    @property
    def latest(self):
        """Sort the entries by their creation date."""
        return self.order_by(Entry.date_created.desc())

    @property
    def oldest(self):
        """Sort the entries by their creation date. The oldest entries are
        returned first."""
        return self.order_by(Entry.date_created.asc())

    @property
    def active(self):
        """Sort the entries by their last activity."""
        return self.order_by(Entry.date_active.desc())

    @property
    def votes(self):
        """Sort the entries by the score that they have received from votes."""
        return self.order_by(Entry.score.desc(), Entry.date_active.desc())



class Entry(db.Model, SerializableObject, TextRendererMixin):
    """The base class of a `Question` or `Answer`, which contains some general
    information about the author and the creation date, as well as the actual
    text and the votings."""

    __tablename__ = 'forum_entry'
    query = db.session.query_property(EntryQuery)

    #: Serializer attributes
    object_type = 'forum.entry'
    public_fields = ('entry_id', 'discriminator', 'author', 'date_created',
                     'date_active', 'score', 'text', 'votes')

    entry_id = db.Column(db.Integer, primary_key=True)
    discriminator = db.Column('type', db.String(12))
    author_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_active = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    score = db.Column(db.Integer, nullable=False, default=0)
    _text = db.Column('text', db.Text, nullable=False)
    rendered_text = db.Column(db.Text, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)

    author = db.relationship(User, lazy='joined', innerjoin=True)
    votes = db.relationship('Vote', backref='entry',
            extension=EntryVotesExtension())

    __mapper_args__ = {'polymorphic_on': discriminator}

    def touch(self):
        db.atomic_add(self, 'view_count', 1)

    def get_vote(self, user):
        return Vote.query.filter_by(user=user, entry=self).first()


class QuestionAnswersExtension(db.AttributeExtension):

    def append(self, state, answer, initiator):
        question = state.obj()
        db.atomic_add(question, 'answer_count', 1, primary_key_field='id')
        return answer

    def remove(self, state, answer, initiator):
        question = state.obj()
        db.atomic_add(question, 'answer_count', -1, primary_key_field='id')


class QuestionQuery(EntryQuery):
    """Adds special filter methods to the `EntryQuery` which are unique to
    questions."""

    def tagged(self, tags):
        """Filter questions by tags."""
        tag_ids = set(t.id for t in tags)
        return self.filter(db.and_(
            Question.id == question_tag.c.question_id,
            question_tag.c.tag_id.in_(tag_ids)))

    @cached_property
    def unanswered(self):
        return self.filter(Question.answer_count == 0)

    def forum(self, forum):
        """Filter questions by the tags of a forum."""
        return self.tagged(forum.all_tags)


class Question(Entry):
    """A `Question` is an `Entry` with a title, a slug and several tags."""
    __tablename__ = 'forum_question'
    __mapper_args__ = {
        'extension': db.SlugGenerator('slug', 'title'),
        'polymorphic_identity': u'question'
    }
    query = db.session.query_property(QuestionQuery)

    #: Serializer attributes
    object_type = 'forum.question'
    public_fields = ('entry_id', 'discriminator', 'author', 'date_created',
                     'date_active', 'score', 'text', 'votes', 'tags',
                     'id', 'title', 'slug')

    id = db.Column(db.Integer, db.ForeignKey(Entry.entry_id), primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), nullable=False, index=True)
    answer_count = db.Column(db.Integer, default=0)

    tags = db.relationship(Tag, secondary=question_tag, lazy='subquery',
                           backref=db.backref('questions', lazy='dynamic'),
                           extension=TagCounterExtension())

    @cached_property
    def popularity(self):
        pos = len([v for v in self.votes if v.score==1]) + self.answer_count
        neg = len([v for v in self.votes if v.score==-1])
        neg += len([a for a in self.answers if a.score<0])
        return confidence(pos, neg)

    def get_url_values(self, **kwargs):
        """Generates an URL for this question."""
        action = kwargs.get('action')
        if action == 'vote-up':
            return 'forum/vote', {'entry_id': self.id, 'action': 'up'}
        elif action == 'vote-down':
            return 'forum/vote', {'entry_id': self.id, 'action': 'down'}
        kwargs.update({
            'slug': self.slug
        })
        return 'forum/question', kwargs

    def __unicode__(self):
        return self.title


class Answer(Entry):
    __tablename__ = 'forum_answer'
    __mapper_args__ = {
        'polymorphic_identity': u'answer'
    }

    #: Serializer attributes
    object_type = 'forum.answer'
    public_fields = ('entry_id', 'discriminator', 'author', 'date_created',
                     'date_active', 'score', 'text', 'votes', 'question')

    id = db.Column(db.Integer, db.ForeignKey(Entry.entry_id), primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey(Question.id))

    question = db.relationship(Question,
            backref=db.backref('answers', extension=QuestionAnswersExtension()),
            primaryjoin=(question_id == Question.id))

    @cached_property
    def popularity(self):
        good_votes = len([v for v in self.votes if v.score==1])
        bad_votes = len([v for v in self.votes if v.score==-1])
        return confidence(good_votes, bad_votes)

    def get_url_values(self, **kwargs):
        """Generates an URL for this answer."""
        kwargs.update({
            '_anchor': 'answer-%s' % self.id
        })
        return self.question.get_url_values(**kwargs)


class VoteQuery(db.Query):

    def get_user_votes_on(self, user_id, entry_ids):
        if entry_ids:
            user_votes = defaultdict(int, dict(
                db.session.query(Vote.entry_id, Vote.score) \
                          .filter(db.and_(Vote.user_id==user_id,
                                          Vote.entry_id.in_(entry_ids)))
            ))
            return user_votes
        else:
            return {}


class Vote(db.Model, SerializableObject):
    """Users are able to vote for the entries in the forum they like.
    Additionally to the score (-1 or +1) users are able to mark the
    entry as one of their favorites."""
    __tablename__ = 'forum_vote'
    __table_args__ = (db.UniqueConstraint('entry_id', 'user_id'), {})

    query = db.session.query_property(VoteQuery)

    #: Serializer attributes
    object_type = 'forum.vote'
    public_fields = ('id', 'entry_id', 'user', 'score', 'favorite')

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('forum_entry.entry_id'),
            nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id),
            nullable=False)
    score = db.ColumnProperty(db.Column(db.Integer, nullable=False,
            default=0), extension=VoteScoreExtension())
    favorite = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship(User, backref='votes', lazy='joined', innerjoin=True)


class ForumSchemaController(db.ISchemaController):
    models = [Forum, Vote, question_tag, forum_tag,
              Entry, Question, Answer]
