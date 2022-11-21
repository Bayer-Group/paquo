# paquo changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
...

## [0.6.0] - 2022-11-21
### Fixed
- paquo: support windows network share URIs
- paquo: add all available scenes of image in `add_image`

### Added
- paquo: support snapshot versions of QuPath for testing newer upstream compatibility
- paquo: allow user to provide path to JVM to support Apple M1 hardware
- paquo: add `remove_image` method to QuPathProject

### Changed
- paquo: simplify ImageProvider and deprecate SimpleImageProvider
- ci: install paquo via pip to speedup workflows
- ci: test against python 3.11

## [0.5.1] - 2022-07-15
### Fixed
- paquo: env var configuration now works via `PAQUO_` and `PAQUO__` prefix

## [0.5.0] - 2022-04-05
### Fixed
- cli: startup time improved
- docs: fix configuration section (double underscore for prefix `PAQUO__`)
- paquo.java: prevent emitting a QuPath logging message on import
- paquo: reduce cli startup time by lazy importing settings
- cli: fixed help display if terminal doesn't support unicode

### Added
- cli: add get_qupath command for downloading specific QuPaths

### Changed
- paquo: drop Python=3.6 support

## [0.4.2] - 2022-01-10
### Added
- paquo: support QuPath v0.2.0 (a83d8a2)

### Fixed
- paquo._config: fixed searchtree to allow local override
- tests: fixed jpype test when run in conda env with external QuPath

### Changed
- paquo: multiple typing improvements and minor fixes

## [0.4.1] - 2022-01-05
### Added
- paquo: emit warning on windows when MicrosoftStore Python is detected

### Fixed
- paquo: fixed EXCEPTION_ACCESS_VIOLATION on Windows with QuPath versions 0.3.x
- paquo: removed distutils.version usage to silence warnings on py39+ (pep632)

## [0.4.0] - 2021-08-25
### Added
- paquo: support qupath version 0.3.0-rc1
- paquo.hierarchy: no_autoflush context manager for speeding up adding many path objects
- paquo.projects: support try_relative in update_image_paths
- cli: allow providing both --annotations and --annotations-cmd
- paquo.hierarchy: support conversion to ome xml
- docs: quickstart example for loading detection measurements as pd.DataFrame (@nickdelgrosso)

### Changed
- paquo._base: remove QuPathBase base class

### Fixed
- paquo.hierarchy: improved update_class_path speed
- paquo.hierarchy: support slicing for annotation and detection proxies
- paquo.hierarchy: fixed proxy issue after load_geosjon
- paquo.projects: speedup add_image for large projects

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


[Unreleased]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.4.2...v0.5.0
[0.4.2]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/bayer-science-for-a-better-life/paquo/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/bayer-science-for-a-better-life/paquo/tree/v0.1.0
