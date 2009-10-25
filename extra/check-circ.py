#!/usr/bin/env python
"""
    check-circ.py
    ~~~~~~~~~~~~~

    Tool for checking for circular imports in a python project.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for details.
"""
import os
from os.path import abspath, normpath, relpath, isfile, join as joinpath
import re
import sys

_import_re = re.compile(r'^(?:from\s+([\w.]+)\s+)import\s+([\w., ]+)')


class CircularImportFinder(object):

    def __init__(self, project_root):
        if not isfile(joinpath(project_root, '__init__.py')):
            raise ValueError('Invalid project root: "%s"' % project_root)
        self.project_root = abspath(project_root)

    def get_package_name(self, path, filename):
        """Return a pretty package name for the given file."""
        if not filename.endswith('.py'):
            return None
        strip_path = normpath(joinpath(self.project_root, os.pardir))
        return '.'.join(relpath(path, strip_path).split(os.sep) + \
            [filename[:-3]])

    def generate_graph(self):
        """Generate a directed dependency graph for the project."""
        graph = dict()
        
        for path, dirs, files in os.walk(self.project_root):
            for filename in files:
                if filename.endswith('.py'):
                    graph[self.get_package_name(path, filename)] = set()

        for path, dirs, files in os.walk(self.project_root):
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                pkg_from = self.get_package_name(path, filename)
                for line in file(os.path.join(path, filename)):
                    match = _import_re.match(line)
                    if not match:
                        continue
                    for g2 in match.group(2).split(','):
                        pkg_to = (match.group(1) or '').split('.') + g2.strip().split('.')
                        pkg = []
                        for p in pkg_to:
                            pkg.append(p)
                            p1, p2 = '.'.join(pkg), '.'.join(pkg + ['__init__'])
                            if graph.has_key(p1) and p1 != pkg_from:
                                graph[pkg_from].add(p1)
                            if graph.has_key(p2) and p2 != pkg_from:
                                graph[pkg_from].add(p2)
                
        return graph

    def print_graph(self, graph):
        """Print the graph to stdout, which might be useful for debugging."""
        for package, dependencies in graph.iteritems():
            print ' - %s (%s)' % (package, ', '.join(dependencies))

    def sort_topological(self, graph):
        """Sort the directed dependency graph topological to find out the
        import order and to detect cyclic dependencies."""
        rval = []
        while graph:
            delete = []
            for package, dependencies in graph.iteritems():
                if not dependencies:
                    delete.append(package)
                    for p, d in graph.iteritems():
                        if package in d:
                            d.remove(package)
                            graph[p] = d
            if delete:
                for package in sorted(delete):
                    rval.append(package)
                    del graph[package]
            else:
                return rval
        return rval
    
    def find_cycle(self, graph, package=None, visited=set(), active=[]):
        """Perform a depth-first-search on the graph to detect the exact
        location of the cycle."""
        if not graph:
            return []
        elif package is None:
            package = graph.keys()[0]
        visited.add(package)
        active.append(package)
        for dependency in graph[package]:
            if dependency in active:
                return active[active.index(dependency):]
            elif dependency not in visited:
                rval = self.find_cycle(graph, dependency, visited, active)
                if rval:
                    return rval
        active.pop()


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stdout.write('Usage: %s <project_root>\n' % sys.argv[0])
        sys.exit(2)

    finder = CircularImportFinder(sys.argv[1])
    graph = finder.generate_graph()
    packages = finder.sort_topological(graph)
    print '\n'.join(packages)
    
    if graph:
        print '\nError: Ouch, a circular dependency was detected!\n'
        print 'Detected cycle:\n - %s\n' % '\n - '.join(finder.find_cycle(graph))
        print 'Remaining dependencies:'
        finder.print_graph(graph)
        sys.exit(1)
    else:
        print  '\nHooray, everything is fine! No circular dependencies found.'
