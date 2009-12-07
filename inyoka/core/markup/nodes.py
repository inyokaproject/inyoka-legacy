# -*- coding: utf-8 -*-
"""
    inyoka.core.markup.nodes
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The nodes for the parse tree of the parser.

    Nodes also provide the formatting methods to generate HTML, docbook or
    whatever.  If you want to add new formatting methods don't forget to
    register it in the dispatching functions.  Also in the other modules
    and especially in macro and parser baseclasses.

    All nodes except of the base nodes have to have a `__dict__`.  This is
    enforced because dict-less objects cannot be replaced in place which is
    a required by the `DeferredNode`.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from inyoka.core.markup.machine import NodeCompiler, NodeRenderer, \
    NodeQueryInterface
from inyoka.utils.html import build_html_tag, escape
from inyoka.utils.debug import debug_repr


class BaseNode(object):
    """
    internal Baseclass for all nodes.  Usually you inherit from `Node`
    that implements the renderer and compiler interface but sometimes
    it can be useful to have a plain node.
    """
    __slots__ = ()

    #: if the current node is a document node (outermost one) this is
    #: true. So far there is only one node which is called "document",
    #: in the future a node "Page" could be added that has layout information
    #: for printing.
    is_document = False

    #: if this node contains child nodes (has a children attribute)
    #: this is true. Also containers are usually subclasses of the
    #: `Container` node but that's not a requirement.
    is_container = False

    #: this is true if the element is a block tag. Block tags can contain
    #: paragraphs and inline elements. All containers that are not block
    #: tags are inline tags and can only contain inline tags.
    is_block_tag = False

    #: this is true if the element is a paragraph node
    is_paragraph = False

    #: this is true of this element can contain paragraphs.
    allows_paragraphs = False

    #: True if this is a text node
    is_text_node = False

    #: This is true of the node contains raw data. Raw data is data that is
    #: never processed by a transformer. For example if you don't want
    #: to have typographical quotes this is the flag to alter. Use this only
    #: if the contents of that node matter (sourcecode etc.)
    is_raw = False

    #: the value of the node as text
    text = u''

    #: whether the node is just for creating line breaks
    is_linebreak_node = False

    def __eq__(self, other):
        return self.__class__ is other.__class__ and \
               self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    __repr__ = debug_repr


class DeferredNode(BaseNode):
    """
    Special node with a `become()` function that can be used to replace
    this node in place with another one.
    """

    def __init__(self, node):
        self.node = node

    @property
    def is_block_tag(self):
        return self.node.is_block_tag

    def become(self, other):
        self.__class__ = other.__class__
        self.__dict__ = other.__dict__


class Node(BaseNode, NodeRenderer, NodeCompiler, NodeQueryInterface):
    """
    The public baseclass for all nodes.  It implements the `NodeRenderer`
    and `NodeCompiler` and sets some basic attributes every node must have.
    """

    def prepare(self, format):
        """
        Public interface to the rendering functions.  This is only a
        dispatcher on the basenode, the preparation methods always
        *have* to call themselves with their internal name for
        performance reasons.  The `prepare()` method itself is only
        used by the renderer and node compiler.
        """
        return {
            'html':     self.prepare_html,
            'docbook':  self.prepare_docbook
        }[format]()

    def prepare_html(self):
        """
        The AST itself never survives the parsing process.  At the end
        of parsing `prepare_html` (or `prepare_docbook` if one wants to
        implement that) is called and the iterator returned is converted
        into an active cacheable object (pickled if it contains dynamic
        rendering parts, otherwise dumped as utf-8 string).
        """
        return iter(())

    def prepare_docbook(self):
        """
        The prepare function for docbook.
        """
        return iter(())


class Text(Node):
    """
    Represents text.
    """

    is_text_node = True
    allowed_in_signatures = True

    def __init__(self, text=u''):
        self.text = text

    def prepare_html(self):
        yield escape(self.text)

    def prepare_docbook(self):
        yield escape(self.text)


class Container(Node):
    """
    A basic node with children.
    """
    is_container = True

    #: this is true if the container is plain (unstyled)
    is_plain = True

    def __init__(self, children=None):
        if children is None:
            children = []
        self.children = children

    def get_fragment_nodes(self, inline_paragraph=False):
        """
        This function returns a tuple in the form ``(children, is_block)``.
        If the container holds exactly one unstyled paragraph the elements
        in that paragraph are used if `inline_paragraph` is set to `True`.

        The `is_block` item in the tuple is `True` if the children returned
        required a block tag as container.
        """
        if inline_paragraph:
            if len(self.children) == 1 and self.children[0].is_paragraph and \
               self.children[0].is_plain:
                return self.children[0].children, False
        is_block_tag = False
        for child in self.children:
            if child.is_block_tag:
                is_block_tag = True
                break
        return self.children, is_block_tag

    @property
    def is_block_tag(self):
        return self.get_fragment_nodes()[1]

    @property
    def text(self):
        return u''.join(x.text for x in self.children)

    def prepare_html(self):
        for child in self.children:
            for item in child.prepare_html():
                yield item

    def prepare_docbook(self):
        for child in self.children:
            for item in child.prepare_docbook():
                yield item


class Element(Container):
    """
    Baseclass for elements.
    """

    def __init__(self, children=None, id=None, style=None, class_=None):
        Container.__init__(self, children)
        self.id = id
        self.style = style
        self.class_ = class_

    @property
    def is_plain(self):
        return self.id is self.style is self.class_ is None

    @property
    def text(self):
        rv = Container.text.__get__(self)
        if self.is_block_tag:
            return rv + '\n'
        return rv


class Document(Container):
    """
    Outermost node.
    """
    allows_paragraphs = True
    is_document = True
    allowed_in_signatures = True


class Strong(Element):
    """
    Holds children that are emphasized strongly.  For HTML this will
    return a <strong> tag which is usually bold.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'strong', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</strong>'

    def prepare_docbook(self):
        yield u'<emphasis role="bold">'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</emphasis>'


class Emphasized(Element):
    """
    Like `Strong`, but with slightly less importance.  Usually rendered
    with an italic font face.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'em', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</em>'

    def prepare_docbook(self):
        yield u'<emphasis>'
        for item in Element.prepare_html(self):
            yield item
        yield u'</emphasis>'


class Underline(Element):
    """
    This element exists for backwards compatibility to MoinMoin and should
    not be used.  It generates a span tag with an "underline" class for
    HTML and could generate something similar for docbook or others.  It's
    also allowed to not render this element in a special way.
    """

    allowed_in_signatures = True

    def prepare_html(self):
        yield build_html_tag(u'span',
            id=self.id,
            style=self.style,
            classes=('underline', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'

    def prepare_docbook(self):
        yield u'<emphasis role="underline">'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</emphasis>'
