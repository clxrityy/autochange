# autochange

Lightweight semantic version + changelog manager.

## Features

- Maintain a markdown `CHANGELOG.md` with sections: Added, Changed, Deprecated, Removed, Fixed, Security.
- Add unreleased changes quickly.
- Release and automatically stamp date + version.
- Compute next semantic version via bump parts (major/minor/patch) or explicit version.
- Import Conventional Commits directly into the unreleased section.

## Install

```zsh
pip install autochange
```

#### Development dependencies

```zsh
pip install -e .[dev]
```

## Usage

```zsh
autochange init               # create CHANGELOG.md
autochange add -t added "New feature" --scope api
autochange add -t fixed "Bug in parser"
autochange release minor      # bumps minor based on last release
autochange release auto --tag --commit --push  # infer bump from changes, commit, tag and push
autochange import-commits --since v0.1.0  # parse commits after tag v0.1.0
autochange tag                # create git tag for latest released version
autochange tag 1.2.3 --push   # create & push tag v1.2.3
```

## Changelog Format

Subset of [Keep a Changelog](https://keepachangelog.com). Example:

```
# Changelog

## Unreleased - UNRELEASED
### Added
- (api) New feature

## 0.1.0 - 2025-08-13
### Fixed
- Parser bug
```

## Roadmap

- [x] Conventional commit parser integration.
- [x] Auto-detect bump type from unreleased changes.
- [x] Git tag creation helper.
- [ ] Export JSON.
- [ ] Supporting different environments (e.g. package.json, Cargo.toml).
