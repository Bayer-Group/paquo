# paquo changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
...

## [0.3.1] - 2021-04-02
### Fixed
- paquo: changing annotations in a hierarchy now propagates to is_changed

## [0.3.0] - 2021-03-29
### Added
- cli: added qpzip subcommand that allows opening zipped QuPath projects
- cli: added quickview subcommand for opening qupath with a specific image
- cli: quickview subcommand support loading annotations
- extras: added an example for an osx app shim allowing paquo to be used as an OSX app

### Changed
- switched conda env to conda-devenv
- changed repr style of paquo classes
- conda env doesn't use defaults anymore

### Fixed
- paquo._logging: paquo doesn't call basicConfig anymore
- paquo: fixed java logging redirection in images and projects
- paquo: hierarchy now skips broken annotations
- paquo: hierarchy annotation loading speedup
- mypy: fixes

## [0.2.0] - 2020-08-21
### Added
- more verbose logging when saving project data

### Changed
- updated the docs

### Fixed
- parse windows network share URIs correctly

## [0.1.1] - 2020-08-12
### Added
- added verbose repr's for improved ipython notebook display

### Fixed
- excluded broken dynaconf==3.1.0
- `QuPathProject.add_image` is now calling `QuPathProject.save`

## [0.1.0] - 2020-08-12
### Added
- initial release of paquo


[Unreleased]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/bayer-science-for-a-better-life/paquo/tree/v0.1.0

