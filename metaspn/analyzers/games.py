"""Game analyzer for MetaSPN."""

from typing import List, Dict, Optional, TYPE_CHECKING
import re

from metaspn.core.metrics import GameSignature
from metaspn.utils.stats import normalize, clamp

if TYPE_CHECKING:
    from metaspn.core.profile import Activity


class GameAnalyzer:
    """Analyzer for classifying content into the six games framework.
    
    The Six Games:
        G1 (Identity/Canon): Foundational content that defines who you are
        G2 (Idea Mining): Exploration and discovery of new concepts
        G3 (Models): Framework and system building
        G4 (Performance): Entertainment and engagement
        G5 (Meaning): Deep insight and wisdom sharing
        G6 (Network): Connection and community building
    
    Classification is based on content analysis, keywords, and patterns.
    """
    
    # Keywords and patterns associated with each game
    GAME_KEYWORDS = {
        "G1": [
            "story", "journey", "origin", "biography", "identity", "mission",
            "values", "philosophy", "manifesto", "beliefs", "principles",
            "who i am", "my story", "about me", "foundation", "core",
        ],
        "G2": [
            "discover", "explore", "research", "analysis", "study", "investigate",
            "curious", "question", "hypothesis", "experiment", "findings",
            "learn", "insight", "observation", "trend", "pattern", "data",
        ],
        "G3": [
            "framework", "model", "system", "method", "process", "template",
            "structure", "blueprint", "guide", "tutorial", "how to", "step by step",
            "architecture", "design", "strategy", "approach", "methodology",
        ],
        "G4": [
            "fun", "entertainment", "story", "narrative", "drama", "humor",
            "engaging", "exciting", "adventure", "experience", "show", "episode",
            "performance", "creative", "artistic", "visual", "audio",
        ],
        "G5": [
            "meaning", "purpose", "wisdom", "insight", "truth", "philosophy",
            "reflection", "contemplation", "lesson", "principle", "value",
            "understanding", "depth", "profound", "essence", "significance",
        ],
        "G6": [
            "community", "network", "connect", "collaborate", "together",
            "conversation", "discussion", "interview", "guest", "partnership",
            "relationship", "social", "group", "collective", "shared",
        ],
    }
    
    # Content type associations
    CONTENT_TYPE_WEIGHTS = {
        "podcast": {"G4": 0.3, "G6": 0.2, "G5": 0.2},
        "youtube": {"G4": 0.4, "G3": 0.2},
        "twitter": {"G6": 0.3, "G2": 0.2},
        "blog": {"G3": 0.3, "G5": 0.3, "G2": 0.2},
    }
    
    def __init__(self) -> None:
        """Initialize game analyzer."""
        # Compile regex patterns for efficiency
        self._keyword_patterns = {
            game: [re.compile(rf"\b{kw}\b", re.IGNORECASE) for kw in keywords]
            for game, keywords in self.GAME_KEYWORDS.items()
        }
    
    def compute(self, activities: List["Activity"]) -> GameSignature:
        """Compute game signature from activities.
        
        Args:
            activities: List of activities to analyze
        
        Returns:
            GameSignature with distribution across games
        """
        if not activities:
            return GameSignature()
        
        # Aggregate scores across all activities
        game_scores = {"G1": 0.0, "G2": 0.0, "G3": 0.0, 
                       "G4": 0.0, "G5": 0.0, "G6": 0.0}
        
        for activity in activities:
            activity_scores = self._analyze_activity(activity)
            for game, score in activity_scores.items():
                game_scores[game] += score
        
        # Normalize to 0-1 range
        total = sum(game_scores.values())
        if total > 0:
            for game in game_scores:
                game_scores[game] = game_scores[game] / total
        
        return GameSignature(
            G1=clamp(game_scores["G1"], 0.0, 1.0),
            G2=clamp(game_scores["G2"], 0.0, 1.0),
            G3=clamp(game_scores["G3"], 0.0, 1.0),
            G4=clamp(game_scores["G4"], 0.0, 1.0),
            G5=clamp(game_scores["G5"], 0.0, 1.0),
            G6=clamp(game_scores["G6"], 0.0, 1.0),
        )
    
    def compute_for_activity(self, activity: "Activity") -> GameSignature:
        """Compute game signature for a single activity.
        
        Args:
            activity: Activity to analyze
        
        Returns:
            GameSignature for this activity
        """
        scores = self._analyze_activity(activity)
        total = sum(scores.values())
        
        if total > 0:
            for game in scores:
                scores[game] = scores[game] / total
        
        return GameSignature(
            G1=clamp(scores["G1"], 0.0, 1.0),
            G2=clamp(scores["G2"], 0.0, 1.0),
            G3=clamp(scores["G3"], 0.0, 1.0),
            G4=clamp(scores["G4"], 0.0, 1.0),
            G5=clamp(scores["G5"], 0.0, 1.0),
            G6=clamp(scores["G6"], 0.0, 1.0),
        )
    
    def _analyze_activity(self, activity: "Activity") -> Dict[str, float]:
        """Analyze a single activity for game signals.
        
        Returns raw scores (not normalized).
        """
        scores = {"G1": 0.0, "G2": 0.0, "G3": 0.0, 
                  "G4": 0.0, "G5": 0.0, "G6": 0.0}
        
        # Analyze text content
        text_to_analyze = ""
        if activity.title:
            text_to_analyze += activity.title + " "
        if activity.content:
            text_to_analyze += activity.content
        
        if text_to_analyze:
            keyword_scores = self._analyze_keywords(text_to_analyze)
            for game, score in keyword_scores.items():
                scores[game] += score
        
        # Add platform-based weights
        platform_weights = self.CONTENT_TYPE_WEIGHTS.get(activity.platform, {})
        for game, weight in platform_weights.items():
            scores[game] += weight
        
        # Analyze existing game signature if present
        if activity.game_signature:
            for game in scores:
                if game in activity.game_signature:
                    scores[game] += activity.game_signature[game] * 2  # Weight existing data higher
        
        return scores
    
    def _analyze_keywords(self, text: str) -> Dict[str, float]:
        """Analyze text for game-related keywords."""
        scores = {"G1": 0.0, "G2": 0.0, "G3": 0.0, 
                  "G4": 0.0, "G5": 0.0, "G6": 0.0}
        
        text_lower = text.lower()
        
        for game, patterns in self._keyword_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text_lower)
                scores[game] += len(matches) * 0.1
        
        return scores
    
    def get_primary_game(self, activities: List["Activity"]) -> Optional[str]:
        """Get the primary (highest scoring) game.
        
        Args:
            activities: List of activities
        
        Returns:
            Primary game identifier or None
        """
        signature = self.compute(activities)
        return signature.primary_game
    
    def get_game_breakdown(self, activities: List["Activity"]) -> dict:
        """Get detailed breakdown of game classification.
        
        Args:
            activities: List of activities
        
        Returns:
            Dictionary with game analysis details
        """
        signature = self.compute(activities)
        
        return {
            "signature": signature.to_dict(),
            "primary_game": signature.primary_game,
            "is_specialist": signature.is_specialist,
            "is_multi_game": signature.is_multi_game,
            "is_balanced": signature.is_balanced,
            "sample_size": len(activities),
        }
    
    def classify_activity_type(self, activity: "Activity") -> str:
        """Classify what type of content an activity represents.
        
        Args:
            activity: Activity to classify
        
        Returns:
            Classification string
        """
        signature = self.compute_for_activity(activity)
        primary = signature.primary_game
        
        if primary is None:
            return "general"
        
        type_names = {
            "G1": "foundational",
            "G2": "exploratory",
            "G3": "instructional",
            "G4": "entertaining",
            "G5": "insightful",
            "G6": "connective",
        }
        
        return type_names.get(primary, "general")
