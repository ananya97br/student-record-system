.PHONY: bootstrap install check migrate seed test e2e run smoke load

bootstrap:
	python3 scripts/bootstrap.py

install:
	python3 -m pip install -r requirements.txt

check:
	.venv/bin/python manage.py check
	find . -name '*.py' -not -path './.venv/*' -not -path './.git/*' -print0 | xargs -0 -n1 .venv/bin/python -m py_compile

migrate:
	.venv/bin/python manage.py migrate

seed:
	.venv/bin/python manage.py seed_demo

test:
	.venv/bin/python manage.py test tests -v 1

e2e:
	.venv/bin/pytest e2e -q

run:
	.venv/bin/python manage.py runserver

smoke:
	sh scripts/smoke.sh

load:
	k6 run load/k6/target-2000.js
