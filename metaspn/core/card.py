"""Card generation system for MetaSPN."""

from dataclasses import dataclass, field
from typing import List, Optional, Literal, TYPE_CHECKING
from datetime import datetime
import json
import hashlib

if TYPE_CHECKING:
    from metaspn.core.profile import UserProfile
    from metaspn.core.level import Badge


CardType = Literal["rookie", "current", "milestone", "seasonal", "special"]


@dataclass
class CardData:
    """Trading card data associated with a user profile."""
    
    level: int
    xp: int
    xp_to_next: int
    rarity: str
    badges: List["Badge"] = field(default_factory=list)
    card_number: Optional[str] = None
    edition: str = "genesis"
    
    @property
    def badge_count(self) -> int:
        """Return number of badges."""
        return len(self.badges)
    
    @property
    def has_rare_badges(self) -> bool:
        """True if any badge is rare or higher."""
        return any(b.rarity in ["rare", "epic", "legendary"] for b in self.badges)
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "rarity": self.rarity,
            "badges": [b.to_dict() for b in self.badges],
            "card_number": self.card_number,
            "edition": self.edition,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CardData":
        """Deserialize from dictionary."""
        from metaspn.core.level import Badge
        
        return cls(
            level=data.get("level", 1),
            xp=data.get("xp", 0),
            xp_to_next=data.get("xp_to_next", 100),
            rarity=data.get("rarity", "common"),
            badges=[Badge.from_dict(b) for b in data.get("badges", [])],
            card_number=data.get("card_number"),
            edition=data.get("edition", "genesis"),
        )


@dataclass
class Card:
    """A generated trading card.
    
    Cards represent a snapshot of a user's profile at a point in time.
    They can be of different types:
        - rookie: First card on a platform
        - current: Current state card
        - milestone: Achievement milestone card
        - seasonal: Time-based special editions
        - special: One-off special cards
    """
    
    # Card identity
    card_id: str
    card_type: CardType
    card_number: str
    edition: str
    
    # Owner info
    user_id: str
    user_name: str
    user_handle: str
    avatar_url: Optional[str] = None
    
    # Platform info
    platform: Optional[str] = None
    
    # Stats snapshot
    level: int = 1
    rarity: str = "common"
    
    # Metrics snapshot
    quality_score: Optional[float] = None
    game_primary: Optional[str] = None
    impact_factor: Optional[float] = None
    
    # Badges
    badges: List[str] = field(default_factory=list)  # Badge IDs
    
    # Timestamps
    generated_at: datetime = field(default_factory=datetime.now)
    snapshot_date: datetime = field(default_factory=datetime.now)
    
    # Visual elements
    border_style: str = "standard"
    background: str = "default"
    effects: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "card_id": self.card_id,
            "card_type": self.card_type,
            "card_number": self.card_number,
            "edition": self.edition,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_handle": self.user_handle,
            "avatar_url": self.avatar_url,
            "platform": self.platform,
            "level": self.level,
            "rarity": self.rarity,
            "quality_score": self.quality_score,
            "game_primary": self.game_primary,
            "impact_factor": self.impact_factor,
            "badges": self.badges,
            "generated_at": self.generated_at.isoformat(),
            "snapshot_date": self.snapshot_date.isoformat(),
            "border_style": self.border_style,
            "background": self.background,
            "effects": self.effects,
        }
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        """Deserialize from dictionary."""
        return cls(
            card_id=data["card_id"],
            card_type=data["card_type"],
            card_number=data["card_number"],
            edition=data.get("edition", "genesis"),
            user_id=data["user_id"],
            user_name=data["user_name"],
            user_handle=data["user_handle"],
            avatar_url=data.get("avatar_url"),
            platform=data.get("platform"),
            level=data.get("level", 1),
            rarity=data.get("rarity", "common"),
            quality_score=data.get("quality_score"),
            game_primary=data.get("game_primary"),
            impact_factor=data.get("impact_factor"),
            badges=data.get("badges", []),
            generated_at=datetime.fromisoformat(data["generated_at"]) if data.get("generated_at") else datetime.now(),
            snapshot_date=datetime.fromisoformat(data["snapshot_date"]) if data.get("snapshot_date") else datetime.now(),
            border_style=data.get("border_style", "standard"),
            background=data.get("background", "default"),
            effects=data.get("effects", []),
        )


