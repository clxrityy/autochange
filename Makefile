PYTHON ?= python
PACKAGE = autochange
SRC_DIR = src

.PHONY: help install dev test lint build clean release version bump-major bump-minor bump-patch ensure-build ensure-twine

help:
	@echo 'Common targets:'
	@echo '  make install     - standard install (no extras)'
	@echo '  make dev         - editable install with dev extras'
	@echo '  make test        - run pytest'
	@echo '  make build       - build sdist & wheel'
	@echo '  make release VER=X.Y.Z  - tag + build + upload (requires twine, sets version in pyproject)'
	@echo '  make bump-major|bump-minor|bump-patch - update version in pyproject.toml'

install:
	$(PYTHON) -m pip install .

dev:
	$(PYTHON) -m pip install -e '.[dev,release]'

TEST_ARGS ?=

test:
	$(PYTHON) -m pytest -q $(TEST_ARGS)

ensure-build:
	@$(PYTHON) -c "import importlib.util, subprocess, sys; mod='build'; print('Ensuring build available...'); importlib.util.find_spec(mod) or subprocess.check_call([sys.executable,'-m','pip','install','build'])"

ensure-twine:
	@$(PYTHON) -c "import importlib.util, subprocess, sys; mod='twine'; print('Ensuring twine available...'); importlib.util.find_spec(mod) or subprocess.check_call([sys.executable,'-m','pip','install','twine'])"

build: ensure-build
	$(PYTHON) -m build

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache pip-wheel-metadata

# Simple version bump helpers (semantic). These edit pyproject.toml in-place.
# They assume version line format: version = "X.Y.Z"

CURRENT_VERSION := $(shell grep '^version = ' pyproject.toml | sed -E 's/version = "([0-9]+\.[0-9]+\.[0-9]+)"/\1/')
MAJOR := $(word 1,$(subst ., ,$(CURRENT_VERSION)))
MINOR := $(word 2,$(subst ., ,$(CURRENT_VERSION)))
PATCH := $(word 3,$(subst ., ,$(CURRENT_VERSION)))

bump-major:
	@NEW_VER=$$(printf '%s.%s.%s' $$((MAJOR+1)) 0 0); \
	sed -i '' -E "s/version = \"$(CURRENT_VERSION)\"/version = \"$$NEW_VER\"/" pyproject.toml; \
	echo Bumped to $$NEW_VER

bump-minor:
	@NEW_VER=$$(printf '%s.%s.%s' $(MAJOR) $$((MINOR+1)) 0); \
	sed -i '' -E "s/version = \"$(CURRENT_VERSION)\"/version = \"$$NEW_VER\"/" pyproject.toml; \
	echo Bumped to $$NEW_VER

bump-patch:
	@NEW_VER=$$(printf '%s.%s.%s' $(MAJOR) $(MINOR) $$((PATCH+1))); \
	sed -i '' -E "s/version = \"$(CURRENT_VERSION)\"/version = \"$$NEW_VER\"/" pyproject.toml; \
	echo Bumped to $$NEW_VER

# release: VER=1.2.3 (explicit)
release: test clean build ensure-twine
ifndef VER
	$(error Specify VER=X.Y.Z)
endif
	@sed -i '' -E "s/version = \"$(CURRENT_VERSION)\"/version = \"$(VER)\"/" pyproject.toml
	@git add pyproject.toml CHANGELOG.md
	@git commit -m "release: $(VER)" || true
	@git tag v$(VER)
	$(PYTHON) -m twine upload dist/*
	@git push --follow-tags

version:
	@echo $(CURRENT_VERSION)
