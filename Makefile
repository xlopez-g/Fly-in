PYTHON_SYS	:=python3
VENV		:= .venv
PYTHON 		:= $(VENV)/bin/python3
PIP 		:= $(VENV)/bin/pip
FLAKE8		:= $(VENV)/bin/flake8
MYPY		:= $(VENV)/bin/mypy

MAP			?=example.txt
SRCS		:=$(wildcard *.py)

.PHONY: install run debug clean lint lint_strict

install:
		@test -d $(PYTHON) || $(PYTHON_SYS) -m venv $(VENV)
		$(PIP) install -r requirements.txt

run:
		$(PYTHON) main.py $(MAP)

debug:
		$(PYTHON) -m pdb main.py

clean:
		find . -type d -name "__pycache__" -exec rm -rf {} +
		rm -rf .mypy_cache .pytest_cache .flake8 $(VENV)

lint:
		$(FLAKE8) --exclude=$(VENV) .
		$(MYPY) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --exclude=$(VENV) .

lint_strict:
		$(FLAKE8) --exclude=$(VENV) .
		$(MYPY) --exclude=$(VENV) . --strict