class CardGenerator:
    """Generator for trading cards.
    
    Creates cards of various types from user profiles.
    """
    
    # Card number counters (in production, would be persisted)
    _card_counter = 0
    
    # Rarity to visual style mappings
    RARITY_BORDERS = {
        "common": "standard",
        "uncommon": "silver",
        "rare": "gold",
        "epic": "holographic",
        "legendary": "prismatic",
    }
    
    RARITY_BACKGROUNDS = {
        "common": "default",
        "uncommon": "gradient_subtle",
        "rare": "gradient_bold",
        "epic": "animated_subtle",
        "legendary": "animated_bold",
    }
    
    RARITY_EFFECTS = {
        "common": [],
        "uncommon": ["shine"],
        "rare": ["shine", "glow"],
        "epic": ["shine", "glow", "particles"],
        "legendary": ["shine", "glow", "particles", "rainbow"],
    }
    
    def generate_all(self, profile: "UserProfile") -> List[Card]:
        """Generate all applicable cards for a profile.
        
        Args:
            profile: User profile to generate cards from
        
        Returns:
            List of generated Card objects
        """
        cards = []
        
        # Always generate current card
        current_card = self.generate_current_card(profile)
        cards.append(current_card)
        
        # Generate rookie cards for each platform
        for platform in profile.platforms:
            if platform.is_rookie:
                rookie_card = self.generate_rookie_card(profile, platform.platform)
                cards.append(rookie_card)
        
        # Generate milestone cards for significant achievements
        milestone_cards = self.generate_milestone_cards(profile)
        cards.extend(milestone_cards)
        
        return cards
    
    def generate_current_card(self, profile: "UserProfile") -> Card:
        """Generate a current state card.
        
        Args:
            profile: User profile
        
        Returns:
            Current state Card
        """
        rarity = profile.cards.rarity if profile.cards else "common"
        
        # Get metrics for card
        quality_score = None
        game_primary = None
        impact_factor = None
        
        if profile.metrics.creator:
            quality_score = profile.metrics.creator.quality_score
            game_primary = profile.metrics.creator.game_signature.primary_game
            impact_factor = profile.metrics.creator.impact_factor
        
        # Get badge IDs
        badges = []
        if profile.cards and profile.cards.badges:
            badges = [b.badge_id for b in profile.cards.badges[:6]]  # Max 6 badges on card
        
        card_number = self._generate_card_number("current", profile.user_id)
        
        return Card(
            card_id=self._generate_card_id(profile.user_id, "current", None),
            card_type="current",
            card_number=card_number,
            edition=profile.cards.edition if profile.cards else "genesis",
            user_id=profile.user_id,
            user_name=profile.name,
            user_handle=profile.handle,
            avatar_url=profile.avatar_url,
            platform=profile.primary_platform,
            level=profile.cards.level if profile.cards else 1,
            rarity=rarity,
            quality_score=quality_score,
            game_primary=game_primary,
            impact_factor=impact_factor,
            badges=badges,
            border_style=self.RARITY_BORDERS.get(rarity, "standard"),
            background=self.RARITY_BACKGROUNDS.get(rarity, "default"),
            effects=self.RARITY_EFFECTS.get(rarity, []),
        )
    
    def generate_rookie_card(self, profile: "UserProfile", platform: str) -> Card:
        """Generate a rookie card for a platform.
        
        Args:
            profile: User profile
            platform: Platform name
        
        Returns:
            Rookie Card
        """
        # Rookie cards are always common rarity
        rarity = "common"
        
        card_number = self._generate_card_number("rookie", profile.user_id, platform)
        
        return Card(
            card_id=self._generate_card_id(profile.user_id, "rookie", platform),
            card_type="rookie",
            card_number=card_number,
            edition="genesis",
            user_id=profile.user_id,
            user_name=profile.name,
            user_handle=profile.handle,
            avatar_url=profile.avatar_url,
            platform=platform,
            level=1,
            rarity=rarity,
            badges=["first_activity"],
            border_style="rookie_special",
            background="rookie_gradient",
            effects=["rookie_glow"],
        )
    
    def generate_milestone_card(
        self, 
        profile: "UserProfile", 
        milestone: str,
        rarity: str = "rare",
    ) -> Card:
        """Generate a milestone achievement card.
        
        Args:
            profile: User profile
            milestone: Milestone identifier
            rarity: Card rarity
        
        Returns:
            Milestone Card
        """
        card_number = self._generate_card_number("milestone", profile.user_id, milestone)
        
        return Card(
            card_id=self._generate_card_id(profile.user_id, "milestone", milestone),
            card_type="milestone",
            card_number=card_number,
            edition="genesis",
            user_id=profile.user_id,
            user_name=profile.name,
            user_handle=profile.handle,
            avatar_url=profile.avatar_url,
            platform=None,
            level=profile.cards.level if profile.cards else 1,
            rarity=rarity,
            badges=[milestone],
            border_style=self.RARITY_BORDERS.get(rarity, "standard"),
            background="milestone_special",
            effects=["milestone_burst"] + self.RARITY_EFFECTS.get(rarity, []),
        )
    
    def generate_milestone_cards(self, profile: "UserProfile") -> List[Card]:
        """Generate milestone cards for significant achievements.
        
        Args:
            profile: User profile
        
        Returns:
            List of milestone Cards
        """
        cards = []
        
        if not profile.cards or not profile.cards.badges:
            return cards
        
        # Define which badges trigger milestone cards
        milestone_badges = {
            "hundred_activities": "rare",
            "five_hundred_activities": "epic",
            "phase_veteran": "rare",
            "phase_legend": "legendary",
            "quality_creator": "rare",
        }
        
        for badge in profile.cards.badges:
            if badge.badge_id in milestone_badges:
                rarity = milestone_badges[badge.badge_id]
                card = self.generate_milestone_card(profile, badge.badge_id, rarity)
                cards.append(card)
        
        return cards
    
    def _generate_card_id(
        self, 
        user_id: str, 
        card_type: str, 
        extra: Optional[str] = None
    ) -> str:
        """Generate unique card ID."""
        components = [user_id, card_type]
        if extra:
            components.append(extra)
        components.append(datetime.now().isoformat())
        
        raw = "_".join(components)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]
    
    def _generate_card_number(
        self, 
        card_type: str, 
        user_id: str,
        extra: Optional[str] = None,
    ) -> str:
        """Generate card number in format: TYPE-XXXXX."""
        # Create deterministic number from inputs
        components = [card_type, user_id]
        if extra:
            components.append(extra)
        
        raw = "_".join(components)
        hash_val = int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16) % 100000
        
        type_prefix = {
            "rookie": "RK",
            "current": "CR",
            "milestone": "MS",
            "seasonal": "SN",
            "special": "SP",
        }.get(card_type, "XX")
        
        return f"{type_prefix}-{hash_val:05d}"


