# Changelog

All notable changes to the Journaling AI project will be documented in this file.

## [Unreleased]

### Refactored - 2025-08-05
- **Enhanced AI Service Cleanup**: Removed unused hardware-adaptive AI system components
  - Simplified `enhanced_ai_service.py` by removing 80KB+ of dead code
  - Eliminated commented-out imports and references to non-existent modules
  - Streamlined service initialization and memory management
  - Renamed methods for consistency (`refresh_hardware_adaptive_models` → `refresh_models`)
  - Added missing imports (`time`) and method implementations (`_generate_contextual_prompts`)
  - Maintained all core AI functionality (tag suggestions, mood prediction, smart prompts)
  - Created comprehensive backup with restoration instructions in `backup/unused-hardware-adaptive-ai/`
  - **Impact**: Improved code maintainability and reduced complexity without functionality loss
  - **Files Modified**: `backend/app/services/enhanced_ai_service.py`
  - **Documentation**: [Enhanced AI Service Cleanup](./docs/code/enhanced-ai-service-cleanup.md)

### Technical Details - 2025-08-05
- **Compilation**: All Python syntax validation passed
- **Testing**: Basic service initialization and method accessibility verified  
- **Memory Management**: Simplified to use PyTorch native CUDA memory management
- **Hardware Detection**: Maintained GPU VRAM-based tier detection (HIGH_END/INTERMEDIATE/BASIC/MINIMAL)
- **Backup**: Complete system backed up with full restoration documentation

---

## Previous Changes

*Note: This changelog was created as part of the documentation standardization effort. Previous changes may be found in git commit history and individual documentation files.*

## Change Categories

- **Added**: New features and functionality
- **Changed**: Modifications to existing features  
- **Deprecated**: Features marked for future removal
- **Removed**: Deleted features and code
- **Fixed**: Bug fixes and corrections
- **Security**: Security-related changes
- **Refactored**: Code improvements without functionality changes
- **Technical**: Infrastructure, build, or tooling changes

## Documentation Standards

Each significant change should include:
- Clear description of what changed
- Reasoning behind the change
- Impact on users and developers
- Files modified with specific details
- Testing and verification performed
- Links to detailed documentation
