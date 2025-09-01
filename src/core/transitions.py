"""
Transition classes for creating smooth transitions between clips.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from enum import Enum


class TransitionType(Enum):
    """Enumeration of available transition types."""
    CROSSFADE = "crossfade"
    WIPE = "wipe"
    SLIDE = "slide"
    FADE = "fade"
    DISSOLVE = "dissolve"


class WipeDirection(Enum):
    """Direction for wipe transitions."""
    LEFT_TO_RIGHT = "left_to_right"
    RIGHT_TO_LEFT = "right_to_left"
    TOP_TO_BOTTOM = "top_to_bottom"
    BOTTOM_TO_TOP = "bottom_to_top"


class Transition(ABC):
    """
    Abstract base class for all transition types.
    
    Transitions are applied between two clips on the same track
    to create smooth visual or audio transitions.
    """
    
    def __init__(
        self,
        duration: float,
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize a transition.
        
        Args:
            duration: Duration of the transition in seconds
            name: Optional name for the transition
        """
        self.duration = duration
        self.name = name
        self._properties: Dict[str, Any] = {}
    
    def set_property(self, key: str, value: Any) -> None:
        """Set a custom property on the transition."""
        self._properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a custom property from the transition."""
        return self._properties.get(key, default)
    
    @abstractmethod
    def get_type(self) -> TransitionType:
        """Return the type of transition."""
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Return parameters specific to this transition type."""
        pass


class CrossfadeTransition(Transition):
    """
    A crossfade transition that gradually blends between two clips.
    
    This is one of the most common transitions, where the outgoing clip
    fades out while the incoming clip fades in simultaneously.
    """
    
    def __init__(
        self,
        duration: float,
        curve: str = "linear",
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize a crossfade transition.
        
        Args:
            duration: Duration of the crossfade in seconds
            curve: Fade curve type ("linear", "ease_in", "ease_out", "ease_in_out")
            name: Optional name for the transition
        """
        super().__init__(duration, name)
        self.curve = curve
        
        # Validate curve type
        valid_curves = ["linear", "ease_in", "ease_out", "ease_in_out"]
        if curve not in valid_curves:
            raise ValueError(f"Curve must be one of: {valid_curves}")
    
    def get_type(self) -> TransitionType:
        return TransitionType.CROSSFADE
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "curve": self.curve,
            "duration": self.duration,
        }
    
    def set_curve(self, curve: str) -> 'CrossfadeTransition':
        """Set the fade curve type."""
        valid_curves = ["linear", "ease_in", "ease_out", "ease_in_out"]
        if curve not in valid_curves:
            raise ValueError(f"Curve must be one of: {valid_curves}")
        self.curve = curve
        return self


class WipeTransition(Transition):
    """
    A wipe transition that reveals the incoming clip by wiping across the screen.
    
    The incoming clip is revealed in a specific direction while the outgoing
    clip is hidden.
    """
    
    def __init__(
        self,
        duration: float,
        direction: WipeDirection = WipeDirection.LEFT_TO_RIGHT,
        feather: float = 0.0,
        name: Optional[str] = None,
    ):
        """
        Initialize a wipe transition.
        
        Args:
            duration: Duration of the wipe in seconds
            direction: Direction of the wipe
            feather: Softness of the wipe edge (0.0 = hard edge, 1.0 = very soft)
            name: Optional name for the transition
        """
        super().__init__(duration, name)
        self.direction = direction
        self.feather = max(0.0, min(1.0, feather))
    
    def get_type(self) -> TransitionType:
        return TransitionType.WIPE
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "feather": self.feather,
            "duration": self.duration,
        }
    
    def set_direction(self, direction: WipeDirection) -> 'WipeTransition':
        """Set the wipe direction."""
        self.direction = direction
        return self
    
    def set_feather(self, feather: float) -> 'WipeTransition':
        """Set the feather amount (softness of the edge)."""
        self.feather = max(0.0, min(1.0, feather))
        return self


class FadeTransition(Transition):
    """
    A simple fade transition that fades out one clip before the next begins.
    
    Unlike crossfade, this creates a gap where both clips are partially transparent.
    """
    
    def __init__(
        self,
        duration: float,
        fade_color: tuple = (0, 0, 0),  # RGB color to fade to
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize a fade transition.
        
        Args:
            duration: Duration of the fade in seconds
            fade_color: RGB color to fade to/from (default: black)
            name: Optional name for the transition
        """
        super().__init__(duration, name)
        self.fade_color = fade_color
    
    def get_type(self) -> TransitionType:
        return TransitionType.FADE
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "fade_color": self.fade_color,
            "duration": self.duration,
        }
    
    def set_fade_color(self, r: int, g: int, b: int) -> 'FadeTransition':
        """Set the color to fade to/from."""
        self.fade_color = (r, g, b)
        return self


class SlideTransition(Transition):
    """
    A slide transition that slides the incoming clip over the outgoing clip.
    """
    
    def __init__(
        self,
        duration: float,
        direction: WipeDirection = WipeDirection.LEFT_TO_RIGHT,
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize a slide transition.
        
        Args:
            duration: Duration of the slide in seconds
            direction: Direction of the slide
            name: Optional name for the transition
        """
        super().__init__(duration, name)
        self.direction = direction
    
    def get_type(self) -> TransitionType:
        return TransitionType.SLIDE
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "duration": self.duration,
        }
    
    def set_direction(self, direction: WipeDirection) -> 'SlideTransition':
        """Set the slide direction."""
        self.direction = direction
        return self
