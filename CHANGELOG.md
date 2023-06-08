# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Unreleased] - yyyy-mm-dd

### Added

### Changed

### Fixed

## [0.4.2] - 2023-06-08

### Changed

- Changed measurements default to 50K items

## [0.4.1] - 2023-06-08

### Changed

- Measurements are now run against aiosqlite

## [0.4.0] - 2023-06-06

### Added

- `keys_iterator()` return an async iterator to loop over all keys.
- The DBM exception tuple `dbm.error` is now passed through

### Changes

- Improved docs

## [0.3.0] - 2023-06-05

### Changed

- Moved thread related code into own module for better separation of concerns.

## [0.2.0] - 2023-06-05

### Added

- Initial release
