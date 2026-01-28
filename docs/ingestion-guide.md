# Ingestion Guide

This guide is for developers building tools that write data to MetaSPN content repositories.

## Quick Decision Tree

```
What kind of content is this?

Content I CONSUMED (read, watched, listened to)
└─→ Write to sources/
    └─→ Is it a podcast? → sources/podcasts/listening-events.jsonl
    └─→ Is it a blog/article? → sources/blogs/reading-events.jsonl
    └─→ Is it a book? → sources/books/reading-events.jsonl
    └─→ Is it a tweet I engaged with? → sources/twitter/engagement-events.jsonl

Content I CREATED (wrote, published, posted)
└─→ Write to artifacts/
    └─→ Is it my tweet? → artifacts/twitter/tweets.jsonl
    └─→ Is it my podcast episode? → artifacts/podcast/episodes.jsonl
    └─→ Is it my blog post? → artifacts/blog/posts.jsonl
    └─→ Is it my YouTube video? → artifacts/youtube/videos.jsonl
```

## Minimal Example

Here's the simplest valid activity you can write:

```json
{
  "activity_id": "twitter_123456789",
  "timestamp": "2024-01-28T12:00:00Z",
  "platform": "twitter",
  "activity_type": "create",
  "content": "This is my tweet content"
}
```

Write it to `artifacts/twitter/tweets.jsonl`:

```bash
echo '{"activity_id":"twitter_123456789","timestamp":"2024-01-28T12:00:00Z","platform":"twitter","activity_type":"create","content":"This is my tweet content"}' >> artifacts/twitter/tweets.jsonl
```

## Writing Activities

### Python Example

```python
import json
from datetime import datetime
from pathlib import Path

def write_activity(repo_path: str, activity: dict) -> None:
    """Write an activity to the correct location."""

    # Determine file path based on activity type and platform
    if activity["activity_type"] == "create":
        # Created content goes to artifacts
        platform_files = {
            "twitter": "artifacts/twitter/tweets.jsonl",
            "podcast": "artifacts/podcast/episodes.jsonl",
            "blog": "artifacts/blog/posts.jsonl",
            "youtube": "artifacts/youtube/videos.jsonl",
        }
    else:
        # Consumed content goes to sources
        platform_files = {
            "podcast": "sources/podcasts/listening-events.jsonl",
            "blog": "sources/blogs/reading-events.jsonl",
            "book": "sources/books/reading-events.jsonl",
            "twitter": "sources/twitter/engagement-events.jsonl",
        }

    file_path = Path(repo_path) / platform_files[activity["platform"]]
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Append to JSONL file
    with open(file_path, "a") as f:
        f.write(json.dumps(activity) + "\n")


# Example: Write a tweet
write_activity("./my-content", {
    "activity_id": "twitter_123456789",
    "timestamp": datetime.now().isoformat() + "Z",
    "platform": "twitter",
    "activity_type": "create",
    "content": "Hello world!",
    "url": "https://twitter.com/me/status/123456789",
    "raw_data": {
        "tweet_id": "123456789",
        "username": "me"
    }
})
```

### Batch Writing

For better performance when writing many activities:

```python
def write_activities_batch(repo_path: str, activities: list[dict]) -> None:
    """Write multiple activities efficiently."""

    # Group by destination file
    by_file: dict[str, list[dict]] = {}

    for activity in activities:
        file_path = get_file_path(repo_path, activity)  # Use logic above
        if file_path not in by_file:
            by_file[file_path] = []
        by_file[file_path].append(activity)

    # Write each file
    for file_path, file_activities in by_file.items():
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a") as f:
            for activity in file_activities:
                f.write(json.dumps(activity) + "\n")
```

## Generating Activity IDs

Activity IDs must be unique across the entire repository.

### Recommended Formats

