# Bluesky Threading Specification

## Overview

Extension to the BlueSkyService class to support native Bluesky threading functionality. Maintains the library's core principles of stateless operations, all-or-nothing posting, and comprehensive error handling.

## Core Threading Methods

### Required Methods

```python
class BlueSkyService(SocialMediaService):
    # Core methods from main spec...
    
    def post_thread(self, messages: List[str], 
                   media: List[List[MediaItem]] = None,
                   rollback_on_failure: bool = True) -> ThreadResult:
        """Post a series of connected posts as a thread"""
        pass
    
    def reply_to_post(self, reply_to_uri: str, reply_to_cid: str,
                     root_uri: str, root_cid: str,
                     text: str, media: List[MediaItem] = None) -> PostResult:
        """Reply to a specific post (building block for threads)"""
        pass
```

### Optional Methods

```python
    def continue_thread(self, thread_uri: str, thread_cid: str, 
                       messages: List[str],
                       media: List[List[MediaItem]] = None,
                       rollback_on_failure: bool = True) -> ThreadResult:
        """Add more posts to an existing thread"""
        pass
    
    def delete_post(self, post_uri: str) -> bool:
        """Delete a specific post (used for rollback)"""
        pass
```

## Data Structures

### ThreadResult Schema

```python
@dataclass
class ThreadResult:
    platform: str = "bluesky"
    thread_id: str              # URI of the first post in thread
    post_results: List[PostResult]  # All individual post results
    thread_url: str             # Human-readable URL to the first post
    
    @property
    def post_count(self) -> int:
        return len(self.post_results)
    
    @property
    def last_post_uri(self) -> str:
        return self.post_results[-1].post_id if self.post_results else None
```

### BlueSkyPostResult Extension

```python
@dataclass
class BlueSkyPostResult(PostResult):
    post_uri: str               # AT Protocol URI 
    post_cid: str               # Content ID
    
    def __post_init__(self):
        # Extract rkey from URI for post_id compatibility
        self.post_id = self.post_uri.split('/')[-1]
        # Convert AT URI to human-readable URL
        self.url = f"https://bsky.app/profile/{self.author_handle}/post/{self.post_id}"
```

### ThreadPostingError

```python
class ThreadPostingError(BlueSkyError):
    """Thread posting failed"""
    def __init__(self, message: str, posted_count: int, rollback_attempted: bool):
        self.posted_count = posted_count
        self.rollback_attempted = rollback_attempted
        super().__init__(message)
```

## Threading Behavior

### All-or-Nothing Guarantee

- **Success**: All posts published successfully, ThreadResult returned
- **Failure with rollback=True**: All posted posts deleted, ThreadPostingError raised
- **Failure with rollback=False**: Partial thread remains, ThreadPostingError raised with posted_count

### Sequential Posting Process

1. **Validate all messages** - check character limits, media constraints
2. **Post first message** - becomes the thread root
3. **Post subsequent messages as replies** - each replies to the previous post with proper root/parent references
4. **On failure**: Delete all posted messages if rollback_on_failure=True

### Reply Reference Structure

Each reply post includes:
```json
{
  "reply": {
    "root": {
      "uri": "at://did:plc:user/app.bsky.feed.post/root_rkey",
      "cid": "root_content_id"
    },
    "parent": {
      "uri": "at://did:plc:user/app.bsky.feed.post/parent_rkey", 
      "cid": "parent_content_id"
    }
  }
}
```

### Media Handling

- `media` parameter is `List[List[MediaItem]]` - one list per post
- Each post's media validated independently
- Media validation follows same rules as single posts

## Usage Examples

### Basic Threading

```python
from hydra_poster import BlueSkyService

messages = [
    "This is post 1/3 about decentralized social media...",
    "Post 2/3: Here's how AT Protocol works...", 
    "Post 3/3: And that's the future! 🦋"
]

bluesky = BlueSkyService(credentials)
try:
    thread = bluesky.post_thread(messages)
    print(f"Thread posted: {thread.thread_url}")
    print(f"Posted {thread.post_count} messages")
except ThreadPostingError as e:
    print(f"Thread failed after {e.posted_count} posts")
    if e.rollback_attempted:
        print("Posted messages have been deleted")
```

### Threading with Media

```python
messages = ["Check out these images!", "And here's another one:"]
media = [
    [MediaItem("photo1.jpg", "image", alt_text="First photo"), 
     MediaItem("photo2.jpg", "image", alt_text="Second photo")],
    [MediaItem("photo3.jpg", "image", alt_text="Third photo")]
]

thread = bluesky.post_thread(messages, media=media)
```

### No Rollback Mode

