"""FastAPI server for MetaSPN."""

import os
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# Request/Response models
class ComputeRequest(BaseModel):
    """Request model for profile computation."""

    repo_path: str = Field(..., description="Path to MetaSPN repository")
    force_recompute: bool = Field(False, description="Force recompute ignoring cache")


class InitRepoRequest(BaseModel):
    """Request model for repository initialization."""

    path: str = Field(..., description="Path where to create repository")
    user_id: str = Field(..., description="Unique user identifier")
    name: str = Field(..., description="Display name")
    handle: Optional[str] = Field(None, description="User handle (e.g., @username)")
    avatar_url: Optional[str] = Field(None, description="URL to avatar image")


class AddActivityRequest(BaseModel):
    """Request model for adding an activity."""

    repo_path: str = Field(..., description="Path to MetaSPN repository")
    platform: str = Field(..., description="Platform name")
    activity_type: str = Field("create", description="Activity type (create/consume)")
    title: str = Field(..., description="Activity title")
    content: Optional[str] = Field(None, description="Activity content")
    url: Optional[str] = Field(None, description="URL to content")
    duration_seconds: Optional[int] = Field(None, description="Duration in seconds")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: str


class ProfileResponse(BaseModel):
    """Profile response model."""

    user_id: str
    name: str
    handle: str
    level: int
    rarity: str
    phase: Optional[str]
    platforms: list[dict[str, Any]]
    metrics: dict[str, Any]
    cards: Optional[dict[str, Any]]


class CardResponse(BaseModel):
    """Card response model."""

    card_id: str
    card_type: str
    card_number: str
    user_name: str
    level: int
    rarity: str


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="MetaSPN API",
        description="Measure transformation, not engagement. API for computing profiles and generating cards.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": "MetaSPN API",
        "version": "0.1.0",
        "description": "Measure transformation, not engagement",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        timestamp=datetime.now().isoformat(),
    )


@app.post("/profile", tags=["Profile"])
async def compute_profile_endpoint(request: ComputeRequest) -> dict[str, Any]:
    """Compute and return user profile from repository.

    This endpoint reads activities from the repository, computes
    all metrics, and returns the complete profile.
    """
    from metaspn import compute_profile
    from metaspn.repo import validate_repo

    # Validate repository exists
    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail=f"Repository not found: {request.repo_path}")

    if not validate_repo(request.repo_path):
        raise HTTPException(status_code=400, detail="Invalid MetaSPN repository")

    try:
        profile = compute_profile(
            request.repo_path,
            force_recompute=request.force_recompute,
        )
        return profile.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile/{user_id}", tags=["Profile"])
async def get_profile_by_user(
    user_id: str,
    base_path: str = Query("./repos", description="Base path for repositories"),
) -> dict[str, Any]:
    """Get profile by user ID.

    Assumes repositories are stored at {base_path}/{user_id}.
    """
    from metaspn import compute_profile
    from metaspn.repo import validate_repo

    repo_path = os.path.join(base_path, user_id)

    if not os.path.exists(repo_path):
        raise HTTPException(status_code=404, detail=f"Repository not found for user: {user_id}")

    if not validate_repo(repo_path):
        raise HTTPException(status_code=400, detail="Invalid MetaSPN repository")

    try:
        profile = compute_profile(repo_path)
        return profile.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cards", tags=["Cards"])
