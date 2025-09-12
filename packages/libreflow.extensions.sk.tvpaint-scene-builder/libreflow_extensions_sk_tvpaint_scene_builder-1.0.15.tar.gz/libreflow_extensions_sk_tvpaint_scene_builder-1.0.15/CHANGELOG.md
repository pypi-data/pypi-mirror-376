# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)[^1].

<!---
Types of changes

- Added for new features.
- Changed for changes in existing functionality.
- Deprecated for soon-to-be removed features.
- Removed for now removed features.
- Fixed for any bug fixes.
- Security in case of vulnerabilities.

-->

## [Unreleased]

## [1.0.15] - 2025-09-12

# Changed
* For the upcoming posing builds : layer groups "Notes & Corrections" (index 8) and "Guides & References" (index 10) are renamed "Notes to forward" and "Temp Notes for WIP" respectively



### Added
* On create default file: 
    - Tvpaint layers tagged "temp notes for wip" (index 10) get removed to clean up the file
    - Animatic gets updated if not up to date


## [1.0.14] - 2025-09-05

### Fixed
* Made the source versions non-editable by users

## [1.0.13] - 2025-08-11

### Added
* On the first opening of the file in any task after posing, the source dependencies data will be fetched from the previous task

## [1.0.12] - 2025-07-30

### Fixed
* Masked the create file action in Tasks where it is not needed

## [1.0.11] - 2025-07-29

### Fixed
* Removed whitespace filtering needed for the extendscript version of the action

## [1.0.10] - 2025-06-26

### Fixed

* Audio Import working properly
* Extended path for the importation of modules in venv

## [1.0.9] - 2025-06-12

### Fixed

* Defaulting color_source_name to None

## [1.0.8] - 2025-05-15

### Added

* Animatic support for updating

## [1.0.7] - 2025-05-09

### Changed

* the builder and the updater will now import the bg_color as a single image

### Fixed

* the trigger for the updater to publish is now the closing of the TvPaint instance instead of the python process' end

## [1.0.6] - 2025-04-28

### Fixed

* hotfix - redirection to task oid after quitting the action's oid

## [1.0.5] - 2025-04-28

### Added

* Opening a tvpaint file in Posing will check if the bg_layout and bg_color on the last revision are up to date (does not work when directly opening a revision from the file history)

* Importing animatic on build

### Fixed

* Batch Reload Audio will ignore existing revisions that are not available locally

### Changed

* functions get_animatic_path and get_source_path in the Create_TVPaint_File class are merged since they do the same thing

## [1.0.4] - 2025-04-18

### Fixed

* Keep Tvpaint open when build is finished

## [1.0.3] - 2025-04-18

### Fixed

* Properly packing scripts in extension

## [1.0.2] - 2025-04-18

### Added

* Readable logs in TVPaint script

### Fixed

* Use BG Color group at import

## [1.0.1] - 2025-04-04

### Added

* automatic creation of layer groups

### Fixed

* bg_color layer folder will not be mandatory anymore to build a project

## [1.0.0] - 2025-03-07

### Added

* Extension to build a tv paint project and import the layers from the bg_layout and bg_color tasks