```python
# Keep partial threads on failure
thread = bluesky.post_thread(messages, rollback_on_failure=False)
```

### Manual Thread Building

```python
# Post individual messages manually
first_post = bluesky.post("Starting a thread...")
reply = bluesky.reply_to_post(
    reply_to_uri=first_post.post_uri,
    reply_to_cid=first_post.post_cid,
    root_uri=first_post.post_uri,
    root_cid=first_post.post_cid,
    text="This is post 2..."
)
final = bluesky.reply_to_post(
    reply_to_uri=reply.post_uri,
    reply_to_cid=reply.post_cid,
    root_uri=first_post.post_uri,
    root_cid=first_post.post_cid,
    text="End of thread!"
)
```

### Continue Existing Thread

```python
# Add more posts to an existing thread
existing_thread_uri = "at://did:plc:user/app.bsky.feed.post/3k43tv4rft22g"
existing_thread_cid = "bafyreig2fjxi3rptqdgylg7e5hmjl6mcke7rn2b6cugzlqq3i4zu6rq52q"
more_messages = ["Additional point 1", "Additional point 2"]

extended = bluesky.continue_thread(existing_thread_uri, existing_thread_cid, more_messages)
```

## Validation Rules

### Thread Validation

- **Message count**: No hard limit (Bluesky is more permissive than Twitter)
- **Character limits**: Each post must meet Bluesky's character requirements (300 characters)
- **Media limits**: Each post's media must pass individual validation
- **Content policy**: Each post validated against Bluesky's community guidelines

### Media Validation per Post

- **Images**: Max 4 per post, up to 1MB each, formats: JPG, PNG, GIF, WEBP
- **Videos**: 1 video max, up to 50MB, formats: MP4, MOV
- **Alt text**: Strongly encouraged for accessibility

## Error Handling

### Validation Errors

```python
class ThreadValidationError(BlueSkyError):
    """Thread validation failed before posting"""
    def __init__(self, errors: List[Dict]):
        self.errors = errors  # Per-post error details
        super().__init__(f"Thread validation failed for {len(errors)} posts")
```

### Example Validation Error

```
ThreadValidationError: Thread validation failed for 2 posts
- Post 2: Text exceeds 300 character limit (315 chars)
- Post 4: Image 'large.jpg' (1.2MB) exceeds 1MB limit
```

### Posting Errors

- **Network failures**: Retry logic for temporary failures
- **Rate limiting**: More lenient than Twitter but still possible
- **Content violations**: Stop immediately, rollback if enabled
- **Auth errors**: Stop immediately, no rollback needed

## Rate Limiting Considerations

### Bluesky Advantages

- **No harsh monthly quotas**: Unlike Twitter's 500 posts/month free tier
- **Reasonable rate limits**: More permissive for threading use cases
- **No rollback quota penalty**: Deleting posts doesn't consume additional quota

### Best Practices

```python
def validate_thread_length(self, messages: List[str]) -> None:
    """Inform about thread length without strict quotas"""
    if len(messages) > 25:
        print(f"Info: Posting {len(messages)} messages in a thread. "
              f"Consider breaking into smaller threads for better engagement.")
```

## Implementation Notes

### API Endpoints Used

- `com.atproto.repo.createRecord` - Create posts and replies
- `com.atproto.repo.deleteRecord` - Delete posts (for rollback)
- Collection type: `app.bsky.feed.post`

### AT Protocol Specifics

- **URIs**: Use AT Protocol URI format (`at://did:plc:user/collection/rkey`)
- **CIDs**: Content-addressed identifiers for immutable references
- **Reply structure**: Must include both `parent` and `root` references
- **Decentralized**: Posts distributed across multiple servers (PDS)

### Rollback Considerations

- Cleaner deletion than Twitter due to decentralized architecture
- Less likely to have persistent cached copies
- Still not truly atomic due to sequential posting nature

### Authentication

- Uses same credential pattern as other services in the library
- Developer provides appropriate Bluesky credentials
- Session-based authentication handled internally

## Testing Strategy

### Unit Tests

- Mock AT Protocol API responses for consistent testing
- Test rollback scenarios with simulated failures
- Validate media handling across multiple posts
- Test URI/CID reference management

### Integration Tests

- Test against Bluesky API with test accounts
- Verify thread creation and proper reply linking
- Test deletion/rollback functionality
- Validate error message accuracy

### Edge Cases

- Very long threads (100+ posts)
- Mixed media types across thread
- Network failures mid-thread
- Invalid URI/CID references
- Authentication failures mid-thread

This spec provides Claude Code with clear implementation guidance while maintaining the library's core design principles and leveraging Bluesky's specific AT Protocol features.