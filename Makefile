#* Variables
SHELL := /usr/bin/env bash
PYTHON := python
PWD := `pwd`

#* Docker variables
PROJECT := tubecast
PROJECT_TITLE := Python Fastapi Stack
VERSION := latest
PYINSTALLER_ENTRY := $(PROJECT)/__main__.py

# poetry show black2 &> /dev/null && echo "true" || echo "false"


#-----------------------------------------------------------------------------------------
# DEV INSTALLATION
#-----------------------------------------------------------------------------------------
.PHONY: install-poetry
install-poetry: ## Download and install Poetry
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(PYTHON) -

.PHONY: uninstall-poetry
uninstall-poetry: ## Uninstall Poetry
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | $(PYTHON) - --uninstall

.PHONY: install-pre-commit-hooks
install-pre-commit-hooks: ## Install Pre-Commit Git Hooks
	poetry run pre-commit install


#-----------------------------------------------------------------------------------------
# INSTALL/UPDATE DEPENDENCIES/REQUIREMENTS
#-----------------------------------------------------------------------------------------

.PHONY: install
install: ## Install Project Dependecies/Requirements from Poetry
	poetry lock -n && poetry export --without-hashes > requirements.txt
	poetry install -n
	-poetry run mypy --install-types --non-interactive ./

.PHONY: update-dev-deps
update-dev-deps: ## Update dev dependecies to @latest version
	poetry add --group dev  bandit@latest darglint@latest "isort[colors]@latest" mypy@latest pre-commit@latest pydocstyle@latest pylint@latest pytest@latest pyupgrade@latest safety@latest coverage@latest coverage-badge@latest pytest-html@latest pytest-cov@latest
	poetry add --group dev  --allow-prereleases black@latest

#-----------------------------------------------------------------------------------------
# ORIGINAL INSTALLATION HOOKS
#-----------------------------------------------------------------------------------------
.PHONY: poetry-download
poetry-download: install-poetry ## Download and install Poetry

.PHONY: pre-commit-install
pre-commit-install: install-pre-commit-hooks ## Install Pre-Commit Git Hooks

#-----------------------------------------------------------------------------------------
# Linting, Formatting, TypeCheck
#-----------------------------------------------------------------------------------------
.PHONY: lint
lint: test check-codestyle mypy pre-commit ## Lint, Format, Check Types, Check Safety

.PHONY: formatting
formatting: codestyle ## Apply Formatting via PyUpgrade, ISort, Black.

.PHONY: codestyle
codestyle: ## Apply Formatting via PyUpgrade, ISort, Black.
	@echo -e "\n### PYUPGRADE ###"
	poetry run pyupgrade --exit-zero-even-if-changed --py310-plus **/*.py
	@echo -e "\n### ISORT ###"
	poetry run isort --settings-path pyproject.toml ./
	@echo -e "\n### BLACK ###"
	poetry run black --config pyproject.toml ./

.PHONY: check-codestyle
check-codestyle: ## Check Formatting via ISort, Black, darglint.
	@echo -e "\n### ISORT ###"
	@poetry run isort --diff --check-only --settings-path pyproject.toml ./
	@echo -e "\n### BLACK ###"
	@poetry run black --diff --check --config pyproject.toml ./
	@echo -e "\n### DARGLINT ###"
	@poetry run darglint --verbosity 2 $(PROJECT) tests

.PHONY: check-safety
check-safety: ## Check Securty & Safty via Bandit, Safety.
	poetry check
	poetry run safety check --full-report
	poetry run bandit -ll --recursive $(PROJECT) tests

.PHONY: mypy
mypy: ## Typechecking via MyPy
	@echo -e "\n### MYPY ###"
	@poetry run mypy --config-file pyproject.toml ./

.PHONY: pre-commit
pre-commit: ## Run Pre-Commit Hooks
	@printf "\n### PRE-COMMIT ###"
	@poetry run pre-commit run --all-files


#-----------------------------------------------------------------------------------------
# TESTS
#-----------------------------------------------------------------------------------------
.PHONY: tests
tests: test ## Run Tests & Coverage

.PHONY: test
test: ## Run Tests & Coverage
	@printf "\n### PYTEST ###\n"
	@PWD=$(PWD) poetry run pytest -c pyproject.toml --cov-report=html --cov-report=xml  --cov=$(PROJECT) tests/
	@# poetry run pytest --cov=$(PROJECT) tests/ --cov-fail-under=100
	@poetry run coverage-badge -o assets/images/coverage.svg -f
	@printf "\n"
#-----------------------------------------------------------------------------------------
# BUILD PACKAGE
#-----------------------------------------------------------------------------------------
.PHONY: build-package
build-package: ## Build as Package
	poetry build


#-----------------------------------------------------------------------------------------
# DOCKER
#-----------------------------------------------------------------------------------------
# Example: make docker-build VERSION=latest
# Example: make docker-build PROJECT=some_name VERSION=0.0.1
.PHONY: docker-build
docker-build: ## Build a docker image from Dockerfile
	@echo Building docker $(PROJECT):$(VERSION) ...
	docker build \
		-t $(PROJECT):$(VERSION) . \
		-f ./docker/Dockerfile --no-cache

# Example: make docker-remove VERSION=latest
# Example: make docker-remove PROJECT=some_name VERSION=0.0.1
.PHONY: docker-remove
docker-remove: ## Remove Docker Image
	@echo Removing docker $(PROJECT):$(VERSION) ...
	docker rmi -f $(PROJECT):$(VERSION)


#-----------------------------------------------------------------------------------------
# CLEANUP
#-----------------------------------------------------------------------------------------
.PHONY: cleanup
cleanup: pycache-remove dsstore-remove mypycache-remove ipynbcheckpoints-remove pytestcache-remove ## Complete Cleanup

.PHONY: pycache-remove
pycache-remove: ## Clean PyCache
	find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: dsstore-remove
dsstore-remove: ## Clean .DS_Store
	find . | grep -E ".DS_Store" | xargs rm -rf

.PHONY: mypycache-remove
mypycache-remove: ## Clean .mypy_cache
	find . | grep -E ".mypy_cache" | xargs rm -rf

.PHONY: ipynbcheckpoints-remove
ipynbcheckpoints-remove: ## Clean ipynb_checkpoints
	find . | grep -E ".ipynb_checkpoints" | xargs rm -rf

.PHONY: pytestcache-remove
pytestcache-remove: ## Clean pytest_cache
	find . | grep -E ".pytest_cache" | xargs rm -rf

.PHONY: build-remove
build-remove: ## Clean Builds
	rm -rf build/
	rm -rf build_linux/
	rm -rf build_win/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

#-----------------------------------------------------------------------------------------
# HELP
#-----------------------------------------------------------------------------------------
.PHONY: help
help: ## Self-documented Makefile
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
