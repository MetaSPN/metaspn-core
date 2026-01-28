# MetaSPN

**Measure transformation, not engagement.**

MetaSPN is a Python package for computing development metrics and generating trading cards from content repositories. Transform any content repository (podcasts, tweets, blogs, etc.) into observable development metrics and collectible trading cards.

## Installation

```bash
pip install metaspn
```

For development:

```bash
pip install metaspn[dev]
```

## Quick Start

### Initialize a Repository

```python
from metaspn import init_repo

init_repo("./my-content", {
    "user_id": "leo_guinan",
    "name": "Leo Guinan",
    "handle": "@leo_guinan"
})
```

### Add Activities

```python
from metaspn.repo import add_activity
from metaspn.core.profile import Activity
from datetime import datetime

activity = Activity(
    timestamp=datetime.now(),
    platform="podcast",
    activity_type="create",
    title="Episode 1: Getting Started",
    duration_seconds=3600
)

add_activity("./my-content", activity)
```

### Compute Profile

```python
from metaspn import compute_profile

profile = compute_profile("./my-content")

print(f"Level: {profile.cards.level}")
print(f"Quality: {profile.metrics.creator.quality_score:.2f}")
print(f"Rarity: {profile.cards.rarity}")
```

### Generate Cards

```python
from metaspn import generate_cards

cards = generate_cards(profile)

for card in cards:
    print(f"{card.card_type}: {card.platform} - {card.rarity}")
```

## CLI Usage

```bash
# Initialize a new repo
metaspn init ./my-content --user-id leo_guinan --name "Leo Guinan"

# Compute profile
metaspn profile ./my-content

# Generate cards
metaspn cards ./my-content --output ./cards/

# Show stats
metaspn stats ./my-content

# Validate repo
metaspn validate ./my-content

# Export data
metaspn export ./my-content --format json --output profile.json

# Start API server
metaspn serve --port 8000
```

## Core Concepts

### Repository as Database

MetaSPN uses Git repositories as the source of truth. All content and activities are stored as append-only logs, making the system:

- **Deterministic**: Same input always produces the same output
- **Portable**: Your data travels with you
- **Auditable**: Complete history of all changes

### Computed Profiles

Profiles are derived from repository data, not stored separately. This ensures consistency and enables recomputation at any time.

### Six Games Framework

Content is classified into six "games" representing different types of value creation:

- **G1 (Identity/Canon)**: Foundational content that defines who you are
- **G2 (Idea Mining)**: Exploration and discovery of new concepts
- **G3 (Models)**: Framework and system building
- **G4 (Performance)**: Entertainment and engagement
- **G5 (Meaning)**: Deep insight and wisdom sharing
- **G6 (Network)**: Connection and community building

### Trading Cards

MetaSPN generates collectible trading cards that represent your development journey:

- **Rookie Cards**: Your first entries on each platform
- **Current Cards**: Your present state and capabilities
- **Milestone Cards**: Achievement markers along your journey

## API Reference

### Main Functions

- `compute_profile(repo_path, force_recompute=False)` - Compute user profile from repository
- `generate_cards(profile)` - Generate trading cards from profile
- `init_repo(path, user_info)` - Initialize a new MetaSPN repository
- `add_activity(path, activity)` - Add an activity to the repository

### Data Models

- `UserProfile` - Complete user profile with all metrics
- `Activity` - Base activity class for all platform events
- `GameSignature` - Distribution across six games
- `CardData` - Trading card information

## Platforms Supported

- **Podcast** - Episode tracking and analysis
- **YouTube** - Video content metrics
- **Twitter** - Tweet analysis and engagement
- **Blog** - Written content tracking

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://docs.metaspn.network)
- [GitHub Repository](https://github.com/metaspn/metaspn)
- [Issue Tracker](https://github.com/metaspn/metaspn/issues)
