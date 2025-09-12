# Social Media Posting Library Specification

## Overview

A Python library focused on reliable social media posting with rich media support. The library handles complex API orchestration, comprehensive error handling, and provides consistent interfaces across platforms.

## Core Design Principles

- **Stateless operations** - no persistent state between calls
- **All-or-nothing posting** - automatic rollback on failures  
- **Pre-validation** - fail fast with comprehensive error reporting
- **Platform authenticity** - don't abstract away platform-specific credential handling
- **Simplicity first** - easy to use, especially for AI coding agents

## Architecture

### Abstract Base Class

```python
from abc import ABC, abstractmethod

class SocialMediaService(ABC):
    @abstractmethod
    def post(self, text: str, media: List[MediaItem] = None) -> PostResult:
        """Main posting method - all-in-one operation"""
        pass
    
    @abstractmethod
    def validate_media(self, media: List[MediaItem]) -> None:
        """Pre-validate media items, raise exceptions on issues"""
        pass
```

**Rationale**: Minimal ABC to reduce cognitive load. Only enforces truly universal methods. Platform-specific methods (like `upload_media`, `delete_media`) exist but aren't enforced.

### MediaItem Abstraction

```python
@dataclass
class MediaItem:
    content: Union[str, bytes, os.PathLike]  # URL, file path, or raw bytes
    media_type: str                          # "image", "video", "document"
    alt_text: Optional[str] = None
    filename: Optional[str] = None           # Required when content is bytes
    
    def is_url(self) -> bool:
        return isinstance(self.content, str) and self.content.startswith(('http://', 'https://'))
    
    def is_file_path(self) -> bool:
        return isinstance(self.content, (str, os.PathLike)) and not self.is_url()
    
    def is_bytes(self) -> bool:
        return isinstance(self.content, bytes)
```

**Input Validation Rules:**
- `media_type` is required (no auto-detection to avoid ambiguity)
- `filename` is required when `content` is bytes
- URLs are downloaded during `validate_media()` phase for early failure detection
- After validation, all MediaItems have their `content` normalized to bytes

### PostResult Schema

```python
@dataclass
class PostResult:
    platform: str               # "twitter", "linkedin", etc.
    post_id: str                # Platform-specific post ID
    url: str                    # Human-readable URL to the post
    media_ids: List[str] = None # Uploaded media IDs (for debugging)
    metadata: Dict = None       # Platform-specific extra data
```

## Platform Implementations

### Required Service Objects
- `TwitterService`
- `LinkedInService` 
- `RedditService`
- `GithubService` (for issues)
- `BlueSkyService`
- `GhostService`

### Service Object Pattern

```python
# Stateful service objects with dependency injection
twitter = TwitterService(credentials, settings=None)
result = twitter.post("Hello world", media=[media_item])

# Optional settings override
custom_settings = {"max_image_count": 2}
twitter = TwitterService(credentials, settings=custom_settings)
```

### Platform-Specific Methods

While not enforced by ABC, platforms may implement additional methods:

```python
class TwitterService(SocialMediaService):
    def post(self, text: str, media: List[MediaItem] = None) -> PostResult: ...
    def validate_media(self, media: List[MediaItem]) -> None: ...
    
    # Platform-specific methods
    def upload_media(self, media: List[MediaItem]) -> List[str]: ...
    def create_tweet(self, text: str, media_ids: List[str] = None) -> PostResult: ...
    def delete_media(self, media_ids: List[str]) -> None: ...
```

## Media Handling Pipeline

### Validation Process

1. **Format validation** - check MediaItem structure
2. **Content accessibility** - download URLs, verify file paths exist
3. **Platform limits** - check file sizes, counts, formats against platform rules
4. **Content normalization** - convert all inputs to bytes

### Platform Media Limits

#### Twitter
- **Images**: Max 4, up to 5MB each, formats: JPG, PNG, GIF, WEBP
- **Videos**: 1 video max, up to 512MB, formats: MP4, MOV
- **Character limits**: Reduced when media attached

#### LinkedIn  
- **Images**: Max 9, up to 100MB each, formats: JPG, PNG, GIF
- **Videos**: 1 video max, up to 5GB, formats: MP4, MOV, WMV, AVI
- **Documents**: PDFs up to 100MB

#### Reddit
- **Images**: Max varies by subreddit, typically up to 20MB
- **Videos**: Max varies by subreddit, typically up to 1GB
- **Platform-specific**: Some subreddits only allow text posts

#### GitHub (Issues)
- **File attachments**: Up to 25MB per file, various formats
- **Images**: Embedded in issue body via upload

#### Bluesky
- **Images**: Max 4, up to 1MB each, formats: JPG, PNG, GIF, WEBP
- **Alt text**: Supported and encouraged

#### Ghost
- **Images**: Embedded in HTML content, no specific limits
- **Rich content**: Full HTML support

### Two-Phase Upload Process

For platforms requiring separate media upload:

1. **Upload Phase**: Upload all media files, collect media IDs
2. **Post Phase**: Create post referencing uploaded media
3. **Rollback**: If post creation fails, automatically delete uploaded media

**All-or-nothing guarantee**: Either entire operation succeeds or nothing is posted/uploaded.

