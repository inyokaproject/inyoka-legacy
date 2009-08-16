#
# Inyoka Makefile
# ~~~~~~~~~~~~~~~
#
# Shortcuts for various tasks.
#
# :copyright: 2009 by the Inyoka Team, see AUTHORS for more details.
# :license: GNU GPL, see LICENSE for more details.
#
.PHONY: test doc pdfdoc reindent migrate test_data server profiled shell clean-files

test:
	@(python run_tests.py)

doc:
	@(cd docs; make html)
	@(echo -e '\E[33;34m'"\033[1mDocumentation build at docs/_build/html\033[0m")

pdfdoc:
	@(cd docs; make latex; cd _build/latex; make all-pdf)
	@(echo -e '\E[33;34m'"\033[1mDocumentation build at docs/_build/latex/Inyoka.pdf\033[0m")

reindent:
	@extra/reindent.py -r -B .

migrate:
	@(python dbmanage.py upgrade)

server_cherrypy:
	@(python manage-inyoka.py runcp)

server:
	@(python manage-inyoka.py runserver)

server2.4:
	@(python2.4 manage-inyoka.py runserver)

profiled:
	@(python manage-inyoka.py profiled)

shell:
	@(python manage-inyoka.py shell)

dbshell:
	@(python manage-inyoka.py dbshell)

codetags:
	@(python extra/find_codetags.py ./inyoka)
	@(echo -e '\E[33;34m'"\033[1mOpen tags.html with your browser to see all tags that bothers us\033[0m")

clean-files:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '*.orig' -exec rm -f {} +
	find . -name '*.orig.*' -exec rm -f {} +
	find . -name '*.rej' -exec rm -f {} +
	rm -rf docs/_build

extract-messages:
	pybabel extract -F babel.ini -o lodgeit/i18n/messages.pot .

update-translations:
	pybabel update -ilodgeit/i18n/messages.pot -dlodgeit/i18n -Dmessages

compile-translations:
	pybabel compile -dlodgeit/i18n --statistics
