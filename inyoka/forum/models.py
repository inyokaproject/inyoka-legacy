# -*- coding: utf-8 -*-
"""
    inyoka.news.models
    ~~~~~~~~~~~~~~~~~~

    Database models for the Inyoka Forum application-

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from datetime import datetime
from werkzeug import cached_property
from inyoka.core.api import ctx, db, auth, markup, cache
from inyoka.core.auth.models import User
from inyoka.utils.text import gen_ascii_slug
import re

tag_re = re.compile(r'[\w-]{2,20}')

class QuestionMapperExtension(db.MapperExtension):
    """This MapperExtension ensures that questions are
    slugified properly.
    """

    def before_insert(self, mapper, connection, instance):
        instance.slug = db.find_next_increment(
            Question.slug, gen_ascii_slug(instance.title)
        )



question_tag = db.Table('forum_question_tag', db.metadata,
    db.Column('question_id', db.Integer, db.ForeignKey('forum_question.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('forum_tag.id'))
)

forum_tag = db.Table('forum_forum_tag', db.metadata,
    db.Column('forum_id', db.Integer, db.ForeignKey('forum_forum.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('forum_tag.id')),
    db.Column('propose', db.Boolean)
)


class Tag(db.Model):
    __tablename__ = 'forum_tag'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, index=True, unique=True)

    def __init__(self, name):
        if not tag_re.match(name):
            raise ValueErro('Invalid tag name "%s"' % name)
        self.name = name
    
    def get_url_values(self):
       return 'forum/questions', {'tags': self.name} 

       
class Forum(db.Model):
    __tablename__ = 'forum_forum'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), unique=True, index=True)
    description = db.Column(db.String(200), nullable=False, default=u'')
    parent_id = db.Column(db.Integer, db.ForeignKey('%s.id' % __tablename__),
            nullable=True, index=True)
    position = db.Column(db.Integer, nullable=False, default=0,
            index=True)

    subforums = db.relation('Forum', backref=db.backref('parent',
            remote_side='Forum.id'))
    tags = db.relation('Tag', secondary=forum_tag, backref='forums')

    def get_url_values(self):
       return 'forum/forum', {'slug': self.slug} 


class Question(db.Model):
    __tablename__ = 'forum_question'
    __mapper_args__ = {'extension': QuestionMapperExtension()}

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(160), nullable=False, index=True)
    sticky = db.Column(db.Boolean, default=False, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date_asked = db.Column(db.DateTime, nullable=False)
    
    tags = db.relation('Tag', secondary=question_tag, backref='questions')
    author = db.relation('User', backref='questions')

    @cached_property
    def summary(self):
        words = self.text.split()[:20]
        words.append(' ...')
        return u' '.join(words)

    def get_url_values(self):
       return 'forum/question', {'slug': self.slug} 


class Answer(db.Model):
    __tablename__ = 'forum_answer'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey(Question.id),
            nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    date_answered = db.Column(db.DateTime, nullable=False)
    text = db.Column(db.Text, nullable=False)

    question = db.relation('Question', backref='answers')
    author = db.relation('User', backref='answers')



class ForumSchemaController(db.ISchemaController):
    models = [Forum, Question, Answer, Tag, question_tag, forum_tag]