| Platform | Format | Example |
|----------|--------|---------|
| Twitter | `twitter_{tweet_id}` | `twitter_1327008879046225921` |
| Podcast (created) | `podcast_ep_{episode_id}` | `podcast_ep_42` |
| Podcast (consumed) | `podcast_listen_{uuid}` | `podcast_listen_a1b2c3d4` |
| Blog (created) | `blog_post_{slug_or_id}` | `blog_post_my-first-post` |
| Blog (consumed) | `blog_read_{hash}` | `blog_read_abc123` |
| YouTube | `youtube_{video_id}` | `youtube_dQw4w9WgXcQ` |
| Book | `book_{isbn}` | `book_9780804139298` |

### ID Generation Code

```python
import uuid
import hashlib

def generate_activity_id(platform: str, unique_data: str) -> str:
    """Generate a unique activity ID."""

    # If we have a platform-specific ID, use it
    if unique_data:
        return f"{platform}_{unique_data}"

    # Otherwise generate a UUID
    return f"{platform}_{uuid.uuid4().hex[:12]}"


def generate_id_from_content(platform: str, content: str, timestamp: str) -> str:
    """Generate ID from content hash (for consumed content without IDs)."""
    hash_input = f"{content}:{timestamp}"
    content_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:12]
    return f"{platform}_{content_hash}"
```

## Timestamp Handling

All timestamps must be ISO 8601 format with timezone.

```python
from datetime import datetime, timezone

# Correct: UTC timestamp
timestamp = datetime.now(timezone.utc).isoformat()
# "2024-01-28T12:00:00+00:00"

# Also correct: Z suffix for UTC
timestamp = datetime.utcnow().isoformat() + "Z"
# "2024-01-28T12:00:00Z"

# Incorrect: No timezone info
timestamp = datetime.now().isoformat()
# "2024-01-28T12:00:00" ← Missing timezone!
```

## Platform-Specific Templates

### Twitter Ingestion Tool

```python
def ingest_tweet(repo_path: str, tweet_data: dict) -> None:
    """Ingest a tweet from Twitter API response."""

    activity = {
        "activity_id": f"twitter_{tweet_data['id']}",
        "timestamp": tweet_data["created_at"],  # Twitter uses ISO format
        "platform": "twitter",
        "activity_type": "create",
        "content": tweet_data["text"],
        "url": f"https://twitter.com/{tweet_data['author']['username']}/status/{tweet_data['id']}",
        "raw_data": {
            "tweet_id": tweet_data["id"],
            "username": tweet_data["author"]["username"],
            "author_id": tweet_data["author_id"],
            "tweet_type": "original",  # or "reply", "retweet", "quote"
            "metrics": {
                "likes": tweet_data.get("public_metrics", {}).get("like_count", 0),
                "retweets": tweet_data.get("public_metrics", {}).get("retweet_count", 0),
                "replies": tweet_data.get("public_metrics", {}).get("reply_count", 0),
            }
        }
    }

    write_activity(repo_path, activity)
```

### Podcast Episode Ingestion

```python
def ingest_podcast_episode(repo_path: str, episode_data: dict) -> None:
    """Ingest a podcast episode from RSS feed."""

    activity = {
        "activity_id": f"podcast_ep_{episode_data['guid']}",
        "timestamp": episode_data["pubDate"],  # Convert to ISO format
        "platform": "podcast",
        "activity_type": "create",
        "title": episode_data["title"],
        "content": episode_data.get("description", ""),
        "url": episode_data.get("link"),
        "duration_seconds": parse_duration(episode_data.get("duration")),
        "raw_data": {
            "episode_id": episode_data["guid"],
            "show_title": episode_data["show_title"],
            "audio_url": episode_data.get("enclosure", {}).get("url"),
            "episode_number": episode_data.get("episode"),
            "season": episode_data.get("season"),
        }
    }

    write_activity(repo_path, activity)
```

### Listening Event Ingestion

