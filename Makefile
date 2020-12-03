install: # install dependencies
    python -m pip install --upgrade pip setuptools
    python -m pip install -r dev-requirements.txt

flake: # TODO: requires: install
    python -m flake8

