#-*- coding: utf-8 -*-
"""
    inyoka.paste.models
    ~~~~~~~~~~~~~~~~~~~

    Models for the paste app.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.api import db, href


class Entry(db.Model):
    __tablename__ = 'paste_entry'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(30))
    author_id = db.Column(db.Integer, nullable=False) #TODO: ForeignKey!
    pub_date = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    def get_absolute_url(self):
        return href('paste/view_paste', id=self.id)

#XXX: just to make the test pass. actually that should happen automatically???
db.metadata.tables[Entry.__tablename__] = Entry.__table__
