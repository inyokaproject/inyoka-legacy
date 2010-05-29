# -*- coding: utf-8 -*-
"""
    inyoka.core.mixins
    ~~~~~~~~~~~~~~~~~~

    Various mixins for model extension.

    :copyright: 2010 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.markup.parser import parse, render
from inyoka.core.database import db
from inyoka.utils.diff3 import prepare_udiff, generate_udiff


class TextRendererMixin(object):
    """Mixin that renders the text to `rendered_text` when set.  Combine
    with a synonym column mapping for `text` to `_text`.
    """

    #: The function that is called to render the text
    text_renderer = lambda s, v: render(parse(v), format='html')
    #: If the text was rendered or not
    _rendered = False

    def __init__(self, *args, **kwargs):
        super(TextRendererMixin, self).__init__(*args, **kwargs)
        self._render()

    def _get_text(self):
        return self._text

    def _set_text(self, value):
        if self._text == value:
            # don't render the text if nothing changed
            return
        self._text = value
        self._render()

    def _render(self):
        """Render the entries text and save it to `rendered_text`."""
        if self._text is not None:
            self.rendered_text = unicode(self.text_renderer(self._text))

    text = property(_get_text, _set_text)
    del _get_text, _set_text


class RevisionedModelMixin(object):
    """A mixin to implement some common functions used on revisioned models.

    Some usage example::

        class PasteEntry(db.Model):
            __tablename__ = 'pastes'
            id = db.Column(db.Integer, primary_key=True)
            code = db.Column(db.Text)

    This is some standalone model.  Now that we want to make it implement
    revisions.  For that this mixin relies on one additional column.
    A ``parent_id`` that points to the paste entry model.

    Now we've done that our model looks like that::

        class PasteEntry(db.Model, RevisionedModelMixin):
            __tablename__ = 'pastes'
            id = db.Column(db.Integer, primary_key=True)
            code = db.Column(db.Text)
            parent_id = db.Column(db.Integer, db.ForeignKey('pastes.id'))

    With that you can use the tree additional functions
    :func:`~RevisionedModelMixin.resolve_root`,
    :func:`~RevisionedModelMixin.fetch_replies,
    :func:`~RevisionedModelMixin.compare_to`, see those documentation for
    more detail.
    """

    @classmethod
    def resolve_root(cls, identifier):
        """Find the root for a tree.

        :param identifier: The identifier a model should queried for.
                           We use ``cls.query.get`` to query the identifier.
        :returns: The very root object with no additional parent_id set.
        """
        obj = cls.query.get(identifier)
        if obj is None:
            return
        while obj.parent_id is not None:
            obj = obj.parent
        return obj

    def fetch_replies(self):
        """Get new replies for the model.

        Those replies only match the current active instance.
        """
        cls = self.__class__
        obj_list = cls.query.filter(db.and_(
            cls.parent_id.in_([self.id]),
        )).order_by(cls.id.desc()).all()

        return obj_list

    def compare_to(self, other, column, context_lines=4, template=False):
        """Compare the mdoel with another revision.

        :param other: The other model instance to compare with.
        :param column: A string what column to compare.
        :param context_lines: How many additional lines to show on the udiff.
        :param template: Either or not to prepare the udiff for templates use.
        """
        udiff = generate_udiff(
            old=getattr(self, column, u''),
            new=getattr(other, column, u''),
            old_title=unicode(self),
            new_title=unicode(other),
            context_lines=context_lines
        )

        if template:
            diff = prepare_udiff(udiff)
            return diff and diff[0] or None
        return udiff
