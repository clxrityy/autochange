# Changelog

All notable changes to this project will be documented in this file.

## Unreleased - UNRELEASED

## 0.1.1 - 2025-08-19

### Added

- Conventional commit parser and `import-commits` command (with tests)
- Property-based tests (Hypothesis)
- Tagging & release workflow: annotated tags plus flags `--commit`, `--push`, `--sign`, `--force-tag`, `--dirty-ok`
- Auto-bump inference (`release auto`) with rule: **major** if any `BREAKING`, otherwise **minor** if Added entries, else **patch**
- Integrated workflow: `autochange release auto --tag --commit --push` updates changelog, syncs `pyproject.toml`, commits, tags, pushes
- Automatic version synchronization to `pyproject.toml` on release
- Makefile improvements (bootstrap target, venv auto-detection) for developer convenience

## 0.1.0 - 2025-08-14

### Added

- Initialized project
