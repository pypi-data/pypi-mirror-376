---
description: Build distribution package
argument-hint: [target platform]
---

Build distribution package: $ARGUMENTS

1. Clean previous builds
2. Run linting and formatting
3. Execute test suite
4. Update version number
5. Build package/binary
6. Generate checksums
7. Create release artifacts
8. Build documentation

Build targets:
- Source distribution
- Wheel (Python)
- Binary executables
- Cross-platform builds
- Docker images
- Homebrew formula