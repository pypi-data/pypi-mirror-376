
# Quick helpers for MDL
.PHONY: venv install build sdist wheel pipx-install pipx-uninstall zipapp test clean test-compiler

PYTHON ?= python3

venv:
	$(PYTHON) -m venv .venv

install: venv
	. .venv/bin/activate; pip install -e .

build: ## sdist + wheel
	. .venv/bin/activate || true; python -m pip install -U pip build; python -m build

sdist: build
wheel: build

zipapp:
	python -c "import zipapp; zipapp.create_archive('$(CURDIR)', target='mdl.pyz', interpreter='/usr/bin/env python3', main='minecraft_datapack_language.cli:main', compressed=True)"; \
	echo "Created ./mdl.pyz"

pipx-install:
	pipx install .

pipx-uninstall:
	pipx uninstall minecraft-datapack-language || true

test-compiler: ## Test the compiler fixes
	@echo "Testing compiler fixes..."
	@python test_compiler_fixes.py

test: test-compiler ## Run all tests
	@echo "All tests completed."

clean:
	rm -rf .venv build dist *.egg-info tmp_mdl_test mdl.pyz
