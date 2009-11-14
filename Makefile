# The Inyoka Makefile. Provides shortcuts for common tasks.
#
# :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
# :license: GNU GPL, see LICENSE for more details.

.PHONY: help docs docs/ server shell dbshell test-venv test runtests reindent clean-files


help:
	@echo "Commands understood:"
	@echo "  docs        create the docs (standalone HTML files)"
	@echo "  server      start a development server"
	@echo "  shell       start an interactive python shell"
	@echo "  test        run the unit and doc tests"
	@echo "  reindent    clean up indents"

docs/: docs
# bash_completion completes to docs/

docs:
	@(cd docs; make html)
	@(echo; echo '[32mDocs have been built in [1mdocs/_build/html/[0m[32m.[0m')

server:
	@python manage-inyoka.py runserver

shell:
	@python manage-inyoka.py shell

test-venv:
	python extra/make-bootstrap.py > ../bootstrap.py
	cd .. && python bootstrap.py inyoka-testsuite
	
test:
	extra/buildbottest.sh `pwd`

runtests:
	@PYTHONPATH=`pwd`:$PYTHONPATH python extra/runtests.py

reindent:
	@extra/reindent.py -r -B .

clean-files:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '*.orig' -exec rm -f {} +
	find . -name '*.orig.*' -exec rm -f {} +
	find . -name '*.py.fej' -exec rm -f {} +

i18n:
	@extra/extract-messages
	@extra/update-translations
	@extra/compile-translations
