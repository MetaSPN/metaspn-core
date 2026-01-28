"""Lifecycle state machine for MetaSPN."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Literal, Optional

if TYPE_CHECKING:
    from metaspn.core.profile import Activity, PlatformPresence, ProfileMetrics


# Lifecycle phases
LifecyclePhase = Literal["rookie", "developing", "established", "veteran", "legend"]


@dataclass
class LifecycleState:
    """Current lifecycle state of a user.

    Phases:
        rookie: New to the platform, <30 days or <10 activities
        developing: Building presence, 30-90 days or 10-50 activities
        established: Consistent presence, 90-365 days or 50-200 activities
        veteran: Long-term contributor, 1-3 years or 200-500 activities
        legend: Exceptional track record, 3+ years or 500+ activities
    """

    phase: LifecyclePhase
    phase_progress: float  # 0.0-1.0 progress to next phase
    days_in_phase: int
    phase_entered: datetime

    # Phase-specific data
    activities_in_phase: int = 0
    next_phase: Optional[LifecyclePhase] = None
    activities_to_next: int = 0

    @property
    def is_rookie(self) -> bool:
        """True if in rookie phase."""
        return self.phase == "rookie"

    @property
    def is_established(self) -> bool:
        """True if established or higher."""
        return self.phase in ["established", "veteran", "legend"]

    @property
    def is_veteran(self) -> bool:
        """True if veteran or legend."""
        return self.phase in ["veteran", "legend"]

    @property
    def is_legend(self) -> bool:
        """True if legend phase."""
        return self.phase == "legend"

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "phase": self.phase,
            "phase_progress": self.phase_progress,
            "days_in_phase": self.days_in_phase,
            "phase_entered": self.phase_entered.isoformat(),
            "activities_in_phase": self.activities_in_phase,
            "next_phase": self.next_phase,
            "activities_to_next": self.activities_to_next,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LifecycleState":
        """Deserialize from dictionary."""
        return cls(
            phase=data["phase"],
            phase_progress=data.get("phase_progress", 0.0),
            days_in_phase=data.get("days_in_phase", 0),
            phase_entered=(
                datetime.fromisoformat(data["phase_entered"])
                if data.get("phase_entered")
                else datetime.now()
            ),
            activities_in_phase=data.get("activities_in_phase", 0),
            next_phase=data.get("next_phase"),
            activities_to_next=data.get("activities_to_next", 0),
        )


class LifecycleStateMachine:
    """State machine for computing lifecycle phase transitions.

    The lifecycle progresses based on both time and activity:

    Phase Thresholds (either condition advances):
        rookie -> developing: 30 days OR 10 activities
        developing -> established: 90 days OR 50 activities
        established -> veteran: 365 days OR 200 activities
        veteran -> legend: 1095 days (3 years) OR 500 activities
    """

    PHASES: list[LifecyclePhase] = ["rookie", "developing", "established", "veteran", "legend"]

    # Activity thresholds for each phase transition
    ACTIVITY_THRESHOLDS = {
        "rookie": 10,
        "developing": 50,
        "established": 200,
        "veteran": 500,
    }

    # Day thresholds for each phase transition
    DAY_THRESHOLDS = {
        "rookie": 30,
        "developing": 90,
        "established": 365,
        "veteran": 1095,  # 3 years
    }

    def compute(
        self,
        activities: list["Activity"],
        platforms: list["PlatformPresence"],
        metrics: "ProfileMetrics",
    ) -> LifecycleState:
        """Compute current lifecycle state based on activities and metrics.

        Args:
            activities: All user activities
            platforms: User's platform presences
            metrics: Computed profile metrics

        Returns:
            Current LifecycleState
        """
        if not activities:
            return LifecycleState(
                phase="rookie",
                phase_progress=0.0,
                days_in_phase=0,
                phase_entered=datetime.now(),
                activities_in_phase=0,
                next_phase="developing",
                activities_to_next=self.ACTIVITY_THRESHOLDS["rookie"],
            )

        # Sort activities by timestamp
        sorted_activities = sorted(activities, key=lambda a: a.timestamp)
        first_activity = sorted_activities[0].timestamp
        total_activities = len(activities)

        # Calculate days since first activity (handle timezone-aware datetimes)
        now = datetime.now()
        if first_activity.tzinfo is not None:
            # Make now timezone-aware if first_activity is
            from datetime import timezone

            now = datetime.now(timezone.utc)
        days_active = (now - first_activity).days

        # Determine current phase
        phase = self._determine_phase(days_active, total_activities)

        # Calculate progress to next phase
        next_phase = self._get_next_phase(phase)
        phase_progress, activities_to_next = self._calculate_progress(
            phase, days_active, total_activities
        )

        # Estimate when current phase was entered
        phase_entered = self._estimate_phase_entry(phase, sorted_activities, days_active)
        # Handle timezone-aware datetimes
        now_for_phase = datetime.now()
        if phase_entered.tzinfo is not None:
            from datetime import timezone

            now_for_phase = datetime.now(timezone.utc)
        days_in_phase = (now_for_phase - phase_entered).days

        # Count activities in current phase
        activities_in_phase = len([a for a in activities if a.timestamp >= phase_entered])

        return LifecycleState(
            phase=phase,
            phase_progress=phase_progress,
            days_in_phase=days_in_phase,
            phase_entered=phase_entered,
            activities_in_phase=activities_in_phase,
            next_phase=next_phase,
            activities_to_next=activities_to_next,
        )

    def _determine_phase(self, days: int, activities: int) -> LifecyclePhase:
        """Determine current phase based on days and activities."""
        # Check from highest to lowest phase
        if (
            days >= self.DAY_THRESHOLDS["veteran"]
            or activities >= self.ACTIVITY_THRESHOLDS["veteran"]
        ):
            return "legend"
        if (
            days >= self.DAY_THRESHOLDS["established"]
            or activities >= self.ACTIVITY_THRESHOLDS["established"]
        ):
            return "veteran"
        if (
            days >= self.DAY_THRESHOLDS["developing"]
            or activities >= self.ACTIVITY_THRESHOLDS["developing"]
        ):
            return "established"
        if (
            days >= self.DAY_THRESHOLDS["rookie"]
            or activities >= self.ACTIVITY_THRESHOLDS["rookie"]
        ):
            return "developing"
        return "rookie"

    def _get_next_phase(self, current: LifecyclePhase) -> Optional[LifecyclePhase]:
        """Get the next phase after current."""
        try:
            idx = self.PHASES.index(current)
            if idx < len(self.PHASES) - 1:
                return self.PHASES[idx + 1]
        except ValueError:
            pass
        return None

    def _calculate_progress(
        self, phase: LifecyclePhase, days: int, activities: int
    ) -> tuple[float, int]:
        """Calculate progress to next phase.

        Returns:
            Tuple of (progress 0.0-1.0, activities needed for next phase)
        """
        if phase == "legend":
            return 1.0, 0

        # Get thresholds for next phase
        day_threshold = self.DAY_THRESHOLDS[phase]
        activity_threshold = self.ACTIVITY_THRESHOLDS[phase]

        # Get previous thresholds (for current phase start)
        prev_phases = self.PHASES[: self.PHASES.index(phase)]
        if prev_phases:
            prev_phase = prev_phases[-1]
            prev_day_threshold = self.DAY_THRESHOLDS.get(prev_phase, 0)
            prev_activity_threshold = self.ACTIVITY_THRESHOLDS.get(prev_phase, 0)
        else:
            prev_day_threshold = 0
            prev_activity_threshold = 0

        # Calculate progress based on both metrics
        day_progress = min(
            1.0, (days - prev_day_threshold) / max(1, day_threshold - prev_day_threshold)
        )
        activity_progress = min(
            1.0,
            (activities - prev_activity_threshold)
            / max(1, activity_threshold - prev_activity_threshold),
        )

        # Use the higher progress
        progress = max(day_progress, activity_progress)

        # Calculate activities needed
        activities_to_next = max(0, activity_threshold - activities)

        return progress, activities_to_next

    def _estimate_phase_entry(
        self,
        phase: LifecyclePhase,
        sorted_activities: list["Activity"],
        days_active: int,
    ) -> datetime:
        """Estimate when user entered current phase."""
        if phase == "rookie":
            return sorted_activities[0].timestamp if sorted_activities else datetime.now()

        # Get the threshold for entering current phase
        phase_idx = self.PHASES.index(phase)
        prev_phase = self.PHASES[phase_idx - 1]

        activity_threshold = self.ACTIVITY_THRESHOLDS.get(prev_phase, 0)
        day_threshold = self.DAY_THRESHOLDS.get(prev_phase, 0)

        # Check which threshold was hit first
        first_activity = sorted_activities[0].timestamp

        # If activity threshold was hit
        if len(sorted_activities) >= activity_threshold:
            return sorted_activities[activity_threshold - 1].timestamp

        # Otherwise use day threshold
        from datetime import timedelta

        return first_activity + timedelta(days=day_threshold)

    def can_advance(self, state: LifecycleState) -> bool:
        """Check if user can advance to next phase."""
        return state.phase_progress >= 1.0 and state.next_phase is not None

    def advance(self, state: LifecycleState) -> LifecycleState:
        """Advance to next phase if possible."""
        if not self.can_advance(state):
            return state

        next_phase = state.next_phase
        if next_phase is None:
            return state

        return LifecycleState(
            phase=next_phase,
            phase_progress=0.0,
            days_in_phase=0,
            phase_entered=datetime.now(),
            activities_in_phase=0,
            next_phase=self._get_next_phase(next_phase),
            activities_to_next=self.ACTIVITY_THRESHOLDS.get(next_phase, 0),
        )
