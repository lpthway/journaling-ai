# 🛠️ Tools Directory

This directory contains tools and utilities for the journaling-ai project.

## Directory Status

Currently empty - tools have been extracted to standalone projects for better maintainability.

## Extracted Tools

See [EXTRACTED_TOOLS.md](../docs/EXTRACTED_TOOLS.md) for information about tools that were moved to separate repositories.

## Adding New Tools

When adding new tools to this directory, consider:

1. **Scope**: Is this tool specific to journaling-ai or could it be useful elsewhere?
2. **Complexity**: Simple scripts can live here, complex tools should be standalone
3. **Dependencies**: Avoid tools with heavy dependencies that conflict with the main project
4. **Maintenance**: Consider the long-term maintenance burden

### Guidelines for Tool Placement

**Keep in tools/ if**:
- Simple utility scripts (< 500 lines)
- Highly specific to journaling-ai
- Minimal dependencies
- Quick development aids

**Extract to standalone project if**:
- Complex tool with multiple modules
- Could benefit other projects
- Has unique dependency requirements
- Warrants its own testing/documentation
- Could attract external contributors

---

*For extracted tools documentation, see [EXTRACTED_TOOLS.md](../docs/EXTRACTED_TOOLS.md)*
