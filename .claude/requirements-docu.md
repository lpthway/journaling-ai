# AI Project Documentation Instructions

You are tasked with creating comprehensive, detailed documentation for any project you work on or modify. This documentation must be clear enough that you or another AI can understand the project's current state and continue working on it effectively in the future.

## Documentation Requirements

### 1. Project Overview Section
- **Project Name**: Clear, descriptive title
- **Purpose**: What the project does and why it exists
- **Current Status**: Working, in-progress, or broken with specific details
- **Technology Stack**: Languages, frameworks, libraries, tools used
- **Dependencies**: External packages, APIs, services required
- **Entry Points**: Main files, startup commands, or key functions

### 2. Architecture Documentation
- **Project Structure**: Directory/file organization with explanations
- **Data Flow**: How information moves through the system
- **Key Components**: Major modules, classes, or functions and their roles
- **Design Patterns**: Architectural decisions and patterns used
- **Configuration**: Environment variables, config files, settings

### 3. Change Log (CRITICAL)
For every modification you make, document:
- **Date/Time**: When the change was made
- **Type**: Bug fix, feature addition, refactoring, optimization, etc.
- **Files Modified**: Exact file paths and what was changed
- **Reason**: Why the change was necessary
- **Impact**: What other parts of the system might be affected
- **Before/After**: Code snippets showing key changes
- **Testing**: How the change was verified to work

### 4. Current Implementation Details
- **Functions/Methods**: Purpose, parameters, return values, side effects
- **Data Structures**: Classes, objects, database schemas
- **Algorithms**: Complex logic explained in plain language
- **API Endpoints**: Routes, methods, expected inputs/outputs
- **Database Operations**: Queries, migrations, data relationships

### 5. Known Issues and Limitations
- **Bugs**: Identified problems not yet fixed
- **Technical Debt**: Areas needing refactoring or improvement
- **Performance Issues**: Bottlenecks or inefficiencies
- **Missing Features**: Planned but not implemented functionality
- **Compatibility**: Browser, OS, or version limitations

### 6. Setup and Usage Instructions
- **Installation**: Step-by-step setup process
- **Configuration**: Required settings and customization options
- **Running the Project**: Commands to start/test/deploy
- **Common Tasks**: Frequent operations with exact commands
- **Troubleshooting**: Common problems and solutions

### 7. Development Guidelines
- **Code Style**: Formatting, naming conventions used
- **Testing Strategy**: How to write and run tests
- **Deployment Process**: How to release changes
- **Git Workflow**: Branching strategy, commit message format

## Writing Guidelines

### Clarity and Precision
- Use specific, technical language when necessary
- Include exact file paths, function names, and line numbers
- Provide code snippets for complex explanations
- Use consistent terminology throughout

### Future AI Readability
- Assume the reader has no prior knowledge of this specific project
- Explain the reasoning behind decisions, not just what was done
- Include context about why certain approaches were chosen
- Link related concepts and dependencies

### Maintenance Focus
- Make it easy to identify what needs updating when requirements change
- Clearly mark deprecated or outdated sections
- Include version information for all dependencies
- Document any workarounds or temporary solutions

### Structure and Organization
- Use clear headings and subheadings
- Include a table of contents for long documents
- Cross-reference related sections
- Keep information in logical, scannable chunks

## Documentation Structure and Organization

### Recommended Folder Structure
docs/
├── README.md # Main project overview and quick start
├── CHANGELOG.md # Chronological list of all changes
├── architecture/
│ ├── overview.md # High-level system design
│ ├── data-flow.md # Data flow diagrams and explanations
│ ├── components.md # Detailed component documentation
│ └── decisions.md # Architectural decision records (ADRs)
├── setup/
│ ├── installation.md # Step-by-step installation guide
│ ├── configuration.md # Configuration options and examples
│ ├── development.md # Development environment setup
│ └── deployment.md # Production deployment guide
├── api/
│ ├── endpoints.md # API endpoint documentation
│ ├── authentication.md # Auth mechanisms and flows
│ ├── examples.md # Request/response examples
│ └── changelog.md # API version changes
├── database/
│ ├── schema.md # Database structure and relationships
│ ├── migrations.md # Migration history and notes
│ └── queries.md # Common queries and procedures
├── code/
│ ├── modules/ # Per-module documentation
│ │ ├── auth.md
│ │ ├── user-management.md
│ │ └── data-processing.md
│ ├── functions.md # Key functions and their purposes
│ └── classes.md # Class documentation
├── operations/
│ ├── monitoring.md # Logging, metrics, alerts
│ ├── troubleshooting.md # Common issues and solutions
│ ├── backup.md # Backup and recovery procedures
│ └── security.md # Security considerations and practices
├── testing/
│ ├── strategy.md # Testing approach and standards
│ ├── unit-tests.md # Unit testing guidelines
│ ├── integration-tests.md # Integration testing setup
│ └── test-data.md # Test data management
└── resources/
├── glossary.md # Terms and definitions
├── references.md # External links and resources
├── templates/ # Code templates and examples
└── diagrams/ # Architecture diagrams and flowcharts


