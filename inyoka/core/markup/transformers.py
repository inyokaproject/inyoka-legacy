# -*- coding: utf-8 -*-
"""
    inyoka.core.markup.transformers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module holds ast transformers we use.  Transformers can assume that
    they always operate on complete trees, thus the outermost node is always
    a container node.

    Transformers are not necessarily the last thing that processes a tree.
    For example macros that are marked as tree processors and have have their
    stage attribute set to 'final' are expanded after all the transformers
    finished their job.

    :copyright: 2009-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import re
from inyoka import Interface
from inyoka.core.markup import nodes


_paragraph_re = re.compile(r'(\s*?\n){2,}')


class ITransformer(Interface):
    """
    Baseclass for all transformers.
    """

    def transform(self, tree):
        """
        This is passed a tree that should be processed.  A class can modify
        a tree in place, the return value has to be the tree then.  Otherwise
        it's safe to return a new tree.
        """
        return tree


class AutomaticParagraphs(ITransformer):
    """
    This transformer is enabled per default and wraps elements in paragraphs.
    All macros and parsers depend on this parser so it's a terrible idea to
    disable this one.
    """

    def joined_text_iter(self, node):
        """
        This function joins multiple text nodes that follow each other into
        one.
        """
        text_buf = []

        def flush_text_buf():
            if text_buf:
                text = u''.join(text_buf)
                if text:
                    yield nodes.Text(text)
                del text_buf[:]

        for child in node.children:
            if child.is_text_node:
                text_buf.append(child.text)
            else:
                for item in flush_text_buf():
                    yield item
                yield child
        for item in flush_text_buf():
            yield item

    def transform(self, parent):
        """
        Insert real paragraphs into the node and return it.
        """
        for node in parent.children:
            if node.is_container and not node.is_raw:
                self.transform(node)

        if not parent.allows_paragraphs:
            return parent

        paragraphs = [[]]

        for child in self.joined_text_iter(parent):
            if child.is_text_node:
                blockiter = iter(_paragraph_re.split(child.text))
                for block in blockiter:
                    try:
                        is_paragraph = blockiter.next()
                    except StopIteration:
                        is_paragraph = False
                    if block:
                        paragraphs[-1].append(nodes.Text(block))
                    if is_paragraph:
                        paragraphs.append([])
            elif child.is_block_tag:
                paragraphs.extend((child, []))
            else:
                paragraphs[-1].append(child)

        del parent.children[:]
        for paragraph in paragraphs:
            if not isinstance(paragraph, list):
                parent.children.append(paragraph)
            else:
                for node in paragraph:
                    if not node.is_text_node or node.text:
                        parent.children.append(nodes.Paragraph(paragraph))
                        break

        return parent


class HeadlineProcessor(ITransformer):
    """
    This transformer looks at all headlines and makes sure that every ID is
    unique.  If one id clashes with another headline ID a numeric suffix is
    added.  What this transformer does not do is resolving clashes with
    footnotes or other references.  At least not by now because such clashes
    are very unlikely.
    """

    def transform(self, tree):
        id_map = {}
        for headline in tree.query.by_type(nodes.Headline):
            while 1:
                if not headline.id:
                    headline.id = 'empty-headline'
                if headline.id not in id_map:
                    id_map[headline.id] = 1
                    break
                else:
                    id_map[headline.id] += 1
                    headline.id += '-%d' % id_map[headline.id]
        return tree
