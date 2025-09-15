# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-09-15

### Added
- 🔧 **Enhanced Installation Methods**:
  - Method 4: Clone Repository option for development/local setup
  - Improved npx wrapper with `--project-dir` argument support
  - UV (Universal Python Installer) installation method
- 📁 **Smart Project Detection**: Auto-detection of project workspace when using npx
- 🎯 **Cross-Platform Compatibility**: Enhanced macOS support with virtual environment handling
- 📊 **Performance Improvements**: Better error handling and dependency management

### Enhanced
- 🔍 **Improved Path Resolution**: Fixed npx execution context issues on macOS
- 🐍 **Python Environment Handling**: Better virtual environment detection and creation
- 📝 **Documentation**: Comprehensive README updates with all installation methods
- 🛡️ **Error Handling**: Enhanced error messages and troubleshooting guides

### Fixed
- 🔧 **macOS NPX Issues**: Resolved "externally-managed-environment" errors on macOS Homebrew Python
- 📂 **Project Path Detection**: Fixed workspace detection when running via npx from different directories
- 🐛 **Virtual Environment**: Improved .venv creation and Python executable detection
- 💾 **Dependency Installation**: Enhanced pip installation process with better error handling


## [1.1.0] - 2025-07-01

### Added
- Initial release of Robot Framework MCP Server
- Basic test case generation for login functionality
- Page object model creation
- Advanced Selenium keywords generation
- Performance monitoring test templates
- Data-driven test creation
- API integration test generation
- Input validation and security features
- Multiple selector template support (appLocator, generic, bootstrap)
- Robot Framework syntax validation
