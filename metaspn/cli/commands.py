"""CLI commands for MetaSPN."""

import json
import os
from datetime import datetime
from typing import Optional

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
def enhance(path: str, force: bool, clear: bool, show_status: bool) -> None:
    """Manage enhancement layers for a repository.

    Computes and stores quality scores and game signatures separately
    from source data. Enhancements are stored in artifacts/enhancements/
    and can be recomputed without modifying source files.

    Example:
        metaspn enhance ./my-content              # Compute missing enhancements
        metaspn enhance ./my-content --force      # Recompute all enhancements
        metaspn enhance ./my-content --status     # Show enhancement status
        metaspn enhance ./my-content --clear      # Clear all enhancements
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

        # Compute enhancements
        click.echo("Computing enhancements...")
        result = compute_and_store_enhancements(path, force_recompute=force)

        click.echo("\nEnhancements computed:")
        click.echo(f"  Quality scores: {result['quality_scores']}")
        click.echo(f"  Game signatures: {result['game_signatures']}")
        click.echo(f"  Total activities: {result['total_activities']}")

        if result["quality_scores"] == 0 and result["game_signatures"] == 0:
            click.echo("\nAll enhancements were already up to date.")
        else:
            click.echo("\nEnhancements saved to artifacts/enhancements/")

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
