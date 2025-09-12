# Development Tools

This directory contains development and testing tools for the social media posting library.

## Contents

### `cli.py` - Professional Testing CLI

A comprehensive command-line interface for testing the social media posting library across all platforms.

**Features:**
- **Multi-platform support** - Test Twitter, Bluesky, LinkedIn, Reddit, or all platforms at once
- **Threading support** - Create threaded posts with `--threaded` flag
- **Media support** - Upload images and documents with platform-specific handling
- **Configuration management** - JSON-based configuration with validation
- **Rich output** - Beautiful console tables and status indicators
- **Cleanup functionality** - Automatically delete test posts with `--cleanup`

**Usage Examples:**

```bash
# Basic posting
uv run dev/cli.py twitter "Hello world!"
uv run dev/cli.py linkedin "My post" --threaded

# With images (uses test assets)
uv run dev/cli.py bluesky "Check this out" --image=1 --image=2
uv run dev/cli.py linkedin "Professional post" --document

# Reddit-specific options
uv run dev/cli.py reddit "Test post" --subreddit=test --title="My Title"
uv run dev/cli.py reddit "Link post" --url="https://github.com" --title="GitHub"

# Test all platforms
uv run dev/cli.py all "Cross-platform test" --cleanup

# Configuration management  
uv run dev/cli.py config-check
uv run dev/cli.py init-config
```

**Command Reference:**

| Command | Description |
|---------|-------------|
| `post <platform> <message>` | Post to specified platform |
| `config-check` | Validate configuration and show platform status |
| `init-config` | Create config.json from template |

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--threaded` | `-t` | Create thread/series instead of single post |
| `--image=N` | `-i N` | Include test image N (can be used multiple times) |
| `--document` | `-d` | Include test document (LinkedIn only) |
| `--subreddit=NAME` | `-s NAME` | Reddit subreddit (required for Reddit) |
| `--title=TITLE` | | Reddit post title (required for Reddit) |
| `--url=URL` | `-u URL` | URL for link posts (Reddit) |
| `--cleanup` | `-c` | Delete posts after creation |
| `--config=FILE` | | Use specific config file |

### `config.example.json` - Configuration Template

Template configuration file showing the required structure and fields for all platforms.

**Setup Instructions:**
1. Copy `dev/config.example.json` to `config.json` in the project root
2. Fill in your actual API credentials and tokens
3. Update file paths if needed

**Platform Requirements:**
- **Twitter**: `bearer_token`
- **Bluesky**: `handle`, `password` (app password)  
- **LinkedIn**: `access_token`, `person_urn`
- **Reddit**: `access_token`, `user_agent`

### `assets/` - Test Media Files

Contains test media files used by the CLI tool:

| File | Description | Usage |
|------|-------------|-------|
| `test-image-1.jpg` | Primary test image | Single image tests, multi-image tests |
| `test-image-2.jpeg` | Secondary test image | Multi-image tests |
| `test-document.pdf` | Test PDF document | LinkedIn document posts (if created) |

**Image Usage:**
- Use `--image=1` for the first test image
- Use `--image=1 --image=2` for both test images
- Images are automatically validated for platform requirements

## Development Workflow

### 1. Setup
```bash
# Create your config file
uv run dev/cli.py init-config
# Edit config.json with your credentials
```

### 2. Test Individual Platforms
```bash
# Test basic functionality
uv run dev/cli.py twitter "Testing basic post"
uv run dev/cli.py bluesky "Testing with media" --image=1
```

### 3. Test Threading
```bash
# Test threading capabilities
uv run dev/cli.py twitter "Thread test" --threaded
uv run dev/cli.py linkedin "Series test" --threaded
```

### 4. Test All Platforms
```bash
# Comprehensive test with cleanup
uv run dev/cli.py all "Full platform test" --cleanup
```

### 5. Validate Configuration
```bash
# Check your setup
uv run dev/cli.py config-check
```

## Notes

- **Reddit Limitations**: Only supports text and link posts (no images due to simplification)
- **LinkedIn Threading**: Creates numbered series, not true threads
- **Rate Limits**: Be mindful of platform rate limits during testing
- **Cleanup**: Always use `--cleanup` for test posts to avoid cluttering your accounts
- **Credentials**: Never commit your `config.json` with real credentials to version control

## Troubleshooting

**Common Issues:**

1. **Authentication Errors**: Check your tokens in `config.json`
2. **Image Not Found**: Verify the test images exist in `dev/assets/`
3. **Rate Limits**: Wait between requests or use different platforms
4. **Reddit Subreddit**: Ensure you have permission to post in the specified subreddit

**Getting Help:**
```bash
uv run dev/cli.py --help
uv run dev/cli.py post --help
```

This CLI tool represents a production-quality testing interface that showcases the library's capabilities while providing essential development and validation functionality.