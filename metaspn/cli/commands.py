"""CLI commands for MetaSPN."""

import json
import os
from datetime import datetime
from typing import Any, Optional, TypedDict

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="metaspn")
def cli() -> None:
    """MetaSPN - Measure transformation, not engagement.

    A toolkit for computing development metrics and generating
    trading cards from content repositories.
    """
    pass


@cli.command()
@click.argument("path", type=click.Path())
@click.option("--user-id", required=True, help="Unique user identifier")
@click.option("--name", required=True, help="Display name")
@click.option("--handle", default=None, help="User handle (e.g., @username)")
@click.option("--avatar-url", default=None, help="URL to avatar image")
def init(
    path: str, user_id: str, name: str, handle: Optional[str], avatar_url: Optional[str]
) -> None:
    """Initialize a new MetaSPN repository.

    Creates the directory structure and initial configuration files
    for tracking content and computing profiles.

    Example:
        metaspn init ./my-content --user-id leo_guinan --name "Leo Guinan"
    """
    from metaspn.repo import init_repo

    try:
        user_info = {
            "user_id": user_id,
            "name": name,
            "handle": handle or f"@{user_id}",
        }
        if avatar_url:
            user_info["avatar_url"] = avatar_url

        init_repo(path, user_info)
        click.echo(f"Initialized MetaSPN repository at {path}")
        click.echo(f"  User: {name} ({handle or f'@{user_id}'})")
        click.echo("\nNext steps:")
        click.echo("  1. Add activities to sources/")
        click.echo(f"  2. Run 'metaspn profile {path}' to compute profile")
    except FileExistsError:
        click.echo(f"Error: Repository already exists at {path}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--force", is_flag=True, help="Force recompute (ignore cache)")
@click.option("--output", "-o", default=None, help="Output file for JSON")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--no-enhance", is_flag=True, help="Skip enhancement layer (use embedded scores)")
@click.option("--recompute-enhance", is_flag=True, help="Recompute all enhancements")
def profile(
    path: str,
    force: bool,
    output: Optional[str],
    as_json: bool,
    no_enhance: bool,
    recompute_enhance: bool,
) -> None:
    """Compute user profile from repository.

    Analyzes all activities in the repository and computes
    metrics, lifecycle state, level, rarity, and achievements.

    By default, uses the enhancement layer (artifacts/enhancements/)
    to store and load quality scores and game signatures separately
    from source data.

    Example:
        metaspn profile ./my-content
        metaspn profile ./my-content --force --json
        metaspn profile ./my-content --no-enhance     # Skip enhancement layer
        metaspn profile ./my-content --recompute-enhance  # Recompute all enhancements
    """
    from metaspn import compute_profile
    from metaspn.repo.enhancement_store import EnhancementStore

    try:
        # Handle enhancement recomputation
        if recompute_enhance and not no_enhance:
            click.echo("Clearing existing enhancements...")
            store = EnhancementStore(path)
            store.clear_enhancements()

        click.echo("Computing profile...")

        result = compute_profile(
            path,
            force_recompute=force,
            use_enhancement_store=not no_enhance,
            compute_enhancements=not no_enhance,
        )

        if as_json or output:
            json_output = result.to_json()
            if output:
                with open(output, "w") as f:
                    f.write(json_output)
                click.echo(f"\nProfile saved to {output}")
            else:
                click.echo(json_output)
        else:
            click.echo(f"\nProfile computed for {result.name}")
            click.echo("=" * 50)
            click.echo(f"Handle: {result.handle}")
            click.echo(f"Level: {result.cards.level if result.cards else 'N/A'}")
            click.echo(f"XP: {result.cards.xp if result.cards else 0}")
            click.echo(f"Rarity: {result.cards.rarity if result.cards else 'common'}")

            if result.lifecycle:
                click.echo(f"Phase: {result.lifecycle.phase}")

            if result.platforms:
                click.echo(f"\nPlatforms ({len(result.platforms)}):")
                for platform in result.platforms:
                    click.echo(
                        f"  - {platform.platform}: {platform.role} "
                        f"({platform.activity_count} activities)"
                    )

            if result.metrics.creator:
                click.echo("\nCreator Metrics:")
                creator = result.metrics.creator
                click.echo(f"  Quality Score: {creator.quality_score:.2f}")
                click.echo(f"  Game Alignment: {creator.game_alignment:.2f}")
                click.echo(f"  Impact Factor: {creator.impact_factor:.2f}")
                click.echo(f"  Total Outputs: {creator.total_outputs}")
                if creator.game_signature.primary_game:
                    click.echo(f"  Primary Game: {creator.game_signature.primary_game}")

            if result.metrics.consumer:
                click.echo("\nConsumer Metrics:")
                consumer = result.metrics.consumer
                click.echo(f"  Execution Rate: {consumer.execution_rate:.2f}")
                click.echo(f"  Integration Skill: {consumer.integration_skill:.2f}")
                click.echo(f"  Total Consumed: {consumer.total_consumed}")
                click.echo(f"  Hours Consumed: {consumer.hours_consumed:.1f}")

            if result.cards and result.cards.badges:
                click.echo(f"\nAchievements ({len(result.cards.badges)}):")
                for badge in result.cards.badges[:5]:
                    click.echo(f"  {badge.icon} {badge.name}")
                if len(result.cards.badges) > 5:
                    click.echo(f"  ... and {len(result.cards.badges) - 5} more")

    except FileNotFoundError:
        click.echo(f"Error: Repository not found at {path}", err=True)
        raise SystemExit(1)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="./cards", help="Output directory for cards")
