# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2025-09-11

### Added

- Enhanced developer documentation and added a contribution guide.
- Added a demo video to the documentation and updated linting rules.

### Fixed

- Improved handling of links with spaces in angle brackets in the graph.
- Modernized the documentation deployment workflow and fixed broken links.

### Changed

- Replaced the demo video with a more lightweight animated GIF.
- Updated the project logo with a new network-graph-themed design.

## [1.0.0] - 2025-08-21

### Added

- Interactive graph visualization for MkDocs documentation
- Dual view modes: full-site overview and local page connections
- Seamless integration with Material for MkDocs themes
- Configurable node naming strategies (`title` or `file_name`)
- Debug logging support for development
- Extensive CSS customization via CSS variables
- Responsive design for desktop and mobile devices
- D3.js-powered interactive graph rendering
- Performance-optimized lightweight implementation

### Configuration Options

- `name`: Node naming strategy configuration
- `debug`: Debug logging toggle

### CSS Variables

- `--md-graph-node-color`: Default node color
- `--md-graph-node-color--hover`: Node hover color
- `--md-graph-node-color--current`: Current page node color
- `--md-graph-link-color`: Connection line color
- `--md-graph-text-color`: Node label text color

### Documentation

- Comprehensive documentation site
- Getting started tutorial
- Configuration reference
- Customization guide
- Developer contribution guide

### Development

- Python 3.10+ support
- Material for MkDocs v9.0.0+ compatibility
- Automated testing with pytest
- Code quality tools (ruff, pyright)
- Pre-commit hooks
- GitHub Actions CI/CD pipeline
- Development environment setup with uv