### File Naming Conventions
- Use lowercase with hyphens: `user-authentication.md`
- Be descriptive and specific: `database-migration-guide.md` not `db.md`
- Include version numbers when relevant: `api-v2-endpoints.md`
- Use consistent prefixes for related files: `setup-`, `troubleshooting-`, etc.

### Core Documentation Files

#### README.md (Project Root)
```markdown
# Project Name

Brief description and purpose

## Quick Start
- Installation: `npm install`
- Run: `npm start`
- Test: `npm test`

## Documentation Structure
- [Full Documentation](./docs/README.md)
- [API Documentation](./docs/api/)
- [Setup Guide](./docs/setup/)
- [Architecture Overview](./docs/architecture/)

## Recent Changes
See [CHANGELOG.md](./CHANGELOG.md) for detailed history.

## Support
- Issues: Link to issue tracker
- Documentation: Link to docs folder

docs/README.md (Documentation Index)
# Project Documentation

## Getting Started
1. [Installation Guide](./setup/installation.md)
2. [Configuration](./setup/configuration.md)
3. [Architecture Overview](./architecture/overview.md)

## For Developers
- [Development Setup](./setup/development.md)
- [Code Structure](./code/)
- [Testing Guidelines](./testing/)

## For Operations
- [Deployment](./setup/deployment.md)
- [Monitoring](./operations/monitoring.md)
- [Troubleshooting](./operations/troubleshooting.md)

## Reference
- [API Documentation](./api/)
- [Database Schema](./database/)
- [Glossary](./resources/glossary.md)

CHANGELOG.md Format
# Changelog

## [Unreleased]
### Added
- New feature descriptions

### Changed
- Modified functionality

### Fixed
- Bug fixes

### Removed
- Deprecated features

## [1.2.0] - 2024-08-05
### Added
- User authentication system
- Password reset functionality

### Changed
- Updated database schema for user roles
- Improved error handling in API endpoints

### Technical Details
- Modified files: `src/auth.js`, `src/database/users.sql`
- Database migration: `migrations/003_add_user_roles.sql`
- New dependencies: `bcrypt`, `jsonwebtoken`

## Output Format

Create documentation in markdown format with:

- Clear hierarchy using proper heading levels
- Code blocks with syntax highlighting
- Tables for structured data
- Links to external resources
- Inline code formatting for file names, commands, variables
- Cross-references between related documentation files

## Documentation Management Best Practices

### File Organization Principles
- **Logical Grouping**: Related documentation stays together
- **Progressive Disclosure**: Start with overview, drill down to details
- **Single Source of Truth**: Each piece of information has one authoritative location
- **Consistent Navigation**: Similar structure across all documentation sections

### Cross-Referencing Strategy
- **Internal Links**: Use relative paths to link between docs
- **Index Pages**: Each folder should have a README.md or index.md
- **Breadcrumbs**: Include navigation context in each file
- **Tags and Categories**: Use consistent tagging for searchability

### Documentation Maintenance

#### Daily Practices
- Update relevant docs immediately after code changes
- Add entries to CHANGELOG.md for every modification
- Check and update cross-references when moving or renaming files

#### Weekly Reviews
- Verify all links are working
- Check for outdated information
- Update status indicators and progress markers

#### Monthly Audits
- Review and reorganize file structure if needed
- Archive or remove obsolete documentation
- Update dependency versions and compatibility notes

### Version Control Integration

#### Git Integration
```bash
# Documentation-specific commits
git commit -m "docs: update API endpoint documentation"
git commit -m "docs: add troubleshooting guide for user auth"

# Documentation branches for major updates
git checkout -b docs/api-v2-documentation

### Documentation Versioning
- Keep docs in sync with code versions
- Tag documentation releases: `docs-v1.2.0`
- Maintain compatibility matrices for different versions

## Update Protocol

When modifying existing documentation:
- Update the relevant sections immediately after making code changes
- Add new entries to the change log with timestamps
- Review and update the "Current Status" section
- Check if architecture or setup instructions need updates
- Verify that all file paths and references are still accurate
- Update cross-references and internal links
- Rebuild any generated documentation or diagrams

## Quality Checklist

Before finalizing documentation, ensure:
- [ ] A new AI could understand the project's purpose and structure
- [ ] All recent changes are documented with sufficient detail
- [ ] Setup instructions are complete and tested
- [ ] Known issues are clearly identified
- [ ] Code examples are accurate and functional
- [ ] External dependencies are properly documented
- [ ] The documentation reflects the current state of the code

Remember: This documentation is your project's memory. Make it comprehensive enough that you can pick up where you left off months later, and detailed enough that another AI can contribute meaningfully to the project.
