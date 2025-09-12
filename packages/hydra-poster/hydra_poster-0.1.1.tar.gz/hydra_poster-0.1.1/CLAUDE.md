# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python library for reliable social media posting across multiple platforms (Twitter, LinkedIn, Reddit, GitHub, Bluesky, Ghost) with comprehensive threading support. Designed for simplicity and use by AI coding agents.

## Core Architecture

### Design Principles
- **Stateless operations** - no persistent state between calls
- **All-or-nothing posting** - automatic rollback on failures  
- **Pre-validation** - fail fast with comprehensive error reporting
- **Platform authenticity** - preserve platform-specific credential handling
- **Simplicity first** - easy to use, especially for AI coding agents

### Key Components
- `SocialMediaService` - Abstract base class with `post()` and `validate_media()` methods
- `MediaItem` - Unified media abstraction supporting URLs, file paths, and raw bytes
- `PostResult` / `ThreadResult` - Structured response objects with platform-specific metadata
- Platform-specific services (TwitterService, BlueSkyService, etc.)

### Threading Architecture
- **Twitter**: Reply-chain model with tweet deletion for rollback
- **Bluesky**: AT Protocol with URI/CID references and proper root/parent linking
- Sequential posting with comprehensive rollback support
- Media validation per tweet/post in threads

## Development Commands

```bash
# Development setup
make install                # Install all dependencies
uv add package-name         # Add new dependency
uv add --dev package-name   # Add dev dependency

# Testing
make test                   # Run fast tests (default - excludes slow tests)
make test-all               # Run all tests including slow ones
make test-slow              # Run only slow tests
make test-cov               # Run fast tests with coverage report
uv run pytest tests/test_twitter.py::test_specific_function  # Run specific test

# Code Quality
make lint                   # Run ruff linting
make format                 # Run ruff formatting
make type-check             # Run mypy type checking
make ci                     # Run all CI checks (lint, format-check, type-check, test)

# Pre-commit (runs automatically on commit)
uv run pre-commit install   # Setup hooks
uv run pre-commit run --all-files  # Run all hooks manually

# Build and package
make build                  # Build the package
make clean                  # Clean up cache files and build artifacts
```

## Implementation Notes

### Media Validation Pipeline
1. Format validation - check MediaItem structure
2. Content accessibility - download URLs, verify file paths
3. Platform limits - check file sizes, counts, formats
4. Content normalization - convert all inputs to bytes

### Error Handling
- Comprehensive exception hierarchy with `SocialMediaError` base
- Platform-specific exceptions (TwitterError, BlueSkyError, etc.)
- Detailed validation errors with actionable guidance
- Media-specific error identification

### Platform-Specific Considerations
- **Twitter**: 500 posts/month free tier limit, rollback consumes quota
- **Bluesky**: More permissive rate limits, AT Protocol URI/CID handling
- **All platforms**: Two-phase upload process (upload media, then create post)

## Specifications

Detailed specifications are available in:
- `social_media_library_spec.md` - Core library architecture
- `twitter_threading_spec.md` - Twitter threading implementation
- `bluesky_threading_spec.md` - Bluesky threading implementation