# CLI Reference

MetaSPN provides a command-line interface for managing content repositories.

## Installation

```bash
pip install metaspn
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `init` | Initialize a new repository |
| `profile` | Compute user profile |
| `enhance` | Manage enhancement layers |
| `index` | Build activity indexes |
| `query` | Query activities with filters |
| `history` | View enhancement history |
| `check` | Check if repository is ready for scoring |
| `stats` | Show repository statistics |
| `validate` | Validate repository structure |
| `cards` | Generate trading cards |
| `add` | Add an activity |
| `export` | Export profile data |
| `serve` | Start the API server |

---

## `metaspn init`

Initialize a new MetaSPN repository with the data lake structure.

```bash
metaspn init PATH --user-id USER_ID --name NAME [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PATH` | Directory path for the repository |

### Options

| Option | Required | Description |
|--------|----------|-------------|
| `--user-id` | Yes | Unique user identifier |
| `--name` | Yes | Display name |
| `--handle` | No | User handle (e.g., @username) |
| `--avatar-url` | No | URL to avatar image |

### Example

```bash
metaspn init ./my-content \
  --user-id "leo_guinan" \
  --name "Leo Guinan" \
  --handle "@leo_guinan"
```

---

## `metaspn profile`

Compute user profile from repository activities.

```bash
metaspn profile PATH [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--force` | Force recompute (ignore cache) |
| `--output`, `-o` | Output file for JSON |
| `--json` | Output as JSON |
| `--no-enhance` | Skip enhancement layer |
| `--recompute-enhance` | Recompute all enhancements |

### Examples

```bash
# Basic profile computation
metaspn profile ./my-content

# Force recompute and output as JSON
metaspn profile ./my-content --force --json

# Save to file
metaspn profile ./my-content -o profile.json

# Skip enhancement layer (use embedded scores)
metaspn profile ./my-content --no-enhance
```

---

## `metaspn enhance`

Manage enhancement layers for computed metrics.

```bash
metaspn enhance PATH [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--force` | Force recompute all enhancements |
| `--clear` | Clear all enhancements |
| `--status` | Show enhancement status only |
| `--archive-previous` | Archive current before recomputing |

### Examples

```bash
# Compute missing enhancements
metaspn enhance ./my-content

# Show status
metaspn enhance ./my-content --status

# Force recompute with history preservation
metaspn enhance ./my-content --force --archive-previous

# Clear all enhancements
metaspn enhance ./my-content --clear
```

### Status Output

```
Enhancement Status for ./my-content
==================================================
Total Activities: 42390

Quality Scores:
  File exists: True
  Records: 42390
  Coverage: 42390/42390 activities

Game Signatures:
  File exists: True
  Records: 42390
  Coverage: 42390/42390 activities

Embeddings:
  File exists: False
  Records: 0
  Coverage: 0/42390 activities

All enhancements up to date.
```

---

## `metaspn index`

Build or rebuild the activity index/manifest for fast querying.

```bash
metaspn index PATH [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--rebuild` | Force rebuild of all indexes |

### Examples

```bash
# Build indexes (skips if exists)
metaspn index ./my-content

# Force rebuild
metaspn index ./my-content --rebuild
```

### Output

```
Building manifest...

Manifest built successfully
==================================================
Total activities: 42390
Last updated: 2024-01-28T12:00:00Z

By platform:
  twitter: 38880
  podcast: 3000
  blog: 510

By type:
  create: 42390
  consume: 0

Year range: 2020 - 2024

Indexes saved to artifacts/indexes/
```

---

## `metaspn query`

Query activities with filters.

```bash
metaspn query PATH [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--platform`, `-p` | Filter by platform |
| `--type` | Filter by activity type (create/consume) |
| `--since` | Filter by start date (YYYY-MM-DD) |
| `--until` | Filter by end date (YYYY-MM-DD) |
| `--limit`, `-n` | Maximum results (default: 10) |
| `--json` | Output as JSON |
| `--count` | Show count only |

### Examples

```bash
# Query Twitter activities
metaspn query ./my-content --platform twitter --limit 10

# Query by date range
metaspn query ./my-content --since 2024-01-01 --until 2024-01-31

# Count created content
metaspn query ./my-content --type create --count

# Output as JSON
metaspn query ./my-content --platform podcast --json
```

### Output

```
Found 10 activities
Filters: platform=twitter
==================================================
[2024-01-28 12:00] twitter/create: Just shipped a new feature!...
  URL: https://twitter.com/leo_guinan/status/123
[2024-01-28 11:30] twitter/create: Thinking about...
  URL: https://twitter.com/leo_guinan/status/122
...

(Showing first 10 results. Use --limit to see more.)
```

---

## `metaspn history`

View enhancement history for activities.

```bash
metaspn history PATH [ACTIVITY_ID] [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--type` | Enhancement type (quality_scores/game_signatures/embeddings) |
| `--list` | List all history files |
| `--json` | Output as JSON |

### Examples

```bash
# List history files
metaspn history ./my-content --list

# View history for specific activity
metaspn history ./my-content twitter_1327008879046225921

# View game signature history
metaspn history ./my-content twitter_1327008879046225921 --type game_signatures
```

### List Output

```
Enhancement History: quality_scores
==================================================
  2024-01-28_v1.1_algorithm_update.jsonl
  2024-01-15_v1.0_manual_archive.jsonl

Current algorithm version: 1.1
```

### Timeline Output

```
Enhancement Timeline: twitter_1327008879046225921
Type: quality_scores
==================================================

[2024-01-28T12:00:00Z] v1.1 (from latest)
  Quality Score: 0.87
  Content Score: 0.90
  Consistency Score: 0.82

[2024-01-15T10:00:00Z] v1.0 (from 2024-01-15_v1.0_manual_archive.jsonl)
  Quality Score: 0.85
  Content Score: 0.88
  Consistency Score: 0.80
```

---

## `metaspn stats`

Show repository statistics.

```bash
metaspn stats PATH
```

### Example

```bash
metaspn stats ./my-content
```

### Output

```
Leo Guinan
==================================================
Handle: @leo_guinan
Repository: /Users/leo/my-content
Created: 2024-01-01T00:00:00Z
Activity Files: 5

--- Level & Rarity ---
Level: 42
XP: 12500 (next level: 2500 XP)
Rarity: epic

--- Lifecycle ---
Phase: established
Progress: 65%
Next Phase: scaling

--- Platforms ---
  [C] twitter: 38880 activities
  [C] podcast: 3000 activities
  [C] blog: 510 activities

--- Creator Metrics ---
Quality: 0.85
Game Alignment: 0.78
Impact Factor: 0.72
Consistency: 0.91
Total Outputs: 42390

Top Games: G3:0.45, G4:0.25, G1:0.15

--- Achievements (12) ---
  🎯 First Tweet
  📱 Social Butterfly
  🎙️ Podcaster
  ...
```

---

## `metaspn check`

Check if repository is ready for scoring.

```bash
metaspn check PATH [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--fix` | Attempt to fix minor issues |
| `--json` | Output as JSON |
| `-v`, `--verbose` | Show detailed error information |

### What It Checks

| Check | Description |
|-------|-------------|
| **Structure** | Repository has valid structure and profile.json |
| **Activities** | Activities have required fields and valid formats |
| **Content** | Activities have content for quality scoring |
| **Locations** | Activities are in semantically correct locations |

### Required Fields

For each activity, the check verifies:

- `activity_id` - Present, unique, and in `platform_id` format
- `timestamp` - Present and valid ISO 8601 format
- `platform` - Present and recognized (twitter, podcast, blog, youtube, book)
- `activity_type` - Present and valid (create or consume)

### Examples

```bash
# Basic check
metaspn check ./my-content

# Verbose output with all issues
metaspn check ./my-content --verbose

# JSON output for CI/CD
metaspn check ./my-content --json
```

### Output

```
Repository Check: ./my-content
============================================================

Structure: PASS

Activities: PASS

Content Quality: WARN
  - Only 45% of activities have content - quality scoring may be limited

File Locations: PASS

============================================================
READY FOR SCORING
  2 warning(s) - scoring will work but may have reduced accuracy

Total activities: 42390
  Valid: 42390
  With content: 19075
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Ready for scoring |
| 1 | Not ready - errors must be fixed |

### JSON Output

```json
{
  "ready_for_scoring": true,
  "structure": {"passed": true, "errors": [], "warnings": []},
  "activities": {"passed": true, "errors": [], "warnings": []},
  "content": {"passed": true, "errors": [], "warnings": ["Only 45% have content"]},
  "locations": {"passed": true, "errors": [], "warnings": []},
  "summary": {
    "errors": 0,
    "warnings": 2,
    "total_activities": 42390,
    "valid_activities": 42390,
    "activities_with_content": 19075
  }
}
```

---

## `metaspn validate`

Validate repository structure.

```bash
metaspn validate PATH
```

### Example

```bash
metaspn validate ./my-content
```

### Output

```
Validating repository at ./my-content...
Repository structure: OK
  .metaspn: OK
  sources/podcasts: OK
  sources/books: OK
  sources/blogs: OK
  sources/twitter: OK
  artifacts/twitter: OK
  artifacts/podcast: OK
  ...

Repository Info:
  User ID: leo_guinan
  Name: Leo Guinan
  Version: 2.0.0
  Activity Files: 5

Validation: PASSED
```

---

## `metaspn cards`

Generate trading cards from profile.

```bash
metaspn cards PATH [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--output-dir`, `-o` | Output directory (default: ./cards) |
| `--format` | Output format (json/all) |

### Example

```bash
metaspn cards ./my-content --output-dir ./my-cards
```

---

## `metaspn add`

Add an activity to the repository.

```bash
metaspn add PATH PLATFORM [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `PATH` | Repository path |
| `PLATFORM` | Platform (podcast/youtube/twitter/blog) |

### Options

| Option | Description |
|--------|-------------|
| `--title` | Activity title (required) |
| `--content` | Activity content |
| `--url` | URL to content |
| `--duration` | Duration in seconds |
| `--type` | Activity type (create/consume) |
| `--timestamp` | ISO format timestamp |

### Example

```bash
metaspn add ./my-content podcast \
  --title "Episode 42" \
  --duration 3600 \
  --url "https://mypodcast.com/ep42"
```

---

## `metaspn export`

Export profile data to file.

```bash
metaspn export PATH --output FILE [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--format` | Export format (json/csv) |
| `--output`, `-o` | Output file path (required) |
| `--include` | Sections to include (profile/activities/cards) |

### Examples

```bash
# Export profile as JSON
metaspn export ./my-content --format json -o profile.json

# Export with activities
metaspn export ./my-content -o data.json --include profile --include activities
```

---

## `metaspn serve`

Start the API server.

```bash
metaspn serve [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `--host` | Host to bind to (default: 127.0.0.1) |
| `--port` | Port to bind to (default: 8000) |
| `--reload` | Enable auto-reload for development |

### Example

```bash
metaspn serve --port 8080 --host 0.0.0.0
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `METASPN_CACHE_DIR` | Custom cache directory |
| `METASPN_LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) |

---

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | Error (invalid input, missing file, etc.) |

---

## Common Workflows

### Initial Setup

```bash
# Initialize repository
metaspn init ./my-content --user-id "me" --name "My Name"

# (Add activities via external tools)

# Check if ready for scoring
metaspn check ./my-content

# Build indexes
metaspn index ./my-content

# Compute enhancements
metaspn enhance ./my-content

# Generate profile
metaspn profile ./my-content
```

### Regular Updates

```bash
# (New activities added)

# Update indexes incrementally
metaspn index ./my-content

# Compute enhancements for new activities
metaspn enhance ./my-content

# Regenerate profile
metaspn profile ./my-content
```

### Algorithm Updates

```bash
# Archive current scores before updating
metaspn enhance ./my-content --archive-previous

# (Update metaspn package with new algorithms)

# Recompute all enhancements
metaspn enhance ./my-content --force
```
