# -*- coding: utf-8 -*-
"""
    inyoka.utils.debug
    ~~~~~~~~~~~~~~~~~~

    This module is a fork of the `zine.utils.debug` module for use in inyoka.

    :copyright: 2009-2010 by the Inyoka Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import re
import sys
from werkzeug import escape, html
from inyoka.core.routing import href


_body_end_re = re.compile(r'</\s*(body|html)(?i)')


def debug_repr(obj):
    """
    A function that does a debug repr for an object.  This is used by all the
    `nodes`, `macros` and `parsers` so that we get a debuggable ast.
    """
    return '%s.%s(%s)' % (
        obj.__class__.__module__.rsplit('.', 1)[-1],
        obj.__class__.__name__,
        ', '.join('%s=%r' % (key, value)
        for key, value in sorted(getattr(obj, '__dict__', {}).items())
        if not key.startswith('_'))
    )


def find_calling_context(skip=2):
    """Finds the calling context."""
    frame = sys._getframe(skip)
    while frame.f_back is not None:
        name = frame.f_globals.get('__name__')
        if name and name.startswith('inyoka.'):
            funcname = frame.f_code.co_name
            if 'self' in frame.f_locals:
                funcname = '%s.%s of %s' % (
                    frame.f_locals['self'].__class__.__name__,
                    funcname,
                    hex(id(frame.f_locals['self']))
                )
            return '%s:%s (%s)' % (
                frame.f_code.co_filename,
                frame.f_lineno,
                funcname
            )
        frame = frame.f_back
    return '<unknown>'


def render_query_table(queries):
    """Renders a nice table of all queries in the page."""
    total = 0
    stylesheet = href('static', file='style/debug.css')

    qresult = []
    for statement, parameters, start, end, calling_context in queries:
        total += (end - start)
        qresult.append(u'<li><pre>%s</pre><pre>Parameters: %s</pre>'
                      u'<div class="detail"><em>%s</em> | '
                      u'<strong>took %.3f ms</strong></div></li>' % (
            statement,
            parameters,
            escape(calling_context),
            (end - start) * 1000
        ))
    result = [u'<div id="database_debug_table">']
    stat = (u'<strong>(%d queries in %.2f ms)</strong>'
            % (len(queries), total * 1000))
    result.append(stat)
    result.append(u'<div id="database_debug_table_inner"><ul>')
    result.extend(qresult)
    result.append(u'<li>%s</li></ul></div></div>' % stat)

    result.append(html.script("""
        $(document).ready(function() {
            function toggleLog() {
                $('#database_debug_table_inner').toggle();
            }
            $('<a href="#database_debug_table">Show/Hide Log</a>').click(toggleLog)
                .prependTo($('#database_debug_table'));
            toggleLog();
        });
        """, type='text/javascript'))

    return u'\n'.join(result)


def inject_query_info(request, response):
    """Injects the collected queries into the response."""
    if not request.queries:
        return
    debug_info = render_query_table(request.queries).encode(response.charset)

    body = response.data
    match = _body_end_re.search(body)
    if match is not None:
        pos = match.start()
        response.data = body[:pos] + debug_info + body[pos:]
    else:
        response.data = body + '<hr>' + debug_info
    if 'content-length' in response.headers:
        response.headers['content-length'] = len(response.data)