async def generate_cards_endpoint(request: ComputeRequest) -> list[dict[str, Any]]:
    """Generate trading cards for a user.

    Computes the profile and generates all applicable cards.
    """
    from metaspn import compute_profile, generate_cards
    from metaspn.repo import validate_repo

    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail=f"Repository not found: {request.repo_path}")

    if not validate_repo(request.repo_path):
        raise HTTPException(status_code=400, detail="Invalid MetaSPN repository")

    try:
        profile = compute_profile(
            request.repo_path,
            force_recompute=request.force_recompute,
        )
        cards = generate_cards(profile)
        return [card.to_dict() for card in cards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cards/{user_id}", tags=["Cards"])
async def get_cards_by_user(
    user_id: str,
    base_path: str = Query("./repos", description="Base path for repositories"),
) -> list[dict[str, Any]]:
    """Get cards by user ID.

    Assumes repositories are stored at {base_path}/{user_id}.
    """
    from metaspn import compute_profile, generate_cards
    from metaspn.repo import validate_repo

    repo_path = os.path.join(base_path, user_id)

    if not os.path.exists(repo_path):
        raise HTTPException(status_code=404, detail=f"Repository not found for user: {user_id}")

    if not validate_repo(repo_path):
        raise HTTPException(status_code=400, detail="Invalid MetaSPN repository")

    try:
        profile = compute_profile(repo_path)
        cards = generate_cards(profile)
        return [card.to_dict() for card in cards]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/repo/init", tags=["Repository"])
async def init_repo_endpoint(request: InitRepoRequest) -> dict[str, Any]:
    """Initialize a new MetaSPN repository."""
    from metaspn.repo import init_repo

    if os.path.exists(os.path.join(request.path, ".metaspn")):
        raise HTTPException(status_code=400, detail="Repository already exists at this path")

    try:
        user_info = {
            "user_id": request.user_id,
            "name": request.name,
            "handle": request.handle or f"@{request.user_id}",
        }
        if request.avatar_url:
            user_info["avatar_url"] = request.avatar_url

        init_repo(request.path, user_info)

        return {
            "status": "success",
            "message": f"Repository initialized at {request.path}",
            "user_id": request.user_id,
            "name": request.name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/repo/validate", tags=["Repository"])
async def validate_repo_endpoint(
    path: str = Query(..., description="Path to repository"),
) -> dict[str, Any]:
    """Validate a MetaSPN repository structure."""
    from metaspn.repo import get_repo_info, validate_repo

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    is_valid = validate_repo(path)

    if is_valid:
        info = get_repo_info(path)
        return {
            "valid": True,
            "info": info,
        }
    else:
        return {
            "valid": False,
            "info": None,
        }


@app.post("/activity", tags=["Activities"])
async def add_activity_endpoint(request: AddActivityRequest) -> dict[str, Any]:
    """Add an activity to a repository."""
    from metaspn.core.profile import Activity
    from metaspn.repo import add_activity, validate_repo
    from metaspn.utils.dates import parse_date

    if not os.path.exists(request.repo_path):
        raise HTTPException(status_code=404, detail=f"Repository not found: {request.repo_path}")

    if not validate_repo(request.repo_path):
        raise HTTPException(status_code=400, detail="Invalid MetaSPN repository")

    try:
        # Parse timestamp
        if request.timestamp:
            timestamp = parse_date(request.timestamp)
        else:
            timestamp = datetime.now()

        activity = Activity(
            timestamp=timestamp,
            platform=request.platform,
            activity_type=request.activity_type,
            title=request.title,
            content=request.content,
            url=request.url,
            duration_seconds=request.duration_seconds,
        )

        file_path = add_activity(request.repo_path, activity)

        return {
            "status": "success",
            "activity_id": activity.activity_id,
            "file_path": str(file_path),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/activities", tags=["Activities"])
async def get_activities_endpoint(
    path: str = Query(..., description="Path to repository"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(100, description="Maximum number of activities"),
) -> list[dict[str, Any]]:
    """Get activities from a repository."""
    from metaspn.repo import load_activities, validate_repo

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Repository not found: {path}")

    if not validate_repo(path):
        raise HTTPException(status_code=400, detail="Invalid MetaSPN repository")

    try:
        activities = load_activities(path, platform)

        # Apply limit
        activities = activities[-limit:]

        return [a.to_dict() for a in activities]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", tags=["Stats"])
async def get_stats_endpoint(
    path: str = Query(..., description="Path to repository"),
) -> dict[str, Any]:
    """Get repository statistics."""
    from metaspn import compute_profile
    from metaspn.repo import get_repo_info, validate_repo
    from metaspn.repo.reader import RepoReader

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Repository not found: {path}")

    if not validate_repo(path):
        raise HTTPException(status_code=400, detail="Invalid MetaSPN repository")

    try:
        info = get_repo_info(path)
        reader = RepoReader(path)
        platform_stats = reader.get_platform_stats()

        profile = compute_profile(path)

        return {
            "repo_info": info,
            "platform_stats": platform_stats,
            "level": profile.cards.level if profile.cards else 0,
            "rarity": profile.cards.rarity if profile.cards else "common",
            "phase": profile.lifecycle.phase if profile.lifecycle else "rookie",
            "total_activities": profile.metrics.development.total_activities,
            "active_days": profile.metrics.development.active_days,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Any, exc: Exception) -> dict[str, Any]:
    """Handle unexpected exceptions."""
    return {
        "error": True,
        "message": str(exc),
        "type": type(exc).__name__,
    }
