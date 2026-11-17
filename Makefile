PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
UV ?= uv
SRC_DIR := src

.PHONY: install run debug clean lint lint-strict

install:
	uv sync

run:
	$(PYTHON) $(SRC_DIR)/__main__.py

debug:
	$(PYTHON) -m pdb $(SRC_DIR)/__main__.py

clean:
	rm -rf __pycache__ .mypy_cache .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

lint:
	$(UV) run flake8 $(SRC_DIR)
	$(UV) run mypy $(SRC_DIR) --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	$(UV) run flake8 $(SRC_DIR)
	$(UV) run mypy $(SRC_DIR) --strict
