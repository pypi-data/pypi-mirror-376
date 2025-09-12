# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
The rules for this file:
  * entries are sorted newest-first.
  * summarize sets of changes - don't reproduce every git log comment here.
  * don't ever delete anything.
  * keep the format consistent:
    * do not use tabs but use spaces for formatting
    * 79 char width
    * YYYY-MM-DD date format (following ISO 8601)
  * accompany each entry with github issue/PR number (Issue #xyz)
-->
## [1.1.3] - 2025-09-11

### Authors
* @orbeckst
* @rjoshi44

### Fixed
* Fixed setting of gskip in ProcessProtein/cluster.py command line interface:
  set the default to 100 (as in the paper) and ensure that the correct value
  is used as Gibbs.gskip (which is relative to the save skip step of Gibbs.g)
  (Issue #48)

### Changed
The following changes do not functionally change the code but users relying
on default values need to be aware of the changes to gibbs.Gibbs.

* Default kwargs for the skipping in the Gibbs sampler are now
  gibbs.Gibbs(g=100, gskip=1) (used to be g=50, gskip=2) but for most users
  gskip for processing data is not important and it makes more sense to focus 
  on g as the stride at which we sample AND process data (#48, PR #49)
* internal code refactor and clean-up: moved util.run_residue() to
  gibbs.run_residue() and use direct assignment instead of setattr() (PR #50)

## [1.1.2] - 2025-07-22

### Authors
* @rjoshi44
* @copilot
* @orbeckst

### Fixed
* fixed contact script (issue #34)
* Fixed ProcessProtein command-line interface to accept gskip and burnin 
  parameters, resolving TypeError in script execution. Added --gskip and 
  --burnin arguments to cluster.py with default values from the research 
  paper (gskip=1000, burnin=10000) (Issue #37)
* Fixed ProcessProtein.write_data() method to handle residues as numpy array 
  instead of dictionary, resolving AttributeError when calling the method 
  after reprocess() or get_taus(). Also fixed get_taus() method to return 
  values as documented. Added comprehensive test coverage for write_data() 
  functionality (Issue #37)

 
## [1.1.1] - 2025-07-18

### Authors
* @rsexton2
* @orbeckst

## Changed
* The default name for the contacts file changed from "contacts.pkl" to
  "contacts_max10.0.pkl" as it now embeds the max_cutoff (Issue #27, PR #31)

## Fixed
* distinguished max_cutoff from cutoff in contact file metadata (Issues #27
  and #32) 


## [1.1.0] - 2025-07-04

### Authors
* @rsexton2
* @copilot
* @orbeckst

### Added
* Support for combining contact timeseries from multiple repeat runs through
  new `CombineContacts` class and `python -m basicrta.combine` CLI interface.
  Enables pooled analysis of binding kinetics data with metadata preservation
  and trajectory source tracking (Issue #16)

### Changed
* package has final paper citation



## [1.0.0] - 2025-05-24

### Authors
* @rsexton2
* @ianmkenney
* @rjoshi44
* @orbeckst

### Added
* added option processing for label-cutoff to cluster.py (PR #13)

### Fixed
* Fix package detection and installation (PR #12)
* fix citation in reST docs (PR #7)
* update codcov action in workflow (PR #9)

### Removed
* no testing on Windows, temporarily exclude windows-latest from CI (PR #11)

## [0.2.0] - 2024-11-14

### Authors
* @rsexton2

### Summary
Feature-complete release.

### Added
* Workflow executable through command-line
* updated docs/tutorial

