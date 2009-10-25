#!/usr/bin/env python
"""
    check-circ.py
    ~~~~~~~~~~~~~

    Tool for checking for circular imports in a python project.

    :author: Christoph Hack
    :license: GPL, see LICENSE for details
"""
import os
import re
import sys

if len(sys.argv) != 2:
    sys.stdout.write('Usage: %s <project_root>\n' % sys.argv[0])
    sys.exit(2)

re_import = re.compile(r'^(?:from\s+([\w.]+)\s+)import\s+([\w.]+)')
root_path = sys.argv[1]


def dfs(graph, pkg, visited=set(), active=[]):
    visited.add(pkg)
    active.append(pkg)
    for p in graph[pkg]:
        if p in active:
            return active[active.index(p):]
        if p not in visited:
            rval = dfs(graph, p, visited, active)
            if rval:
                return rval
    active.pop()

graph = dict()
for path, dirs, files in os.walk(root_path):
    for f in files:
        if f.endswith('.py'):
           graph['.'.join(path.split(os.sep) + [f[:-3]])] = set()

for path, dirs, files in os.walk(root_path):
    for f in files:
        if not f.endswith('.py'):
            continue

        pkg_from = '.'.join(path.split(os.sep) + [f[:-3]])
        for line in file(os.path.join(path, f)):
            match = re_import.match(line)
            if match:
                pkg_to = (match.group(1) or '').split('.') + match.group(2).split('.')

                pkg = []
                for p in pkg_to:
                    pkg.append(p)
                    if graph.has_key('.'.join(pkg)):
                        graph[pkg_from].add('.'.join(pkg))
                    if graph.has_key('.'.join(pkg + ['__init__'])):
                        graph[pkg_from].add('.'.join(pkg + ['__init__']))

while graph:
    delete = []
    for pkg, backrefs in graph.iteritems():
        if not backrefs:
            delete.append(pkg)
            for p, b in graph.iteritems():
                if pkg in b:
                    b.remove(pkg)
                    graph[p] = b
    if delete:
        for pkg in delete:
            print pkg
            del graph[pkg]
    else:
        sys.stderr.write('\nERROR: Detected circular import!\n\n')
        sys.stderr.write('Detected Cycle:\n - %s\n\n' % '\n - '.join(dfs(graph, pkg)))
        
        sys.stderr.write('Remaining dependecies:\n - %s\n' % '\n - '.join('%s (%s)' % \
            (k, ', '.join(v)) for k, v in graph.iteritems()))
        
        sys.exit(1)
        break