```python
def ingest_listening_event(repo_path: str, listen_data: dict) -> None:
    """Ingest a podcast listening event from a player."""

    activity = {
        "activity_id": f"podcast_listen_{listen_data['session_id']}",
        "timestamp": listen_data["end_time"],
        "platform": "podcast",
        "activity_type": "consume",
        "title": listen_data["episode_title"],
        "url": listen_data.get("episode_url"),
        "duration_seconds": listen_data["listened_duration"],
        "raw_data": {
            "episode_id": listen_data["episode_id"],
            "show_title": listen_data["show_title"],
            "listening": {
                "start_time": listen_data["start_time"],
                "end_time": listen_data["end_time"],
                "duration_seconds": listen_data["listened_duration"],
                "completion_percentage": listen_data.get("completion", 0),
                "playback_speed": listen_data.get("speed", 1.0),
            }
        }
    }

    write_activity(repo_path, activity)
```

## Validation

Before writing, validate your activity:

```python
def validate_activity(activity: dict) -> list[str]:
    """Validate an activity and return list of errors."""
    errors = []

    # Required fields
    required = ["activity_id", "timestamp", "platform", "activity_type"]
    for field in required:
        if field not in activity:
            errors.append(f"Missing required field: {field}")

    # Valid activity types
    if activity.get("activity_type") not in ["create", "consume"]:
        errors.append(f"Invalid activity_type: {activity.get('activity_type')}")

    # Valid platforms
    valid_platforms = ["twitter", "podcast", "blog", "youtube", "book"]
    if activity.get("platform") not in valid_platforms:
        errors.append(f"Invalid platform: {activity.get('platform')}")

    # Timestamp format
    try:
        datetime.fromisoformat(activity.get("timestamp", "").replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"Invalid timestamp format: {activity.get('timestamp')}")

    # Activity ID format
    activity_id = activity.get("activity_id", "")
    if not activity_id or "_" not in activity_id:
        errors.append(f"Invalid activity_id format: {activity_id}")

    return errors
```

## After Writing

After ingesting new activities, update the indexes:

```bash
# Rebuild manifest to include new activities
metaspn index ./my-content

# Compute enhancements for new activities
metaspn enhance ./my-content
```

Or programmatically:

```python
from metaspn.repo import build_manifest
from metaspn.core.profile import compute_and_store_enhancements

# Update manifest
build_manifest("./my-content", force=True)

# Compute enhancements for new activities only
compute_and_store_enhancements("./my-content", force_recompute=False)
```

## Common Mistakes

### 1. Wrong Directory

```
❌ artifacts/twitter/engagement.jsonl   # Engagement is consumed, not created
✅ sources/twitter/engagement-events.jsonl

❌ sources/podcast/episodes.jsonl       # Your episodes are created, not consumed
✅ artifacts/podcast/episodes.jsonl
```

### 2. Missing Timezone

```
❌ "timestamp": "2024-01-28T12:00:00"
✅ "timestamp": "2024-01-28T12:00:00Z"
```

### 3. Duplicate IDs

Activity IDs must be unique. Check before writing:

```python
# Load manifest to check existing IDs
from metaspn.repo import load_manifest

manifest = load_manifest("./my-content")
existing_ids = set(manifest.activities.keys())

# Filter out duplicates
new_activities = [a for a in activities if a["activity_id"] not in existing_ids]
```

### 4. Invalid JSON

JSONL requires valid JSON on each line:

```
❌ {"activity_id": "x", "content": "has "quotes" inside"}
✅ {"activity_id": "x", "content": "has \"quotes\" inside"}
```

### 5. Wrong Platform Name

```
❌ "platform": "Twitter"   # Wrong case
✅ "platform": "twitter"   # Always lowercase

❌ "platform": "podcasts"  # Wrong for created content
✅ "platform": "podcast"   # Singular for artifacts
```

## Testing Your Ingestion Tool

```bash
# 1. Initialize test repository
metaspn init ./test-repo --user-id test --name "Test User"

# 2. Run your ingestion tool
python my_ingestor.py --repo ./test-repo

# 3. Validate repository
metaspn validate ./test-repo

# 4. Check activities were loaded
metaspn query ./test-repo --count

# 5. Verify enhancement computation works
metaspn enhance ./test-repo

# 6. Generate profile to verify everything
metaspn profile ./test-repo
```
