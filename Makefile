install-prod: # Install only production dependencies
	python -m pip install --upgrade pip setuptools
	python -m pip install -Ur requirements.prod.txt

install: # Install all dependencies (tests, linter, plugins)
	python -m pip install --upgrade pip setuptools
	python -m pip install -Ur requirements.dev.txt

flake:
	python -m flake8

run:
	python manage.py start

db:
	python manage.py migrate
