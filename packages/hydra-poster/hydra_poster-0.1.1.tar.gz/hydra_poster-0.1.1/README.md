# Hydra Poster

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)
[![Tests](https://img.shields.io/badge/tests-pytest-orange.svg)](https://pytest.org/)

> **🤖 AI-Generated Notice**: This project was entirely "vibe-coded" by [Anthropic's Claude Sonnet 4](https://claude.ai), demonstrating AI-powered software development. While functional and production-ready, the codebase represents a collaboration between human creativity and AI implementation.

A Python library for reliable social media posting across multiple platforms with comprehensive threading support. Designed for simplicity and use by AI coding agents, with stateless operations, automatic rollback on failures, and comprehensive pre-validation.

## Table of Contents

- [Features](#features)
- [Platform Support](#platform-support)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Simple Examples](#simple-examples)
- [Advanced Examples](#advanced-examples)
- [For AI Coding Agents](#for-ai-coding-agents)
- [Platform-Specific Details](#platform-specific-details)
- [API Reference](#api-reference)
- [Development & Testing](#development--testing)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)

## Features

- **🔄 All-or-nothing posting** - Automatic rollback on failures across all platforms
- **✅ Pre-validation** - Fail fast with comprehensive error reporting before posting
- **🧵 Threading support** - Native threading on Twitter and Bluesky, numbered series on LinkedIn
- **🎯 Stateless operations** - No persistent state between calls, perfect for AI agents
- **📱 Media support** - Images, videos, documents with platform-specific validation
- **🛡️ Robust error handling** - Detailed exception hierarchy with actionable guidance
- **🔌 Unified interface** - Same `post()` and `post_thread()` methods across platforms
- **🤖 AI-agent optimized** - Simple, predictable API designed for automated usage

## Platform Support

| Platform | Single Posts | Threading | Media Support | Rate Limits |
|----------|--------------|-----------|---------------|-------------|
| **Twitter/X** | ✅ | ✅ Reply chains | Images, videos | 500 posts/month (free) |
| **Bluesky** | ✅ | ✅ AT Protocol | Images, videos | More permissive |
| **LinkedIn** | ✅ | ⚠️ Numbered series* | Images, documents | 2s delays |
| **Reddit** | ✅ | ❌ No threading | None (deprecated) | Standard API limits |

_*LinkedIn "threading" creates separate, unconnected posts with numbers - not true threads._

## Installation

```bash
# From PyPI (when published)
pip install hydra-poster

# Development installation
git clone https://github.com/heysamtexas/hydra-poster
cd hydra-poster
make install
```

## Quick Start

```python
from hydra_poster import TwitterService, BlueSkyService, LinkedInService

# Basic posting
twitter = TwitterService("your_bearer_token")
result = twitter.post("Hello Twitter!")
print(f"Posted: {result.url}")

# Threading (platform-specific behavior)
bluesky = BlueSkyService("handle.bsky.social", "password")
messages = ["First post", "Second post", "Third post"]
thread_result = bluesky.post_thread(messages)
print(f"Thread: {thread_result.thread_url}")

# LinkedIn post series (NOT threading)
linkedin = LinkedInService("access_token", "person_urn")
series_result = linkedin.post_series(messages)  # Creates 3 separate posts
```

## Simple Examples

### Text Posts

```python
# Twitter
twitter = TwitterService("bearer_token")
result = twitter.post("Hello world! 🌍")

# Bluesky  
bluesky = BlueSkyService("username.bsky.social", "password")
result = bluesky.post("Testing from Python 🐍")

# LinkedIn
linkedin = LinkedInService("access_token", "urn:li:person:12345")
result = linkedin.post("Professional update 💼")
```

### Posts with Media

```python
from hydra_poster import MediaItem

# Single image
media = [MediaItem("/path/to/image.jpg", "image", alt_text="A beautiful sunset")]
result = twitter.post("Check this out!", media=media)

# Multiple images
media = [
    MediaItem("/path/to/img1.jpg", "image", alt_text="First image"),
    MediaItem("/path/to/img2.jpg", "image", alt_text="Second image")
]
result = bluesky.post("Photo gallery!", media=media)

# LinkedIn document
doc = [MediaItem("/path/to/doc.pdf", "document", alt_text="Report")]
result = linkedin.post("Quarterly report attached", media=doc)
```

### Reddit Posts

```python
from hydra_poster import RedditService, PostConfig

reddit = RedditService("access_token", "MyApp/1.0")

# Text post
config = PostConfig(metadata={
    "subreddit": "Python",
    "title": "Amazing Python Library!"
})
result = reddit.post("Check out this library...", config=config)

# Link post
config = PostConfig(metadata={
    "subreddit": "programming", 
    "title": "GitHub Project",
    "url": "https://github.com/username/repo"
})
result = reddit.post("Built something cool!", config=config)
```

## Advanced Examples

### Threading with Error Handling

```python
from hydra_poster.exceptions import ThreadPostingError

messages = [
    "🧵 Thread about AI development (1/3)",
    "The technology is advancing rapidly... (2/3)", 
    "What are your thoughts? (3/3)"
]

try:
    # Twitter creates reply chain
    result = twitter.post_thread(messages, rollback_on_failure=True)
    print(f"Thread created: {result.thread_url}")
    print(f"Individual post URLs: {[r.url for r in result.post_results]}")
    
except ThreadPostingError as e:
    print(f"Failed after posting {e.posted_count} messages")
    print(f"Rollback attempted: {e.rollback_attempted}")
    print(f"Error: {e}")
```

### Media Validation and Error Recovery

```python
from hydra_poster.exceptions import MediaValidationError

try:
    # This will validate before posting
    large_media = [MediaItem("/path/to/huge_file.mp4", "video")]
    result = twitter.post("My video", media=large_media)
    
except MediaValidationError as e:
    print(f"Media validation failed: {e}")
    print("Fix suggestions:")
    for suggestion in e.suggestions:
        print(f"  - {suggestion}")
        
    # Retry with smaller file
    small_media = [MediaItem("/path/to/small_vid.mp4", "video")]
    result = twitter.post("My video (compressed)", media=small_media)
```

### Cross-Platform Posting

```python
services = {
    'twitter': TwitterService("bearer_token"),
    'bluesky': BlueSkyService("handle", "password"),
    'linkedin': LinkedInService("token", "urn")
}

message = "Exciting announcement! 🚀"
results = {}
failed_platforms = []

for platform, service in services.items():
    try:
        result = service.post(message)
        results[platform] = result.url
        print(f"✅ {platform}: {result.url}")
    except Exception as e:
        failed_platforms.append(platform)
        print(f"❌ {platform}: {e}")

# Handle partial failures
if failed_platforms:
    print(f"Failed platforms: {failed_platforms}")
    # Implement retry logic or notification
```

## For AI Coding Agents

### Installation Verification
```python
# Always verify installation first
try:
    from hydra_poster import TwitterService
    print("✅ Library installed correctly")
except ImportError as e:
    print(f"❌ Installation failed: {e}")
    exit(1)
```

### Pre-Post Checklist

1. **✅ Credentials Check**
   ```python
   import os
   
   # Verify environment variables exist
   bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
   if not bearer_token:
       raise ValueError("TWITTER_BEARER_TOKEN not found")
   ```

2. **✅ Content Validation**
   ```python
   message = "Your content here"
   
   # Twitter: 280 characters max
   if len(message) > 280:
       raise ValueError(f"Twitter message too long: {len(message)} chars")
   
   # LinkedIn: 3000 characters max  
   if len(message) > 3000:
       raise ValueError(f"LinkedIn message too long: {len(message)} chars")
   ```

3. **✅ Media Validation**
   ```python
   from pathlib import Path
   
   if media_path:
       path = Path(media_path)
       if not path.exists():
           raise FileNotFoundError(f"Media file not found: {path}")
       
       # Check file size (5MB limit for most platforms)
       if path.stat().st_size > 5 * 1024 * 1024:
           raise ValueError("Media file too large (>5MB)")
   ```

4. **✅ Always Use Error Handling**
   ```python
   from hydra_poster.exceptions import SocialMediaError
   
   try:
       result = service.post(message)
       if not result.success:
           print(f"Post failed: {result.error}")
   except SocialMediaError as e:
       print(f"Platform error: {e}")
       # Handle specific error types
   ```

### DO NOT ❌

- **Create service instances in loops** - Reuse instances
- **Post without error handling** - Always wrap in try/except
- **Assume credential format** - Always validate first
- **Retry 429 errors immediately** - Implement exponential backoff
- **Mix up LinkedIn threading** - Use `post_series()` instead

### Recovery Procedures

| Error Type | Solution |
|------------|----------|
| `AuthenticationError` | Check API tokens/credentials |
| `RateLimitError` | Wait and retry with exponential backoff |
| `MediaValidationError` | Check file size/format/existence |
| `ThreadPostingError` | Check if partial posts need cleanup |
| `NetworkError` | Implement retry with timeout |

## Platform-Specific Details

### Twitter/X - Native Reply Chains
- **Connection**: Each post replies to the previous post
- **UI**: Native thread interface with expand/collapse
- **Rollback**: Deletes tweets in reverse order
- **Limits**: 500 posts/month (free tier), 280 chars/post
- **Media**: Images (5MB), videos (512MB), up to 4 per post

### Bluesky - AT Protocol Threading  
- **Connection**: Posts linked via URI and CID references
- **UI**: Native thread interface with proper root/parent structure
- **Rollback**: AT Protocol delete operations
- **Limits**: More permissive than Twitter
- **Media**: Images and videos, platform-specific limits

### LinkedIn - Numbered Post Series ⚠️
- **Connection**: NONE - Posts are completely independent
- **UI**: No thread interface - posts scattered in feed
- **Behavior**: Like posting manually with added numbers
- **Method**: Use `post_series()` not `post_thread()`
- **Limits**: 3000 chars/post, 2s delays between posts
- **Media**: Images, documents (PDFs, Word docs)

### Reddit - Text and Link Posts
- **Threading**: Not supported
- **Required**: Subreddit and title for all posts
- **Media**: No longer supported (deprecated)
- **Types**: Text posts or link posts (with URL)

## API Reference

### Core Classes

#### `SocialMediaService` (Abstract Base)
```python
def post(self, content: str, media: Optional[List[MediaItem]] = None, 
         config: Optional[PostConfig] = None) -> PostResult:
    """Post content to the platform."""
    
def post_thread(self, messages: List[str], media: Optional[List[MediaItem]] = None,
                rollback_on_failure: bool = True) -> ThreadResult:
    """Post a thread/series of messages."""
    
def delete_post(self, post_id: str) -> bool:
    """Delete a post by ID."""
```

#### `MediaItem`
```python
MediaItem(
    content: str,           # File path, URL, or base64 data
    media_type: str,        # "image", "video", "document"  
    alt_text: str = "",     # Accessibility text
    title: str = ""         # Optional title
)
```

#### `PostResult`
```python
class PostResult:
    success: bool           # Whether post succeeded
    post_id: str           # Platform-specific post ID
    url: str               # Direct URL to post
    error: Optional[str]    # Error message if failed
    metadata: dict         # Platform-specific data
```

#### `ThreadResult`  
```python
class ThreadResult:
    success: bool                    # Whether thread succeeded
    post_results: List[PostResult]   # Individual post results
    thread_url: str                  # URL to thread (if available)
    posted_count: int                # Number successfully posted
```

### Platform Services

```python
# Twitter
TwitterService(bearer_token: str)

# Bluesky  
BlueSkyService(handle: str, password: str)

# LinkedIn
LinkedInService(access_token: str, person_urn: str)

# Reddit
RedditService(access_token: str, user_agent: str)
```

## Development & Testing

### Development Setup
```bash
# Clone and setup
git clone https://github.com/heysamtexas/hydra-poster
cd hydra-poster
make install        # Install all dependencies
make test           # Run fast tests
make test-all       # Run all tests including slow ones
make ci             # Run all quality checks
```

### CLI Testing Tool

The repository includes a comprehensive CLI tool in `dev/cli.py` for testing all functionality:

```bash
# Setup config
uv run dev/cli.py init-config
uv run dev/cli.py config-check

# Test single posts
uv run dev/cli.py post twitter "Hello world!"
uv run dev/cli.py post bluesky "Testing" --image=1
uv run dev/cli.py post linkedin "Professional update" --document

# Test threading
uv run dev/cli.py post twitter "Thread test" --threaded
uv run dev/cli.py post linkedin "Series test" --threaded

# Test Reddit
uv run dev/cli.py post reddit "My post" --subreddit=test --title="Title"

# Test all platforms
uv run dev/cli.py post all "Cross-platform test" --cleanup

# See all examples  
uv run dev/cli.py examples
```

### Commands Available

```bash
make install          # Install dependencies
make test            # Run fast tests
make test-all        # Run all tests (including slow)
make test-cov        # Run tests with coverage  
make lint            # Check code style
make format          # Format code
make type-check      # Run mypy type checking
make ci              # Run all CI checks
make build           # Build package
make clean           # Clean cache files
```

## Error Handling

### Exception Hierarchy

```python
from hydra_poster.exceptions import *

SocialMediaError                    # Base exception
├── AuthenticationError            # Invalid credentials
├── RateLimitError                # API rate limits hit
├── MediaValidationError          # Invalid media files
├── NetworkError                  # Connection issues
├── ThreadPostingError           # Thread posting failures
├── PlatformSpecificError        # Platform-specific issues
│   ├── TwitterError
│   ├── BlueSkyError  
│   ├── LinkedInError
│   └── RedditError
```

### Common Error Patterns

```python
# Comprehensive error handling
try:
    result = service.post(content, media=media)
    
except AuthenticationError:
    print("Check your API credentials")
    
except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}")
    
except MediaValidationError as e:
    print(f"Media issue: {e}")
    print("Suggestions:", e.suggestions)
    
except NetworkError:
    print("Network issue - retry later")
    
except SocialMediaError as e:
    print(f"Platform error: {e}")
```

## Contributing

We welcome contributions! This AI-generated project benefits from human review and enhancement.

### Development Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following existing code patterns
4. Add tests for new functionality  
5. Run the full test suite (`make ci`)
6. Commit with descriptive messages
7. Push to your fork and create a Pull Request

### Code Standards
- **Type hints**: All functions must have type annotations
- **Testing**: Maintain >90% code coverage
- **Linting**: Code must pass `ruff` checks
- **Documentation**: Update docstrings and README for new features

### Testing
- Unit tests in `tests/` directory
- Mark slow tests with `@pytest.mark.slow`
- Use the CLI tool in `dev/` for manual testing
- Test against real APIs carefully (use test accounts)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

- **Primary Development**: [Anthropic's Claude Sonnet 4](https://claude.ai) - AI-powered software development
- **Human Collaboration**: Architecture design and requirements specification
- **Inspiration**: The need for reliable, AI-agent-friendly social media automation

---

⚡ **Built with AI** • 🐍 **Python 3.12+** • 🧵 **Threading Support** • 🛡️ **Error Recovery** • 🤖 **AI-Agent Optimized**