@click.option(
    "--format", "fmt", type=click.Choice(["json", "all"]), default="json", help="Output format"
)
def cards(path: str, output_dir: str, fmt: str) -> None:
    """Generate trading cards from profile.

    Creates card data files for all applicable card types
    based on the user's current profile state.

    Example:
        metaspn cards ./my-content
        metaspn cards ./my-content --output-dir ./my-cards
    """
    from metaspn import compute_profile, generate_cards

    try:
        click.echo("Computing profile...")
        result = compute_profile(path)

        click.echo("Generating cards...")
        card_list = generate_cards(result)

        os.makedirs(output_dir, exist_ok=True)

        for card in card_list:
            filename = f"{card.card_type}_{card.card_number}.json"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w") as f:
                f.write(card.to_json())

            click.echo(f"  Generated: {filename} ({card.rarity})")

        click.echo(f"\nGenerated {len(card_list)} cards in {output_dir}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def stats(path: str) -> None:
    """Show repository statistics.

    Displays summary information about the repository
    including activity counts, platform breakdown, and metrics.

    Example:
        metaspn stats ./my-content
    """
    from metaspn import compute_profile
    from metaspn.repo import get_repo_info

    try:
        info = get_repo_info(path)
        result = compute_profile(path)

        click.echo(f"\n{result.name}")
        click.echo("=" * 50)
        click.echo(f"Handle: {result.handle}")
        click.echo(f"Repository: {info['path']}")
        click.echo(f"Created: {info.get('created_at', 'Unknown')}")
        click.echo(f"Activity Files: {info.get('activity_files', 0)}")

        click.echo("\n--- Level & Rarity ---")
        if result.cards:
            click.echo(f"Level: {result.cards.level}")
            click.echo(f"XP: {result.cards.xp} (next level: {result.cards.xp_to_next} XP)")
            click.echo(f"Rarity: {result.cards.rarity}")

        if result.lifecycle:
            click.echo("\n--- Lifecycle ---")
            click.echo(f"Phase: {result.lifecycle.phase}")
            click.echo(f"Progress: {result.lifecycle.phase_progress * 100:.0f}%")
            if result.lifecycle.next_phase:
                click.echo(f"Next Phase: {result.lifecycle.next_phase}")

        click.echo("\n--- Platforms ---")
        for platform in result.platforms:
            role_emoji = {"creator": "C", "consumer": "c", "hybrid": "H"}[platform.role]
            click.echo(
                f"  [{role_emoji}] {platform.platform}: " f"{platform.activity_count} activities"
            )

        click.echo("\n--- Development ---")
        dev = result.metrics.development
        click.echo(f"Total Activities: {dev.total_activities}")
        click.echo(f"Active Days: {dev.active_days}")
        click.echo(f"Current Streak: {dev.streak_current} days")
        click.echo(f"Longest Streak: {dev.streak_longest} days")
        if dev.first_activity:
            click.echo(f"First Activity: {dev.first_activity.strftime('%Y-%m-%d')}")

        if result.metrics.creator:
            creator = result.metrics.creator
            click.echo("\n--- Creator Metrics ---")
            click.echo(f"Quality: {creator.quality_score:.2f}")
            click.echo(f"Game Alignment: {creator.game_alignment:.2f}")
            click.echo(f"Impact Factor: {creator.impact_factor:.2f}")
            click.echo(f"Consistency: {creator.consistency_score:.2f}")
            click.echo(f"Total Outputs: {creator.total_outputs}")

            # Game signature
            sig = creator.game_signature
            games = [
                ("G1", sig.G1),
                ("G2", sig.G2),
                ("G3", sig.G3),
                ("G4", sig.G4),
                ("G5", sig.G5),
                ("G6", sig.G6),
            ]
            top_games = sorted(games, key=lambda x: x[1], reverse=True)[:3]
            click.echo(f"Top Games: {', '.join(f'{g}:{s:.2f}' for g, s in top_games)}")

        if result.metrics.consumer:
            consumer = result.metrics.consumer
            click.echo("\n--- Consumer Metrics ---")
            click.echo(f"Execution Rate: {consumer.execution_rate:.2f}")
            click.echo(f"Integration Skill: {consumer.integration_skill:.2f}")
            click.echo(f"Discernment: {consumer.discernment:.2f}")
            click.echo(f"Total Consumed: {consumer.total_consumed}")
            click.echo(f"Hours Consumed: {consumer.hours_consumed:.1f}")

        if result.cards and result.cards.badges:
            click.echo(f"\n--- Achievements ({len(result.cards.badges)}) ---")
            for badge in result.cards.badges[:8]:
                click.echo(f"  {badge.icon} {badge.name}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
def validate(path: str) -> None:
    """Validate repository structure.

    Checks that the repository has all required directories
    and files, and that the profile.json is valid.

    Example:
        metaspn validate ./my-content
    """
    from metaspn.repo import get_repo_info, validate_repo
    from metaspn.repo.structure import RepoStructure

    try:
        click.echo(f"Validating repository at {path}...")

        is_valid = validate_repo(path)

        if is_valid:
            click.echo("Repository structure: OK")

            structure = RepoStructure(path)

            # Check directories
            for dir_path in structure.REQUIRED_DIRS:
                full_path = structure.repo_path / dir_path
                status = "OK" if full_path.is_dir() else "MISSING"
                click.echo(f"  {dir_path}: {status}")

            # Get repo info
            info = get_repo_info(path)
            click.echo("\nRepository Info:")
            click.echo(f"  User ID: {info.get('user_id')}")
            click.echo(f"  Name: {info.get('name')}")
            click.echo(f"  Version: {info.get('version')}")
            click.echo(f"  Activity Files: {info.get('activity_files')}")

            click.echo("\nValidation: PASSED")
        else:
            click.echo("Validation: FAILED", err=True)
            click.echo("Repository structure is invalid or incomplete.", err=True)
            raise SystemExit(1)

    except Exception as e:
        click.echo(f"Validation Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--fix", is_flag=True, help="Attempt to fix minor issues")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed error information")
def check(path: str, fix: bool, as_json: bool, verbose: bool) -> None:
    """Check if repository is ready for scoring.

    Performs comprehensive validation of repository content to ensure
    it meets all requirements for proper profile scoring.

    Checks:
    - Repository structure exists
    - Activities have required fields (activity_id, timestamp, platform, activity_type)
    - Activity IDs are unique and properly formatted
    - Timestamps are valid ISO 8601 format
    - Content is present for quality scoring
    - Activities are in correct locations (sources vs artifacts)

    Example:
        metaspn check ./my-content
        metaspn check ./my-content --verbose
        metaspn check ./my-content --fix
    """

    try:
        results = _check_repository(path, fix=fix, verbose=verbose)

        if as_json:
            click.echo(json.dumps(results, indent=2, default=str))
            if not results["ready_for_scoring"]:
                raise SystemExit(1)
            return

        # Display results
        click.echo(f"\nRepository Check: {path}")
        click.echo("=" * 60)

        # Structure check
        _display_check_section("Structure", results["structure"])

        # Activities check
        _display_check_section("Activities", results["activities"])

        # Content check
        _display_check_section("Content Quality", results["content"])

        # Location check
        _display_check_section("File Locations", results["locations"])

        # Summary
        click.echo("\n" + "=" * 60)
        total_errors = results["summary"]["errors"]
        total_warnings = results["summary"]["warnings"]

        if results["ready_for_scoring"]:
            click.echo(click.style("READY FOR SCORING", fg="green", bold=True))
            if total_warnings > 0:
                click.echo(
                    f"  {total_warnings} warning(s) - scoring will work but may have reduced accuracy"
                )
        else:
            click.echo(click.style("NOT READY FOR SCORING", fg="red", bold=True))
            click.echo(f"  {total_errors} error(s) must be fixed")
            if total_warnings > 0:
                click.echo(f"  {total_warnings} warning(s)")

        click.echo(f"\nTotal activities: {results['summary']['total_activities']}")
        click.echo(f"  Valid: {results['summary']['valid_activities']}")
        click.echo(f"  With content: {results['summary']['activities_with_content']}")

        if verbose and results["issues"]:
            click.echo("\n--- Detailed Issues ---")
            for issue in results["issues"][:20]:  # Limit to first 20
                level = "ERROR" if issue["level"] == "error" else "WARN"
                click.echo(f"[{level}] {issue['message']}")
                if issue.get("activity_id"):
                    click.echo(f"        Activity: {issue['activity_id']}")
            if len(results["issues"]) > 20:
                click.echo(f"... and {len(results['issues']) - 20} more issues")

        if not results["ready_for_scoring"]:
            raise SystemExit(1)

    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


class CheckSection(TypedDict):
    """Check section result."""

    passed: bool
    errors: list[str]
    warnings: list[str]


class CheckSummary(TypedDict):
    """Check summary statistics."""

    errors: int
    warnings: int
    total_activities: int
    valid_activities: int
    activities_with_content: int


class CheckIssue(TypedDict):
    """Individual check issue."""

    level: str
    message: str
    activity_id: Optional[str]
    field: Optional[str]


class CheckResults(TypedDict):
    """Complete check results."""

    ready_for_scoring: bool
    structure: CheckSection
    activities: CheckSection
    content: CheckSection
    locations: CheckSection
    summary: CheckSummary
    issues: list[CheckIssue]


def _check_repository(path: str, fix: bool = False, verbose: bool = False) -> CheckResults:
    """Perform comprehensive repository check."""
    from metaspn.repo.reader import RepoReader
    from metaspn.repo.structure import RepoStructure, validate_repo

    results: CheckResults = {
        "ready_for_scoring": True,
        "structure": {"passed": False, "errors": [], "warnings": []},
        "activities": {"passed": False, "errors": [], "warnings": []},
        "content": {"passed": False, "errors": [], "warnings": []},
        "locations": {"passed": False, "errors": [], "warnings": []},
        "summary": {
            "errors": 0,
            "warnings": 0,
            "total_activities": 0,
            "valid_activities": 0,
            "activities_with_content": 0,
        },
        "issues": [],
    }

    # 1. Structure check
    if not validate_repo(path):
        results["structure"]["errors"].append("Invalid repository structure")
        results["ready_for_scoring"] = False
    else:
        results["structure"]["passed"] = True

        structure = RepoStructure(path)

        # Check for profile
        if not structure.profile_path.exists():
            results["structure"]["errors"].append("Missing profile.json")
            results["ready_for_scoring"] = False

    if not results["structure"]["passed"]:
        # Can't continue without valid structure
        results["summary"]["errors"] = len(results["structure"]["errors"])
        return results

    # 2. Load and check activities
    try:
        reader = RepoReader(path)
        activities = reader.load_activities()
    except Exception as e:
        results["activities"]["errors"].append(f"Failed to load activities: {e}")
        results["ready_for_scoring"] = False
        results["summary"]["errors"] = 1
        return results

    results["summary"]["total_activities"] = len(activities)

    if len(activities) == 0:
        results["activities"]["warnings"].append("No activities found - nothing to score")
        results["activities"]["passed"] = True  # Not an error, just empty
    else:
        # Check each activity
        seen_ids: set[str] = set()
        valid_count = 0
        content_count = 0

        for activity in activities:
            activity_issues = _check_activity(activity, seen_ids, verbose)

            for issue in activity_issues:
                results["issues"].append(issue)
                if issue["level"] == "error":
                    results["activities"]["errors"].append(issue["message"])
                else:
                    results["activities"]["warnings"].append(issue["message"])

            # Track validity
            has_errors = any(i["level"] == "error" for i in activity_issues)
            if not has_errors:
                valid_count += 1
                if activity.content:
                    content_count += 1

            seen_ids.add(activity.activity_id)

        results["summary"]["valid_activities"] = valid_count
        results["summary"]["activities_with_content"] = content_count

        # Determine if activities section passed
        activity_errors = [i for i in results["issues"] if i["level"] == "error"]
        results["activities"]["passed"] = len(activity_errors) == 0

        if not results["activities"]["passed"]:
            results["ready_for_scoring"] = False

    # 3. Content quality check
    if results["summary"]["total_activities"] > 0:
        content_ratio = (
            results["summary"]["activities_with_content"] / results["summary"]["total_activities"]
        )

        if content_ratio < 0.5:
            results["content"]["warnings"].append(
                f"Only {content_ratio*100:.0f}% of activities have content - quality scoring may be limited"
            )

        if content_ratio == 0:
            results["content"]["errors"].append(
                "No activities have content - cannot compute quality scores"
            )
            results["ready_for_scoring"] = False
        else:
            results["content"]["passed"] = True
    else:
        results["content"]["passed"] = True

    # 4. Location check
    structure = RepoStructure(path)
    location_issues = _check_activity_locations(activities, structure)

    for issue in location_issues:
        results["issues"].append(issue)
        if issue["level"] == "error":
            results["locations"]["errors"].append(issue["message"])
        else:
            results["locations"]["warnings"].append(issue["message"])

    results["locations"]["passed"] = len(results["locations"]["errors"]) == 0

    # Calculate summary
    results["summary"]["errors"] = sum(
        len(section["errors"])
        for section in [
            results["structure"],
            results["activities"],
            results["content"],
            results["locations"],
        ]
    )
    results["summary"]["warnings"] = sum(
        len(section["warnings"])
        for section in [
            results["structure"],
            results["activities"],
            results["content"],
            results["locations"],
        ]
    )

    return results


def _check_activity(activity: Any, seen_ids: set[str], verbose: bool) -> list[CheckIssue]:
    """Check a single activity for issues."""
    issues: list[CheckIssue] = []

    # Check activity_id
    if not activity.activity_id:
        issues.append(
            {
                "level": "error",
                "message": "Activity missing activity_id",
                "activity_id": None,
                "field": "activity_id",
            }
        )
    elif activity.activity_id in seen_ids:
        issues.append(
            {
                "level": "error",
                "message": f"Duplicate activity_id: {activity.activity_id}",
                "activity_id": activity.activity_id,
                "field": "activity_id",
            }
        )
    elif "_" not in activity.activity_id:
        issues.append(
            {
                "level": "warning",
                "message": f"Activity ID not in recommended format (platform_id): {activity.activity_id}",
                "activity_id": activity.activity_id,
                "field": "activity_id",
            }
        )

    # Check timestamp
    if not activity.timestamp:
        issues.append(
            {
                "level": "error",
                "message": "Activity missing timestamp",
                "activity_id": activity.activity_id,
                "field": "timestamp",
            }
        )

    # Check platform
    valid_platforms = ["twitter", "podcast", "blog", "youtube", "book"]
    if not activity.platform:
        issues.append(
            {
                "level": "error",
                "message": "Activity missing platform",
                "activity_id": activity.activity_id,
                "field": "platform",
            }
        )
    elif activity.platform not in valid_platforms:
        issues.append(
            {
                "level": "warning",
                "message": f"Unknown platform '{activity.platform}' - may not be scored correctly",
                "activity_id": activity.activity_id,
                "field": "platform",
            }
        )

    # Check activity_type
    if not activity.activity_type:
        issues.append(
            {
                "level": "error",
                "message": "Activity missing activity_type",
                "activity_id": activity.activity_id,
                "field": "activity_type",
            }
        )
    elif activity.activity_type not in ["create", "consume"]:
        issues.append(
            {
                "level": "error",
                "message": f"Invalid activity_type '{activity.activity_type}' - must be 'create' or 'consume'",
                "activity_id": activity.activity_id,
                "field": "activity_type",
            }
        )

    # Check content (warning only)
    if not activity.content and not activity.title:
        issues.append(
            {
                "level": "warning",
                "message": "Activity has no content or title - quality scoring will be limited",
                "activity_id": activity.activity_id,
                "field": "content",
            }
        )

    return issues


def _check_activity_locations(activities: list[Any], structure: Any) -> list[CheckIssue]:
    """Check if activities are in semantically correct locations."""
    issues: list[CheckIssue] = []

    # Group by type
    creates = [a for a in activities if a.activity_type == "create"]
    consumes = [a for a in activities if a.activity_type == "consume"]

    # Check that we have the expected distribution
    if len(creates) == 0 and len(consumes) > 0:
        issues.append(
            {
                "level": "warning",
                "message": "No 'create' activities found - only consumption data available",
                "activity_id": None,
                "field": None,
            }
        )

    if len(consumes) == 0 and len(creates) > 0:
        issues.append(
            {
                "level": "warning",
                "message": "No 'consume' activities found - only creation data available",
                "activity_id": None,
                "field": None,
            }
        )

    return issues


def _display_check_section(name: str, section: CheckSection) -> None:
    """Display a check section result."""
    if section["passed"]:
        status = click.style("PASS", fg="green")
    elif section["errors"]:
        status = click.style("FAIL", fg="red")
    else:
        status = click.style("WARN", fg="yellow")

    click.echo(f"\n{name}: {status}")

    # Show unique errors/warnings (deduplicated)
    unique_errors = list(set(section["errors"]))[:3]
    unique_warnings = list(set(section["warnings"]))[:3]

    for error in unique_errors:
        click.echo(click.style(f"  - {error}", fg="red"))

    for warning in unique_warnings:
        click.echo(click.style(f"  - {warning}", fg="yellow"))

    remaining_errors = len(section["errors"]) - len(unique_errors)
    remaining_warnings = len(section["warnings"]) - len(unique_warnings)

    if remaining_errors > 0:
        click.echo(f"  ... and {remaining_errors} more errors")
    if remaining_warnings > 0:
        click.echo(f"  ... and {remaining_warnings} more warnings")


@cli.command("export")
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "--format", "fmt", type=click.Choice(["json", "csv"]), default="json", help="Export format"
)
@click.option("--output", "-o", required=True, help="Output file path")
@click.option(
    "--include", multiple=True, help="Include specific sections (profile, activities, cards)"
)
def export_data(path: str, fmt: str, output: str, include: tuple) -> None:
    """Export profile data to file.

    Exports the computed profile and optionally activities
    and cards to JSON or CSV format.

    Example:
        metaspn export ./my-content --format json --output profile.json
        metaspn export ./my-content --format json -o data.json --include profile --include activities
    """
    from metaspn import compute_profile, generate_cards
    from metaspn.repo import load_activities

    try:
        sections = set(include) if include else {"profile"}

        click.echo("Computing profile...")
        result = compute_profile(path)

        export_data_dict: dict = {}

        if "profile" in sections or not include:
            export_data_dict["profile"] = result.to_dict()

        if "activities" in sections:
            click.echo("Loading activities...")
            activities = load_activities(path)
            export_data_dict["activities"] = [a.to_dict() for a in activities]

        if "cards" in sections:
            click.echo("Generating cards...")
            card_list = generate_cards(result)
            export_data_dict["cards"] = [c.to_dict() for c in card_list]

        if fmt == "json":
            with open(output, "w") as f:
                json.dump(export_data_dict, f, indent=2, default=str)
        elif fmt == "csv":
            # CSV export - flatten profile data
            import csv

            with open(output, "w", newline="") as f:
                if "activities" in export_data_dict:
                    activities_list = export_data_dict["activities"]
                    if activities_list:
                        writer = csv.DictWriter(f, fieldnames=activities_list[0].keys())
                        writer.writeheader()
                        writer.writerows(activities_list)
                else:
                    # Flatten profile for CSV
                    flat_data = {
                        "user_id": result.user_id,
                        "name": result.name,
                        "handle": result.handle,
                        "level": result.cards.level if result.cards else 0,
                        "rarity": result.cards.rarity if result.cards else "common",
                        "phase": result.lifecycle.phase if result.lifecycle else "rookie",
                    }
                    writer = csv.DictWriter(f, fieldnames=flat_data.keys())
                    writer.writeheader()
                    writer.writerow(flat_data)

        click.echo(f"\nExported to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("platform", type=click.Choice(["podcast", "youtube", "twitter", "blog"]))
@click.option("--title", required=True, help="Activity title")
@click.option("--content", default=None, help="Activity content")
@click.option("--url", default=None, help="URL to content")
@click.option("--duration", default=None, type=int, help="Duration in seconds")
@click.option("--type", "activity_type", type=click.Choice(["create", "consume"]), default="create")
@click.option("--timestamp", default=None, help="Activity timestamp (ISO format)")
def add(
    path: str,
    platform: str,
    title: str,
    content: Optional[str],
    url: Optional[str],
    duration: Optional[int],
    activity_type: str,
    timestamp: Optional[str],
) -> None:
    """Add an activity to the repository.

    Adds a new activity record to the appropriate platform
    directory in the repository.

    Example:
        metaspn add ./my-content podcast --title "Episode 1" --duration 3600
        metaspn add ./my-content blog --title "My Post" --content "..."
    """
    from metaspn.core.profile import Activity
    from metaspn.repo import add_activity

    try:
        # Parse timestamp
        if timestamp:
            from metaspn.utils.dates import parse_date

            ts = parse_date(timestamp)
        else:
            ts = datetime.now()

        activity = Activity(
            timestamp=ts,
            platform=platform,
            activity_type=activity_type,
            title=title,
            content=content,
            url=url,
            duration_seconds=duration,
        )

        file_path = add_activity(path, activity)
        click.echo(f"Added activity: {title}")
        click.echo(f"  Platform: {platform}")
        click.echo(f"  Type: {activity_type}")
        click.echo(f"  Saved to: {file_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--force", is_flag=True, help="Force recompute all enhancements")
@click.option("--clear", is_flag=True, help="Clear all enhancements without recomputing")
@click.option("--status", "show_status", is_flag=True, help="Show enhancement status only")
@click.option(
    "--archive-previous", is_flag=True, help="Archive current enhancements before recomputing"
)
def enhance(path: str, force: bool, clear: bool, show_status: bool, archive_previous: bool) -> None:
    """Manage enhancement layers for a repository.

    Computes and stores quality scores and game signatures separately
    from source data. Enhancements are stored in artifacts/enhancements/
    and can be recomputed without modifying source files.

    Example:
        metaspn enhance ./my-content              # Compute missing enhancements
        metaspn enhance ./my-content --force      # Recompute all enhancements
        metaspn enhance ./my-content --status     # Show enhancement status
        metaspn enhance ./my-content --clear      # Clear all enhancements
        metaspn enhance ./my-content --archive-previous  # Archive before recomputing
    """
    from metaspn.core.profile import compute_and_store_enhancements
    from metaspn.repo.enhancement_store import EnhancementStore
    from metaspn.repo.reader import load_activities
    from metaspn.repo.structure import validate_repo

    try:
        if not validate_repo(path):
            click.echo(f"Error: Invalid repository at {path}", err=True)
            raise SystemExit(1)

        store = EnhancementStore(path)

        if clear:
            click.echo("Clearing all enhancements...")
            store.clear_enhancements()
            click.echo("Enhancements cleared.")
            return

        if show_status:
            activities = load_activities(path)
            quality_map = store.load_quality_scores()
            game_map = store.load_game_signatures()
            embedding_map = store.load_embeddings()

            click.echo(f"\nEnhancement Status for {path}")
            click.echo("=" * 50)
            click.echo(f"Total Activities: {len(activities)}")
            click.echo("\nQuality Scores:")
            click.echo(f"  File exists: {store.has_quality_scores()}")
            click.echo(f"  Records: {len(quality_map)}")
            click.echo(f"  Coverage: {len(quality_map)}/{len(activities)} activities")

            click.echo("\nGame Signatures:")
            click.echo(f"  File exists: {store.has_game_signatures()}")
            click.echo(f"  Records: {len(game_map)}")
            click.echo(f"  Coverage: {len(game_map)}/{len(activities)} activities")

            click.echo("\nEmbeddings:")
            click.echo(f"  File exists: {store.has_embeddings()}")
            click.echo(f"  Records: {len(embedding_map)}")
            click.echo(f"  Coverage: {len(embedding_map)}/{len(activities)} activities")

            # Show missing
            missing_quality = len(activities) - len(quality_map)
            missing_games = len(activities) - len(game_map)
            if missing_quality > 0 or missing_games > 0:
                click.echo("\nMissing enhancements:")
                if missing_quality > 0:
                    click.echo(f"  Quality scores: {missing_quality}")
                if missing_games > 0:
                    click.echo(f"  Game signatures: {missing_games}")
                click.echo("\nRun 'metaspn enhance' to compute missing enhancements.")
            else:
                click.echo("\nAll enhancements up to date.")
            return

        # Archive previous if requested
        if archive_previous:
            click.echo("Archiving previous enhancements...")
            for enhancement_type in ["quality_scores", "game_signatures"]:
                latest_path = store.structure.get_enhancement_latest_path(enhancement_type)
                if latest_path.exists():
                    history_dir = store.structure.get_enhancement_history_dir(enhancement_type)
                    archive_path = store._archive_enhancement(
                        latest_path, history_dir, "manual_archive"
                    )
                    click.echo(f"  Archived {enhancement_type} to {archive_path.name}")
            # Clear after archiving
            store.clear_enhancements()

        # Compute enhancements
        click.echo("Computing enhancements...")
        result = compute_and_store_enhancements(path, force_recompute=force or archive_previous)

        click.echo("\nEnhancements computed:")
        click.echo(f"  Quality scores: {result['quality_scores']}")
        click.echo(f"  Game signatures: {result['game_signatures']}")
        click.echo(f"  Total activities: {result['total_activities']}")

        if result["quality_scores"] == 0 and result["game_signatures"] == 0:
            click.echo("\nAll enhancements were already up to date.")
        else:
            click.echo("\nEnhancements saved to artifacts/enhancements/")
            if archive_previous:
                click.echo("(Previous enhancements archived to history/)")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--rebuild", is_flag=True, help="Force rebuild of all indexes")
def index(path: str, rebuild: bool) -> None:
    """Build or rebuild the activity index/manifest.

    Creates indexes for fast filtered loading. The manifest tracks all
    activities by platform, date, and type without loading the full data.

    Example:
        metaspn index ./my-content
        metaspn index ./my-content --rebuild
    """
    from metaspn.repo.manifest import ManifestManager
    from metaspn.repo.structure import validate_repo

    try:
        if not validate_repo(path):
            click.echo(f"Error: Invalid repository at {path}", err=True)
            raise SystemExit(1)

        manager = ManifestManager(path)

        if rebuild:
            click.echo("Rebuilding manifest...")
        elif manager.exists():
            click.echo("Updating manifest...")
        else:
            click.echo("Building manifest...")

        manifest = manager.build(force=rebuild)

        click.echo("\nManifest built successfully")
        click.echo("=" * 50)
        click.echo(f"Total activities: {manifest.total_activities}")
        click.echo(f"Last updated: {manifest.last_updated}")

        if manifest.stats.get("by_platform"):
            click.echo("\nBy platform:")
            for platform, count in manifest.stats["by_platform"].items():
                click.echo(f"  {platform}: {count}")

        if manifest.stats.get("by_type"):
            click.echo("\nBy type:")
            for activity_type, count in manifest.stats["by_type"].items():
                click.echo(f"  {activity_type}: {count}")

        if manifest.stats.get("by_year"):
            years = sorted(manifest.stats["by_year"].keys())
            click.echo(f"\nYear range: {years[0]} - {years[-1]}")

        click.echo("\nIndexes saved to artifacts/indexes/")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--platform", "-p", default=None, help="Filter by platform")
@click.option(
    "--type",
    "activity_type",
    default=None,
    type=click.Choice(["create", "consume"]),
    help="Filter by activity type",
)
@click.option("--since", default=None, help="Filter by start date (YYYY-MM-DD)")
@click.option("--until", default=None, help="Filter by end date (YYYY-MM-DD)")
@click.option("--limit", "-n", default=10, type=int, help="Maximum results to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--count", is_flag=True, help="Show count only")
def query(
    path: str,
    platform: Optional[str],
    activity_type: Optional[str],
    since: Optional[str],
    until: Optional[str],
    limit: int,
    as_json: bool,
    count: bool,
) -> None:
    """Query activities with filters.

    Uses the manifest index when available for fast filtering.

    Example:
        metaspn query ./my-content --platform twitter --limit 10
        metaspn query ./my-content --since 2024-01-01 --until 2024-01-31
        metaspn query ./my-content --type create --count
    """
    from metaspn.repo.loader import ActivityLoader
    from metaspn.repo.structure import validate_repo

    try:
        if not validate_repo(path):
            click.echo(f"Error: Invalid repository at {path}", err=True)
            raise SystemExit(1)

        loader = ActivityLoader(path)

        # Parse dates
        start_date = None
        end_date = None
        if since:
            start_date = datetime.strptime(since, "%Y-%m-%d")
        if until:
            end_date = datetime.strptime(until, "%Y-%m-%d")

        if count:
            # Just count
            total = loader.count(platform=platform, activity_type=activity_type)
            if as_json:
                click.echo(json.dumps({"count": total}))
            else:
                filters = []
                if platform:
                    filters.append(f"platform={platform}")
                if activity_type:
                    filters.append(f"type={activity_type}")
                filter_str = f" ({', '.join(filters)})" if filters else ""
                click.echo(f"Count: {total}{filter_str}")
            return

        # Query activities
        activities = list(
            loader.query(
                platform=platform,
                activity_type=activity_type,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        )

        if as_json:
            click.echo(json.dumps([a.to_dict() for a in activities], default=str, indent=2))
        else:
            click.echo(f"\nFound {len(activities)} activities")
            if platform or activity_type or since or until:
                filters = []
                if platform:
                    filters.append(f"platform={platform}")
                if activity_type:
                    filters.append(f"type={activity_type}")
                if since:
                    filters.append(f"since={since}")
                if until:
                    filters.append(f"until={until}")
                click.echo(f"Filters: {', '.join(filters)}")
            click.echo("=" * 50)

            for activity in activities:
                ts_str = activity.timestamp.strftime("%Y-%m-%d %H:%M")
                title = activity.title or (
                    activity.content[:50] + "..."
                    if activity.content and len(activity.content) > 50
                    else activity.content or ""
                )
                click.echo(f"[{ts_str}] {activity.platform}/{activity.activity_type}: {title}")
                if activity.url:
                    click.echo(f"  URL: {activity.url}")

            if len(activities) == limit:
                click.echo(f"\n(Showing first {limit} results. Use --limit to see more.)")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.argument("activity_id", required=False)
@click.option(
    "--type",
    "enhancement_type",
    default="quality_scores",
    type=click.Choice(["quality_scores", "game_signatures", "embeddings"]),
    help="Enhancement type",
)
@click.option("--list", "list_history", is_flag=True, help="List all history files")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def history(
    path: str,
    activity_id: Optional[str],
    enhancement_type: str,
    list_history: bool,
    as_json: bool,
) -> None:
    """View enhancement history for activities.

    Shows how scores/signatures have evolved over time as algorithms changed.

    Example:
        metaspn history ./my-content --list                    # List history files
        metaspn history ./my-content twitter_123456            # Show history for activity
        metaspn history ./my-content twitter_123456 --type game_signatures
    """
    from metaspn.repo.enhancement_store import EnhancementStore
    from metaspn.repo.structure import validate_repo

    try:
        if not validate_repo(path):
            click.echo(f"Error: Invalid repository at {path}", err=True)
            raise SystemExit(1)

        store = EnhancementStore(path)

        if list_history:
            # List all history files
            history_files = store.list_history(enhancement_type)

            if as_json:
                click.echo(json.dumps([str(f.name) for f in history_files]))
            else:
                click.echo(f"\nEnhancement History: {enhancement_type}")
                click.echo("=" * 50)

                if not history_files:
                    click.echo("No history files found.")
                    click.echo(
                        "(History is created when enhancements are recomputed with --archive-previous)"
                    )
                else:
                    for f in history_files:
                        click.echo(f"  {f.name}")

                # Check current version
                versions = store.get_current_algorithm_versions()
                click.echo(f"\nCurrent algorithm version: {versions[enhancement_type]}")

                needs_recompute = store.needs_recompute(enhancement_type)
                if needs_recompute:
                    click.echo(
                        "(Algorithm has changed - run 'metaspn enhance --archive-previous' to update)"
                    )
            return

        if not activity_id:
            click.echo("Error: activity_id is required (or use --list)", err=True)
            raise SystemExit(1)

        # Get timeline for specific activity
        timeline = store.get_enhancement_timeline(activity_id, enhancement_type)

        if as_json:
            click.echo(json.dumps(timeline, indent=2, default=str))
        else:
            click.echo(f"\nEnhancement Timeline: {activity_id}")
            click.echo(f"Type: {enhancement_type}")
            click.echo("=" * 50)

            if not timeline:
                click.echo("No enhancement history found for this activity.")
            else:
                for entry in timeline:
                    source = entry.pop("_source", "unknown")
                    computed = entry.get("computed_at", "unknown")
                    version = entry.get("algorithm_version", "unknown")

                    click.echo(f"\n[{computed}] v{version} (from {source})")

                    # Show key metrics
                    if enhancement_type == "quality_scores":
                        click.echo(f"  Quality Score: {entry.get('quality_score', 'N/A')}")
                        click.echo(f"  Content Score: {entry.get('content_score', 'N/A')}")
                        click.echo(f"  Consistency Score: {entry.get('consistency_score', 'N/A')}")
                    elif enhancement_type == "game_signatures":
                        sig = entry.get("game_signature", {})
                        click.echo(f"  Primary Game: {sig.get('primary_game', 'N/A')}")
                        click.echo(f"  Confidence: {entry.get('confidence', 'N/A')}")
                    elif enhancement_type == "embeddings":
                        click.echo(f"  Dimensions: {entry.get('dimensions', 'N/A')}")
                        click.echo(f"  Model: {entry.get('model_name', 'N/A')}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the API server.

    Runs the FastAPI server for programmatic access
    to MetaSPN functionality.

    Example:
        metaspn serve
        metaspn serve --port 8080 --host 0.0.0.0
    """
    try:
        import uvicorn

        # Verify the server module can be imported
        from metaspn.api import server as _  # noqa: F401

        click.echo("Starting MetaSPN API server...")
        click.echo(f"  URL: http://{host}:{port}")
        click.echo(f"  Docs: http://{host}:{port}/docs")
        click.echo("  Press Ctrl+C to stop\n")

        uvicorn.run(
            "metaspn.api.server:app",
            host=host,
            port=port,
            reload=reload,
        )
    except ImportError:
        click.echo("Error: uvicorn not installed. Install with: pip install uvicorn", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
