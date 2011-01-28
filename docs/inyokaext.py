# -*- coding: utf-8 -*-
"""
    inyokaext
    ~~~~~~~~~

    Some extensions for our documentation.

    :copyright: 2010-2011 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""
import inspect
from docutils import nodes
from docutils.statemachine import ViewList
from inyoka.core.serializer import list_api_methods


def dump_services():
    def directive(dirname, arguments, options, content, lineno,
                  content_offset, block_text, state, state_machine):
        services = list_api_methods()
        result = ViewList()
        for service in services.iterkeys():
            desc = services[service]
            items = ['.. function:: %s%s' % (service, desc['signature']), '']
            # valid methods
            items.append("     - Valid Methods: %s" % u', '.join(desc['valid_methods']))
            items.append('     - Valid Urls:')
            items.extend([("           - `%s`" % url) for url in desc['urls']])
            items.extend('     ' + line for line in desc['doc'])
            for _ in items:
                result.append(_, '<inyokaext>')
        node = nodes.paragraph()
        state.nested_parse(result, content_offset, node)
        return node.children
    return directive


inyoka_services = dump_services()


def setup(app):
    app.add_directive('inyokaservices', inyoka_services, 0, (0, 0, 0))
