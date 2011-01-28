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

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
from urlparse import urlparse, urlunparse
from markupsafe import escape
from inyoka.context import ctx
from inyoka.core.markup.machine import NodeCompiler, NodeRenderer, \
    NodeQueryInterface
from inyoka.utils.html import build_html_tag
from inyoka.utils.debug import debug_repr
from inyoka.utils.text import gen_slug


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


class Raw(Container):
    """
    A raw container.
    """
    is_raw = True


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


class Span(Element):
    """
    Inline general text element
    """

    allowed_in_signatures = True

    def __init__(self, children=None, id=None,
                 style=None, class_=None):
        Element.__init__(self, children, id, style, class_)


    def prepare_html(self):
        yield build_html_tag(u'span',
            id=self.id,
            style=self.style,
            class_=self.class_,
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Link(Element):
    """
    External or anchor links.
    """

    allowed_in_signatures = True

    def __init__(self, url, children=None, title=None, id=None,
                 style=None, class_=None, shorten=False):
        if not children:
            if shorten and len(url) > 50:
                children = [
                    Span([Text(url[:36])], class_=u'longlink_show'),
                    Span([Text(url[36:-14])], class_=u'longlink_collapse'),
                    Span([Text(url[-14:])]),
                ]
            else:
                text = url
                if text.startswith('mailto:'):
                    text = text[7:]
                children = [Text(text)]
            if title is None:
                title = url
        Element.__init__(self, children, id, style, class_)
        self.title = title
        self.scheme, self.netloc, self.path, self.params, self.querystring, \
            self.anchor = urlparse(url)


    @property
    def href(self):
        return urlunparse((self.scheme, self.netloc, self.path, self.params,
                           self.querystring, self.anchor))

    def generate_markup(self, w):
        if self.text == self.href:
            # generate a free link
            return w.markup(self.href)
        else:
            w.markup(u'[%s' % self.href)
            w.markup(u' ')
            w.start_escaping(u']')
            Element.generate_markup(self, w)
            w.stop_escaping()
            w.markup(u']')

    def prepare_html(self):
        if self.scheme == 'javascript':
            yield escape(self.caption)
            return
        rel = None
        if not self.netloc or self.netloc == ctx.cfg['base_domain_name'] or \
           self.netloc.endswith('.' + ctx.cfg['base_domain_name']):
            class_ = u'crosslink'
        else:
            class_ = u'external'
            rel = u'nofollow'

        yield build_html_tag(u'a',
            rel=rel,
            id=self.id,
            style=self.style,
            title=self.title,
            classes=(class_, self.class_),
            href=self.href
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</a>'

    def prepare_docbook(self):
        yield u'<ulink url="%s">' % self.href
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</ulink>'


class Section(Element):

    def __init__(self, level, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.level = level

    def __str__(self):
        return 'Section(%d)' % self.level

    def prepare_html(self):
        class_ = u'section_%d' % self.level
        if self.class_:
            class_ += u' ' + self.class_
        yield build_html_tag(u'div', id=self.id, style=self.style,
                             class_=class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</div>'

    def prepare_docbook(self):
        yield u'<sect%d>' % self.level
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</sect%d>' % self.level


class Paragraph(Element):
    """
    A paragraph.  Everything is in there :-)
    (except of block level stuff)
    """
    is_block_tag = True
    is_paragraph = True
    allowed_in_signatures = True
    is_linebreak_node = True

    @property
    def text(self):
        return Element.text.__get__(self).strip() + '\n\n'

    def generate_markup(self, w):
        Element.generate_markup(self, w)
        w.paragraph()

    def prepare_html(self):
        yield build_html_tag(u'p', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</p>'

    def prepare_docbook(self):
        yield u'<para>'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</para>'


class Error(Element):
    """
    If a macro is not renderable or not found this is
    shown instead.
    """
    is_block_tag = True
    allows_paragraphs = True

    def prepare_html(self):
        yield build_html_tag(u'div',
            id=self.id,
            style=self.style,
            classes=(u'error', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</div>'


class Footnote(Element):
    """
    This represents a footnote.  A transformer moves the actual
    text down to the bottom and sets an automatically incremented id.
    If that transformer is not activated a <small> section is rendered.
    """

    def generate_markup(self, w):
        w.markup(u"((")
        w.start_escaping(u'))')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u"))")

    def prepare_html(self):
        if self.id is None:
            yield build_html_tag(u'small',
                id=self.id,
                style=self.style,
                classes=(u'note', self.class_)
            )
            for item in Element.prepare_html(self):
                yield item
            yield u'</small>'
        else:
            yield u'<a href="#fn-%d" id="bfn-%d" class="footnote">' \
                  u'<span class="paren">[</span>%d<span class="paren">]' \
                  u'</span></a>' % (self.id, self.id, self.id)


class Ruler(Node):
    """
    Newline with line.
    """

    is_block_tag = True

    def generate_markup(self, w):
        w.newline()
        w.markup(u'----')
        w.newline()

    def prepare_html(self):
        yield u'<hr>'


class Quote(Element):
    """
    A blockquote.
    """
    is_block_tag = True
    allows_paragraphs = True
    allowed_in_signatures = True

    def generate_markup(self, w):
        w.newline()
        w.quote()
        Element.generate_markup(self, w)
        w.unquote()

    def prepare_html(self):
        yield build_html_tag(u'blockquote', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</blockquote>'

    def prepare_docbook(self):
        yield u'<blockquote>'
        for item in Element.prepare_html(self):
            yield item
        yield u'</blockquote>'


class Preformatted(Element):
    """
    Preformatted text.
    """
    is_block_tag = True
    is_raw = True
    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u'{{{')
        w.raw()
        w.start_escaping(u'}}}')
        Element.generate_markup(self, w)
        if w._result[-1][-1] == u'}':
            # prevent four }s
            w.touch_whitespace()
        w.stop_escaping()
        w.endraw()
        w.markup(u'}}}')

    def prepare_html(self):
        yield build_html_tag(u'pre', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</pre>'

    def prepare_docbook(self):
        yield u'<screen>'
        for item in Element.prepare_html(self):
            yield item
        yield u'</screen>'


class Headline(Element):
    """
    Represents all kinds of headline tags.
    """
    is_block_tag = True

    def __init__(self, level, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.level = level
        if id is None:
            self.id = gen_slug(self.text)

    def generate_markup(self, w):
        w.markup(u'= ')
        Element.generate_markup(self, w)
        w.markup(u' =')
        w.newline()

    def prepare_html(self):
        yield build_html_tag(u'h%d' % (self.level + 1),
            id=self.id,
            style=self.style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'<a href="#%s" class="headerlink">¶</a>' % self.id
        yield u'</h%d>' % (self.level + 1)

    def prepare_docbook(self):
        yield u'<title>'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</title>'


class Strong(Element):
    """
    Holds children that are emphasized strongly.  For HTML this will
    return a <strong> tag which is usually bold.
    """

    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u"'''")
        w.start_escaping(u"'''")
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u"'''")

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


class Highlighted(Strong):
    """
    Marks highlighted text.
    """

    def generate_markup(self, w):
        w.markup(u'[mark]')
        w.start_escaping(u'[/mark]')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u'[/mark]')

    def prepare_html(self):
        classes = ['highlighted']
        if self.class_:
            classes.append(self._class)
        yield build_html_tag(u'strong', id=self.id, style=self.style,
                             classes=classes)
        for item in Element.prepare_html(self):
            yield item
        yield u'</strong>'


class Emphasized(Element):
    """
    Like `Strong`, but with slightly less importance.  Usually rendered
    with an italic font face.
    """

    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u"''")
        w.start_escaping("''")
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u"''")

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


class SourceLink(Element):

    allowed_in_signatures = False

    def __init__(self, target, children=None, id=None, style=None, class_=None):
        if children is None:
            children = [Text(u'[%d]' % target)]
        Element.__init__(self, children, id, style, class_)
        self.target = target

    @property
    def text(self):
        return '[%d]' % self.target

    def generate_markup(self, w):
        w.markup(self.text)

    def prepare_html(self):
        yield build_html_tag(u'sup', id=self.id, style=self.style,
                             class_=self.class_)
        yield u'<a href="#source-%d">' % self.target
        for item in Element.prepare_html(self):
            yield item
        yield u'</a></sup>'

    def prepare_docbook(self):
        yield self.text


class Code(Element):
    """
    This represents code.  Usually formatted in a monospaced font that
    preserves whitespace.  Additionally this node is maked raw so children
    are not touched by the altering translators.
    """
    is_raw = True
    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u"``")
        w.start_escaping(u'``')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u"``")

    def prepare_html(self):
        yield build_html_tag(u'code', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</code>'

    def prepare_docbook(self):
        yield u'<literal>'
        for item in Element.prepare_html(self):
            yield item
        yield u'</literal>'


class Underline(Element):
    """
    This element exists for backwards compatibility to MoinMoin and should
    not be used.  It generates a span tag with an "underline" class for
    HTML and could generate something similar for docbook or others.  It's
    also allowed to not render this element in a special way.
    """

    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u"__")
        w.start_escaping(u'__')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u"__")

    def prepare_html(self):
        yield build_html_tag(u'span',
            id=self.id,
            style=self.style,
            classes=(u'underline', self.class_)
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'

    def prepare_docbook(self):
        yield u'<emphasis role="underline">'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</emphasis>'


class Stroke(Element):
    """
    This element marks deleted text.
    """

    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u"--(")
        w.start_escaping(u')--')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u")--")

    def prepare_html(self):
        yield build_html_tag(u'del', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</del>'


class Small(Element):
    """
    This elements marks not so important text, so it removes importance.
    It's usually rendered in a smaller font.
    """

    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u"~-(")
        w.start_escaping(u')-~')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u")-~")

    def prepare_html(self):
        yield build_html_tag(u'small', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</small>'


class Big(Element):
    """
    The opposite of Small, but it doesn't give the element a real emphasis.
    """

    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u"~+(")
        w.start_escaping(u')+~')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u")+~")

    def prepare_html(self):
        yield build_html_tag(u'big', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</big>'


class Sub(Element):
    """
    Marks text as subscript.
    """

    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u',,(')
        w.start_escaping(u'),,')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u'),,')

    def prepare_html(self):
        yield build_html_tag(u'sub', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</sub>'

    def prepare_docbook(self):
        yield u'<subscript>'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</subscript>'


class Sup(Element):
    """
    Marks text as superscript.
    """

    allowed_in_signatures = True

    def generate_markup(self, w):
        w.markup(u'^^(')
        w.start_escaping(u')^^')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u')^^')

    def prepare_html(self):
        yield build_html_tag(u'sup', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</sup>'

    def prepare_docbook(self):
        yield u'<superscript>'
        for item in Element.prepare_html(self):
            yield item
        yield u'</superscript>'


class Color(Element):
    """
    Gives the embedded text a color.  Like `Underline` it just exists because
    of backwards compatibility (this time to phpBB).
    """

    allowed_in_signatures = True

    def __init__(self, value, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.value = value

    def generate_markup(self, w):
        w.markup(u'[color=%s]' % self.value)
        w.start_escaping(u'[/color]')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u'[/color]')

    def prepare_html(self):
        style = self.style and self.style + '; ' or ''
        style += u'color: %s' % self.value
        yield build_html_tag(u'span',
            id=self.id,
            style=style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Size(Element):
    """
    Gives the embedded text a size.  Like `Underline` it just exists because
    of backwards compatibility.  Requires the font size in percent.
    """

    def __init__(self, size, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.size = size

    def generate_markup(self, w):
        w.markup(u'[size=%s]' % self.size)
        w.start_escaping(u'[/size]')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u'[/size]')

    def prepare_html(self):
        style = self.style and self.style + '; ' or ''
        style += u'font-size: %.2f%%' % self.size
        yield build_html_tag(u'span',
            id=self.id,
            style=style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class Font(Element):
    """
    Gives the embedded text a font face.  Like `Underline` it just exists
    because of backwards compatibility.
    """

    allowed_in_signatures = True

    def __init__(self, faces, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.faces = faces

    def generate_markup(self, w):
        w.markup(u'[font=%s]' % self.value)
        w.start_escaping(u'[/font]')
        Element.generate_markup(self, w)
        w.stop_escaping()
        w.markup(u'[/font]')

    def prepare_html(self):
        style = self.style and self.style + '; ' or ''
        style += u"font-family: %s" % u', '.join(
            x in ('serif', 'sans-serif', 'fantasy') and x or u"'%s'" % x
            for x in self.faces
        )
        yield build_html_tag(u'span',
            id=self.id,
            style=style,
            class_=self.class_
        )
        for item in Element.prepare_html(self):
            yield item
        yield u'</span>'


class DefinitionList(Element):
    """
    A list of defintion terms.
    """
    is_block_tag = True

    def prepare_html(self):
        yield build_html_tag(u'dl', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</dl>'


class DefinitionTerm(Element):
    """
    A definition term has a term (surprise) and a value (the children).
    """
    is_block_tag = True
    allows_paragraphs = True

    def __init__(self, term, children=None, id=None, style=None,
                 class_=None):
        Element.__init__(self, children, id, style, class_)
        self.term = term

    def generate_markup(self, w):
        w.markup(u'  %s:: ' % self.term)
        w.oneline()
        Element.generate_markup(self, w)
        w.endblock()

    def prepare_html(self):
        yield build_html_tag(u'dt', class_=self.class_, style=self.style,
                             id=self.id)
        yield escape(self.term)
        yield u'</dt>'
        yield build_html_tag(u'dd', class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</dd>'


class List(Element):
    """
    Sourrounds list items so that they appear as list.  Make sure that the
    children are list items.
    """
    is_block_tag = True

    def __init__(self, type, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.type = type

    def generate_markup(self, w):
        w.list(self.type)
        Element.generate_markup(self, w)
        w.endlist()

    def prepare_html(self):
        if self.type == 'unordered':
            tag = u'ul'
            cls = None
        else:
            tag = u'ol'
            cls = self.type
        yield build_html_tag(tag, id=self.id, style=self.style,
                             classes=(self.class_, cls))
        for item in Element.prepare_html(self):
            yield item
        yield u'</%s>' % tag

    def prepare_docbook(self):
        if self.type == 'unordered':
            tag = u'itemizedlist'
        else:
            tag = u'orderedlist'
        yield u'<%s>' % tag
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</%s>' % tag


class ListItem(Element):
    """
    Marks the children as list item.  Use in conjunction with list.
    """
    is_block_tag = True
    allows_paragraphs = True

    def generate_markup(self, w):
        w.item()
        Element.generate_markup(self, w)
        w.enditem()

    def prepare_html(self):
        yield build_html_tag(u'li', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</li>'

    def prepare_docbook(self):
        yield u'<listitem>'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</listitem>'


class Box(Element):
    """
    A dialog like object.  Usually renders to a layer with one headline and
    a second layer for the contents.
    """
    is_block_tag = True
    allows_paragraphs = True

    def __init__(self, title=None, children=None, align=None, valign=None,
                 id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.title = title
        self.class_ = class_
        self.align = align
        self.valign = valign

    def prepare_html(self):
        style = []
        if self.align:
            style.append(u'text-align: ' + self.align)
        if self.valign:
            style.append(u'vertical-align: ' + self.valign)
        if self.style:
            style.append(self.style)
        yield build_html_tag(u'div',
            id=self.id,
            style=style and u' '.join(style) or None,
            classes=(self.class_,)
        )
        if self.title is not None:
            yield build_html_tag(u'h3', class_=self.class_)
            yield escape(self.title)
            yield u'</h3>'
        yield build_html_tag(u'div', classes=(u'contents',))
        for item in Element.prepare_html(self):
            yield item
        yield u'</div></div>'


class Layer(Element):
    """
    Like a box but without headline and an nested content section.  Translates
    into a plain old HTML div or something comparable.
    """
    is_block_tag = True
    allows_paragraphs = True

    def prepare_html(self):
        yield build_html_tag(u'div', id=self.id, style=self.style,
                             class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</div>'


class Table(Element):
    """
    A simple table.  This can only contain table rows.
    """
    is_block_tag = True

    def __init__(self, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)

    def prepare_html(self):
        yield build_html_tag(u'table', id=self.id, class_=self.class_,
                             style=self.style)
        for item in Element.prepare_html(self):
            yield item
        yield u'</table>'

    def prepare_docbook(self):
        cols = 1
        for row in self.query.by_type(TableRow):
            cols = max(cols, len(list(row.query.by_type(TableCell))))
        yield u'<informaltable>'
        yield u'<tgroup cols="%d">' % cols
        yield u'<tbody>'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</tbody>'
        yield u'</tgroup>'
        yield u'</informaltable>'


class TableRow(Element):
    """
    A row in a table.  Only contained in a table and the only children
    nodes supported are table cells and headers.
    """
    is_block_tag = True

    def __init__(self, children=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)

    def prepare_html(self):
        yield build_html_tag(u'tr', id=self.id, class_=self.class_,
                             style=self.style)
        for item in Element.prepare_html(self):
            yield item
        yield u'</tr>'

    def prepare_docbook(self):
        yield u'<row>'
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</row>'


class TableCell(Element):
    """
    Only contained in a table row and renders to a table cell.
    """
    is_block_tag = True
    _html_tag = u'td'

    def __init__(self, children=None, colspan=None, rowspan=None, align=None,
                 valign=None, id=None, style=None, class_=None):
        Element.__init__(self, children, id, style, class_)
        self.colspan = colspan or 0
        self.rowspan = rowspan or 0
        self.align = align
        self.valign = valign

    def prepare_html(self):
        style = []
        if self.align:
            style.append(u'text-align: ' + self.align)
        if self.valign:
            style.append(u'vertical-align: ' + self.valign)
        if self.style:
            style.append(self.style)

        yield build_html_tag(self._html_tag,
            colspan=self.colspan or None,
            rowspan=self.rowspan or None,
            style=style and u'; '.join(style) or None,
            id=self.id,
            class_=self.class_
        )

        for item in Element.prepare_html(self):
            yield item
        yield u'</%s>' % self._html_tag

    def prepare_docbook(self):
        yield build_html_tag(u'entry',
            morerows=(self.rowspan and self.rowspan - 1) or None,
            align=self.align,
        )
        for item in Element.prepare_docbook(self):
            yield item
        yield u'</entry>'


class TableHeader(TableCell):
    """
    Exactly like a table cell but renders to <th>
    """
    _html_tag = u'th'


class TableHeadSection(Element):
    """
    Roughtly translates into a `<thead>` or similar thing.
    """

    def prepare_html(self):
        yield build_html_tag(u'thead', style=self.style,
                             id=self.id, class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</thead>'


class TableBodySection(Element):
    """
    Roughtly translates into a `<tbody>` or similar thing.
    """

    def prepare_html(self):
        yield build_html_tag(u'tbody', style=self.style,
                             id=self.id, class_=self.class_)
        for item in Element.prepare_html(self):
            yield item
        yield u'</tbody>'