## Error Handling

### Exception Hierarchy

```python
class SocialMediaError(Exception):
    """Base exception for all social media operations"""
    pass

class MediaValidationError(SocialMediaError):
    """Media validation failed"""
    def __init__(self, errors: List[Dict]):
        self.errors = errors  # Detailed error list
        super().__init__(f"Media validation failed for {len(errors)} items")

class MediaTooLargeError(MediaValidationError):
    """Media file exceeds size limits"""
    pass

class UnsupportedMediaTypeError(MediaValidationError):  
    """Media format not supported by platform"""
    pass

class MediaUploadError(SocialMediaError):
    """Failed to upload media to platform"""
    pass

class PostCreationError(SocialMediaError):
    """Failed to create post after media upload"""
    pass

# Platform-specific exceptions
class TwitterError(SocialMediaError):
    pass

class LinkedInError(SocialMediaError):
    pass

class RedditError(SocialMediaError):
    pass

class GithubError(SocialMediaError):
    pass

class BlueSkyError(SocialMediaError):
    pass

class GhostError(SocialMediaError):
    pass
```

### Error Message Enhancement

- **Comprehensive validation errors**: Report ALL validation issues at once
- **Suggested fixes**: Include actionable guidance in error messages
- **Platform context**: Preserve original platform error messages while adding helpful context
- **Media-specific errors**: Clear identification of which media items failed and why

Example error message:
```
MediaValidationError: Media validation failed for 2 items
- File 'sunset.jpg' (8.2MB) exceeds Twitter's 5MB image limit. Consider compressing the image.
- File 'video.avi' format not supported by Twitter. Convert to MP4, MOV, or MP4.
```

## Settings and Configuration

### Settings Override Pattern

```python
# Default platform limits
twitter = TwitterService(credentials)

# Override specific limits  
custom_settings = {
    "max_image_size_mb": 3,    # Stricter than platform default
    "max_image_count": 2       # Fewer images allowed
}
twitter = TwitterService(credentials, settings=custom_settings)
```

### Settings Schema (per platform)

```python
@dataclass
class TwitterSettings:
    max_image_count: int = 4
    max_image_size_mb: int = 5
    max_video_count: int = 1
    max_video_size_mb: int = 512
    supported_image_formats: List[str] = field(default_factory=lambda: ["jpg", "png", "gif", "webp"])
    supported_video_formats: List[str] = field(default_factory=lambda: ["mp4", "mov"])
```

## Usage Examples

### Basic Text Posting

```python
from hydra_poster import TwitterService

twitter = TwitterService(access_token="your_token")
result = twitter.post("Hello world!")
print(f"Posted: {result.url}")
```

### Media Posting

```python
from hydra_poster import TwitterService, MediaItem

# Various media input methods
media = [
    MediaItem(content="./sunset.jpg", media_type="image", alt_text="Beautiful sunset"),
    MediaItem(content="https://example.com/video.mp4", media_type="video"),
    MediaItem(content=raw_bytes, media_type="image", filename="generated.png")
]

twitter = TwitterService(access_token)
try:
    result = twitter.post("Check out these amazing photos!", media=media)
    print(f"Posted with media: {result.url}")
except MediaValidationError as e:
    for error in e.errors:
        print(f"Fix required: {error}")
```

### Multi-Platform Posting

```python
from hydra_poster import TwitterService, LinkedInService

platforms = [
    TwitterService(twitter_token),
    LinkedInService(linkedin_urn, linkedin_token)
]

for platform in platforms:
    try:
        result = platform.post("Hello from all platforms!", media)
        print(f"{platform.__class__.__name__}: {result.url}")
    except SocialMediaError as e:
        print(f"{platform.__class__.__name__} failed: {e}")
```

### Step-by-Step Posting (Advanced)

```python
# For platforms that support granular control
twitter = TwitterService(access_token)

# Upload media first
media_ids = twitter.upload_media(media_items)
print(f"Uploaded media: {media_ids}")

# Create post with uploaded media
result = twitter.create_tweet("My post text", media_ids=media_ids)
print(f"Created post: {result.url}")
```

## Implementation Notes

### Synchronous Only
- Start with sync-only implementation for simplicity
- Async support can be added later as separate service classes if needed
- Compatible with Django without requiring channels

### No Caching (Phase 1)
- Keep initial implementation simple without URL caching
- Media files are downloaded fresh each time
- Caching can be added in future versions if performance becomes an issue

### Platform Rate Limiting
- Library does not implement rate limiting
- Platforms will return appropriate HTTP status codes
- Developers responsible for handling rate limit responses

### Credential Management
- Library accepts credentials but doesn't validate formats
- First API call will reveal credential issues with authentic platform error messages
- No attempt to second-guess platform authentication flows

## Testing Strategy

### Unit Testing
- Mock platform APIs for consistent testing
- Test error conditions and rollback scenarios
- Validate media processing pipeline

### Integration Testing  
- Test against actual platform APIs (with test accounts)
- Verify error message accuracy and helpfulness
- End-to-end posting workflows

### Developer Experience Testing
- Test with AI coding agents (Claude Code)
- Validate error messages provide actionable guidance
- Ensure consistent behavior across platforms