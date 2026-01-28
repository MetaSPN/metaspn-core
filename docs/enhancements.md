# Enhancement Layers

Enhancement layers store computed metrics separately from raw activity data. This separation allows:

- Recomputing scores without modifying source data
- Tracking score evolution over time
- Using different algorithm versions
- Efficient incremental updates

## Directory Structure

```
artifacts/enhancements/
├── quality_scores/
│   ├── latest.jsonl           # Current quality scores
│   └── history/
│       ├── 2024-01-15_v1.0_algorithm_update.jsonl
│       └── 2024-01-28_v1.1_algorithm_update.jsonl
├── game_signatures/
│   ├── latest.jsonl           # Current game signatures
│   └── history/
└── embeddings/
    ├── latest.jsonl           # Current embeddings
    └── history/
```

## Enhancement Types

### Quality Scores

Measures content quality on a 0-1 scale across multiple dimensions.

**File:** `artifacts/enhancements/quality_scores/latest.jsonl`

```json
{
  "activity_id": "twitter_1327008879046225921",
  "computed_at": "2024-01-28T12:00:00Z",
  "algorithm_version": "1.0",
  "quality_score": 0.85,
  "content_score": 0.90,
  "consistency_score": 0.80,
  "depth_score": 0.75
}
```

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | string | References the source activity |
| `computed_at` | string | When this score was computed |
| `algorithm_version` | string | Version of scoring algorithm |
| `quality_score` | float | Overall quality (0-1) |
| `content_score` | float | Content richness (0-1) |
| `consistency_score` | float | Consistency with other content (0-1) |
| `depth_score` | float | Depth of insight (0-1) |

### Game Signatures

Classifies content according to the Founder Games framework (G1-G6).

**File:** `artifacts/enhancements/game_signatures/latest.jsonl`

