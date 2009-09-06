# The Inyoka Makefile. Provides shortcuts for common tasks.
#
# :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
# :license: GNU GPL, see LICENSE for more details.

.PHONY: help docs server shell dbshell


help:
	@echo "Commands understood:"
	@echo "  docs        create the docs (standalone HTML files)"
	@echo "  server      start a development server"
	@echo "  shell       start an interactive python shell"
	@echo "  dbshell     start an interactive database shell"

docs/: docs
# bash_completion completes to docs/

docs:
	@(cd docs; make html)
	@(echo; echo '[32mDocs have been built in [1mdocs/_build/html/[0m[32m.[0m')

server:
	@python manage-inyoka.py runserver

shell:
	@python manage-inyoka.py shell

dbshell:
	@python manage-inyoka.py dbshell
