# autochange

Lightweight semantic version + changelog manager.

## Features

- Maintain a markdown `CHANGELOG.md` with sections: Added, Changed, Deprecated, Removed, Fixed, Security.
- Add unreleased changes quickly.
- Release and automatically stamp date + version.
- Compute next semantic version via bump parts (major/minor/patch) or explicit version.

## Install

```
pip install autochange
```

#### Development dependencies

```
git clone https://github.com/clxrityy/autochange.git
cd autochange
pip install -e .[dev]
```

## Usage

```
autochange init               # create CHANGELOG.md
autochange add -t added "New feature" --scope api
autochange add -t fixed "Bug in parser"
autochange release minor      # bumps minor based on last release
```

## Changelog Format

Subset of Keep a Changelog. Example:

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

- Conventional commit parser integration.
- Auto-detect bump type from unreleased changes.
- Git tag creation helper.
- Export JSON.