```json
{
  "activity_id": "twitter_1327008879046225921",
  "computed_at": "2024-01-28T12:00:00Z",
  "algorithm_version": "1.0",
  "confidence": 0.92,
  "game_signature": {
    "G1": 0.15,
    "G2": 0.10,
    "G3": 0.45,
    "G4": 0.20,
    "G5": 0.05,
    "G6": 0.05,
    "primary_game": "G3",
    "secondary_game": "G4"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | string | References the source activity |
| `computed_at` | string | When this was computed |
| `algorithm_version` | string | Version of classification model |
| `confidence` | float | Confidence in classification (0-1) |
| `game_signature` | object | Game scores and classifications |

#### Game Types

| Game | Description |
|------|-------------|
| G1 | **The Money Game** - Focused on revenue, funding, financial metrics |
| G2 | **The Status Game** - Focused on recognition, reputation, visibility |
| G3 | **The Knowledge Game** - Focused on learning, teaching, insights |
| G4 | **The Network Game** - Focused on relationships, community, connections |
| G5 | **The Impact Game** - Focused on change, mission, making a difference |
| G6 | **The Craft Game** - Focused on excellence, mastery, quality |

### Embeddings

Vector embeddings for semantic search and similarity matching.

**File:** `artifacts/enhancements/embeddings/latest.jsonl`

```json
{
  "activity_id": "twitter_1327008879046225921",
  "computed_at": "2024-01-28T12:00:00Z",
  "algorithm_version": "1.0",
  "model_name": "text-embedding-ada-002",
  "dimensions": 1536,
  "embedding": [0.0023, -0.0142, 0.0089, ...]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `activity_id` | string | References the source activity |
| `computed_at` | string | When embedding was computed |
| `algorithm_version` | string | Version identifier |
| `model_name` | string | Name of embedding model |
| `dimensions` | integer | Vector dimensions |
| `embedding` | array | The embedding vector |

---

## History and Versioning

### When History is Created

History files are created when:

1. **Algorithm updates** - When the scoring/classification algorithm changes
2. **Manual archives** - When explicitly requested via `--archive-previous`
3. **Major recomputes** - When doing a full recomputation

### History File Naming

```
{date}_v{version}_{reason}.jsonl
```

Examples:
- `2024-01-28_v1.0_algorithm_update.jsonl`
- `2024-01-28_v1.0_manual_archive.jsonl`
- `2024-01-28_v1.0_full_recompute.jsonl`

### Using History

**List history files:**
```bash
metaspn history ./my-content --list --type quality_scores
```

**View timeline for an activity:**
```bash
metaspn history ./my-content twitter_1327008879046225921
```

**Programmatic access:**
```python
from metaspn.repo import EnhancementStore

store = EnhancementStore("./my-content")

# List history files
history = store.list_history("quality_scores")

# Get timeline for specific activity
timeline = store.get_enhancement_timeline(
    "twitter_1327008879046225921",
    "quality_scores"
)

for entry in timeline:
    print(f"{entry['computed_at']}: {entry['quality_score']}")
```

---

## Computing Enhancements

### CLI Commands

```bash
# Compute missing enhancements only
metaspn enhance ./my-content

# Force recompute all
metaspn enhance ./my-content --force

# Archive current before recomputing
metaspn enhance ./my-content --archive-previous

# Show enhancement status
metaspn enhance ./my-content --status

# Clear all enhancements
metaspn enhance ./my-content --clear
```

### Programmatic Computation

```python
from metaspn.core.profile import compute_and_store_enhancements

# Compute and store enhancements
result = compute_and_store_enhancements(
    "./my-content",
    force_recompute=False  # Only compute missing
)

print(f"Quality scores computed: {result['quality_scores']}")
print(f"Game signatures computed: {result['game_signatures']}")
```

---

## Joining Enhancements with Activities

### EnhancedActivity

The `EnhancedActivity` class provides a view that joins activities with their enhancements:

```python
from metaspn.repo import EnhancementStore, load_activities

# Load activities
activities = load_activities("./my-content")

# Join with enhancements
store = EnhancementStore("./my-content")
enhanced = store.get_all_enhanced(activities)

for ea in enhanced:
    print(f"{ea.activity_id}")
    print(f"  Quality: {ea.quality_score}")
    print(f"  Primary Game: {ea.game_signature.primary_game if ea.game_signature else 'N/A'}")
```

### Selective Loading

You can choose which enhancement types to load:

```python
enhanced = store.get_all_enhanced(
    activities,
    load_quality=True,
    load_games=True,
    load_embeddings=False  # Skip embeddings for faster loading
)
```

---

## Incremental Processing

### Finding Unprocessed Activities

```python
from metaspn.repo import EnhancementStore, load_activities

store = EnhancementStore("./my-content")
activities = load_activities("./my-content")

# Find activities without quality scores
unprocessed = store.get_unprocessed_activities(
    activities,
    "quality_scores"
)

print(f"{len(unprocessed)} activities need quality scoring")
```

### Appending New Enhancements

```python
from metaspn.core.enhancements import QualityScoreEnhancement

# Compute scores for new activities only
new_scores = compute_quality_for(unprocessed)

# Append to existing file
store.save_quality_scores(new_scores, append=True)
```

---

## Algorithm Versioning

### Current Versions

Check current algorithm versions:

```python
from metaspn.repo import EnhancementStore

store = EnhancementStore("./my-content")
versions = store.get_current_algorithm_versions()

print(versions)
# {
#   "quality_scores": "1.0",
#   "game_signatures": "1.0",
#   "embeddings": "1.0"
# }
```

### Detecting Version Changes

```python
# Check if recomputation is needed
needs_update = store.needs_recompute("quality_scores")

if needs_update:
    print("Algorithm has changed - consider recomputing")
```

---

## Best Practices

### 1. Archive Before Major Updates

When updating algorithms, archive first:

```bash
metaspn enhance ./my-content --archive-previous
```

### 2. Track Algorithm Changes

Include meaningful version numbers that reflect actual changes:
- `1.0` → `1.1` for minor improvements
- `1.0` → `2.0` for major algorithm changes
- Use semantic versioning (major.minor.patch) for clarity

### 3. Document Archive Reasons

Use descriptive reasons when archiving:
- `algorithm_update` - Algorithm code changed
- `model_update` - ML model updated
- `manual_archive` - Manual checkpoint
- `full_recompute` - Complete recomputation

### 4. Monitor Coverage

Regularly check enhancement coverage:

```bash
metaspn enhance ./my-content --status
```

### 5. Consider Embedding Storage

Embeddings can be large (1536+ dimensions per activity). Consider:
- Only computing embeddings when needed
- Storing embeddings separately if storage is a concern
- Using lower-dimensional models for large datasets
