# 🔧 Tools and Utilities

This document tracks tools and utilities that were part of this project but have been moved to separate repositories for better maintainability.

## Extracted Tools

### AI Code Analyzer

**Status**: ✅ Extracted to standalone project  
**Original Location**: `tools/ai-code-analyzer/`  
**New Location**: `/home/abrasko/Projects/ai-code-analyzer`  
**Extraction Date**: August 8, 2025

**Description**: 
An intelligent, modular code analysis framework powered by multiple LLMs with advanced quota management and resume capabilities.

**Key Features**:
- Multi-LLM support (Claude, GPT-4, local models)
- Intelligent quota management with timezone-aware scheduling
- Resume capabilities for interrupted analyses
- Plugin-based analyzer system
- Beautiful terminal UI with rich progress indicators
- Type-safe configuration with Pydantic

**Why Extracted**:
The AI Code Analyzer was a complete, standalone tool that could benefit other projects beyond journaling-ai. By extracting it to its own repository, we:
- Avoid conflicts with journaling-ai development
- Allow independent versioning and releases
- Enable broader community contributions
- Reduce the complexity of the main project

**How to Use**:
```bash
# Clone the standalone project
cd /home/abrasko/Projects/ai-code-analyzer

# Install and use
pip install -e .
ai-analyzer analyze /path/to/project
```

## Tool Migration Guidelines

When considering whether to extract a tool to a standalone project:

1. **Standalone Value**: Can the tool benefit other projects?
2. **Complexity**: Is the tool complex enough to warrant its own repo?
3. **Dependencies**: Does it have unique dependencies that conflict with the main project?
4. **Maintenance**: Would separate maintenance be more efficient?
5. **Community**: Could it attract its own community of contributors?

If the answer to most of these is "yes", consider extraction.

## Integration Points

### From journaling-ai to AI Code Analyzer
- The journaling-ai project can still use AI Code Analyzer as an external tool
- Run analyses on the journaling-ai codebase using the standalone analyzer
- No direct code dependencies remain

### Future Extracted Tools
Document any future tool extractions here following the same pattern.

---

*Last updated: August 8, 2025*
