# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6] - 2025-01-15

### Added
- Enhanced metadata detection to support `Base.metadata` from SQLAlchemy declarative base
- Automatic detection of metadata from `Base.metadata` (most common SQLAlchemy pattern)
- Support for three metadata patterns: `metadata`, `MetaData`, and `Base.metadata`

### Improved
- Updated examples to show cleaner `Base.metadata` pattern as recommended approach
- Better error messages with examples for all supported metadata patterns
- More intuitive auto-migration workflow for standard SQLAlchemy applications

### Fixed
- Fixed `set_database_url()` to properly parse and save database configuration components
- Fixed config file showing null values when using programmatic database URL setting
- Database URL components (host, port, user, database, db_type) are now correctly saved to config file

## [0.1.5] - 2025-01-15

### Fixed
- Fixed `set_database_url()` to properly parse and save database configuration components
- Fixed config file showing null values when using programmatic database URL setting
- Database URL components (host, port, user, database, db_type) are now correctly saved to config file

## [0.1.4] - 2025-01-15

### Fixed
- Fixed database driver validation to provide helpful error messages when drivers are missing
- Fixed import references from `migrateDB` to `dbPorter` in example files and docstrings
- Improved error messages for missing database drivers (MySQL, PostgreSQL, etc.)
- Fixed SQLite URL validation to handle URLs without hostname components

### Improved
- Better user experience when database drivers are not installed
- Clear installation instructions in error messages
- Updated example files to use correct package imports

## [Unreleased]

### Added
- Initial release of dbPorter
- YAML-based declarative migrations
- Python-based programmatic migrations
- Migration Graph (DAG) support with dependency management
- Automatic rollback with metadata preservation
- Schema auto-generation from SQLAlchemy models
- Support for multiple databases (SQLite, PostgreSQL, MySQL, SQL Server, Oracle)
- Comprehensive status inspection with visual indicators
- Programmatic configuration for security-conscious organizations
- Table rename support with mapping configuration
- Dry-run capability for safe migration preview
- Conflict detection for parallel development
- Branch management and merging capabilities

### Features
- **Dual Migration Support**: Both YAML and Python migration formats
- **Advanced DAG System**: Branching migrations with dependency tracking
- **Schema Inspection**: Comprehensive database and migration status reporting
- **Security-First**: Programmatic configuration without credential files
- **Multi-Database**: Support for all major SQLAlchemy-compatible databases
- **Developer Experience**: One-time configuration, visual indicators, comprehensive CLI

## [0.1.0] - 2024-01-13

### Added
- Initial release
- Core migration functionality
- CLI interface with Typer
- SQLAlchemy integration
- YAML migration file support
- Python migration file support
- Basic rollback functionality
- Database connection management
- Migration logging and tracking

### Technical Details
- Python 3.8+ support
- SQLAlchemy 2.0+ compatibility
- Typer-based CLI interface
- YAML configuration support
- Environment variable configuration
- Auto-discovery of database connections
