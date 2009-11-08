#-*- coding: utf-8 -*-
"""
    inyoka.paste.models
    ~~~~~~~~~~~~~~~~~~~

    Models for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from operator import attrgetter
from inyoka.core.api import db, href
from inyoka.utils.highlight import highlight_code


class Entry(db.Model):
    __tablename__ = 'paste_entry'

    id = db.Column(db.Integer, primary_key=True)
    _code = db.Column('code', db.Text, nullable=False)
    rendered_code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(30))
    author_id = db.Column(db.Integer, nullable=False) #TODO: ForeignKey!
    pub_date = db.Column(db.DateTime, default=db.func.now(), nullable=False)


    def __init__(self, code, language=None, author=None):
        self.language = language
        self.code = code

        self.author_id = author
#        if author is None:
#            self.author_id = local.get_request().user.id
#        elif isinstance(author, User):
#            self.author_id = author.id
#        else:
#            self.author = author

    def get_absolute_url(self, action='view', external=False):
        return href({
            'view': 'paste/view_paste',
            'raw': 'paste/raw_paste',
            }[action], id=self.id)

    def _set_code(self, code):
        if code is not self._code:
            self.rendered_code = highlight_code(code, self.language)
        self._code = code
    code = property(attrgetter('_code'), _set_code)
