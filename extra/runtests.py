#!/usr/bin/env python
"""
    Inyoka Testrunner
    ~~~~~~~~~~~~~~~~~

    Note, that running the tests is not available via manage-inyoka.py, cause
    we import some stuff there and that does kill covergae.

    :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
    :license: GNU GPL, see LICENSE for more details.
"""

def action_runtests():
    """Run the unit and doctests"""
    import sys
    # remove unused options from sys.argv
    sys.argv = sys.argv[:1]

    from inyoka.core.test import run_suite
    run_suite()


if __name__ == '__main__':
    action_runtests()
