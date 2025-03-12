PYMODULE := trestlebot
E2E := e2e
TESTS := tests

all: develop lint test
.PHONY: all

develop: pre-commit
	@poetry install --with tests,dev
	@poetry shell
.PHONY: develop

pre-commit:
	@poetry run pre-commit install

lint:
	@poetry check --lock
	@poetry run isort --profile=black --lines-after-imports=2 \
	--check-only $(TESTS) $(PYMODULE)
	@poetry run black --check $(TESTS) $(PYMODULE) --diff
	@poetry run mypy $(PYMODULE) $(TESTS)
	@poetry run flake8
.PHONY: lint

format:
	@poetry run isort --profile=black --lines-after-imports=2 $(TESTS) $(PYMODULE)
	@poetry run black $(TESTS) $(PYMODULE)
.PHONY: format

test:
	@poetry run pytest --cov --cov-config=pyproject.toml --cov-report=xml
.PHONY: test

test-slow:
	@poetry run pytest --slow --cov --cov-config=pyproject.toml --cov-report=xml
.PHONY: test-slow

test-e2e:
	@poetry run pytest $(TESTS)/$(E2E) --slow --cov --cov-config=pyproject.toml --cov-report=xml
.PHONY: test-e2e

test-int:
	@poetry run pytest tests/integration --slow --cov --cov-config=pyproject.toml --cov-report=xml
.PHONY: test-int

test-code-cov:
	@poetry run pytest --cov=trestlebot --exitfirst --cov-config=pyproject.toml --cov-report=xml --cov-fail-under=80
.PHONY: test-code-cov

# https://github.com/python-poetry/poetry/issues/994#issuecomment-831598242
# Check for CVEs locally. For continuous dependency updates, we use dependabot.
dep-cve-check:
	@poetry export -f requirements.txt --without-hashes | poetry run safety check --continue-on-error --stdin
.PHONY: dep-cve-check

security-check:
	@poetry run pre-commit run semgrep --all-files
.PHONY: security-check

build: clean-build
	@poetry build
.PHONY: build

clean-build:
	@rm -rf dist
.PHONY: clean-build

clean:
	@git clean -Xdf
.PHONY: clean

publish:
	@poetry config pypi-token.pypi $(PYPI_TOKEN)
	@poetry publish --dry-run
	@poetry publish
.PHONY: publish

build-and-publish: build publish
.PHONY: build-and-publish

update-action-readmes:
	@poetry run python scripts/update_action_readmes.py
.PHONY: update-action-readmes