def generate_cards(profile: "UserProfile") -> List[Card]:
    """Generate all applicable trading cards for a profile.
    
    This is the main entry point for card generation. It creates
    all applicable cards based on the user's profile state.
    
    Args:
        profile: Complete UserProfile object
    
    Returns:
        List of generated Card objects
    
    Example:
        >>> profile = compute_profile("./my-content")
        >>> cards = generate_cards(profile)
        >>> for card in cards:
        ...     print(f"{card.card_type}: {card.rarity}")
    """
    generator = CardGenerator()
    return generator.generate_all(profile)


def generate_card(
    profile: "UserProfile",
    card_type: CardType,
    platform: Optional[str] = None,
) -> Card:
    """Generate a specific type of card.
    
    Args:
        profile: Complete UserProfile object
        card_type: Type of card to generate
        platform: Platform for platform-specific cards
    
    Returns:
        Generated Card object
    """
    generator = CardGenerator()
    
    if card_type == "current":
        return generator.generate_current_card(profile)
    elif card_type == "rookie":
        if platform is None:
            platform = profile.primary_platform or "unknown"
        return generator.generate_rookie_card(profile, platform)
    elif card_type == "milestone":
        return generator.generate_milestone_card(profile, "custom_milestone")
    else:
        return generator.generate_current_card(profile)
