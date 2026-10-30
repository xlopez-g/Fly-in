PYTHON = python3
PIP = pip
MAP ?=config.txt

.PHONY: install run debug cleaan lint lint_strict

install:
		$(PIP) install -r requirements.txt

run:
		$(PYTHON) main.py $(MAP)

debug:
		$(PYTHON) -m pdb main.py

clean:
		find . -type d -name "__pycache__" -exec rm -rf {} +
		rm -rf .mypy_cache .pytest_cache .flake8

lint:
		flake8 .
		mypy . --warn-return-any--warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs--check-untyped-defs

lint_strict:
		flake8 .
		mypy . --strict