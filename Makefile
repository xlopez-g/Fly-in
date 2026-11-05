VENV	:= .venv
PYTHON 	:= $(VENV)/bin/python3
PIP 	:= $(VENV)/bin/pip
FLAKE8	:= $(VENV)/bin/flake8
MYPY	:= $(VENV)/bin/mypy
MAP		?=config.txt

.PHONY: install run debug clean lint lint_strict

install:
		@test -d $(VENV) || python3 -m venv $(VENV)
		$(PIP) install -r requirements.txt

run:
		$(PYTHON) main.py $(MAP)

debug:
		$(PYTHON) -m pdb main.py

clean:
		find . -type d -name "__pycache__" -exec rm -rf {} +
		rm -rf .mypy_cache .pytest_cache .flake8

lint:
		$(FLAKE8) .
		$(MYPY) --warn-return-any--warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs--check-untyped-defs -

lint_strict:
		$(FLAKE8) .
		$(MYPY) . --strict
