"""
Core clip classes representing different types of media content.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from pathlib import Path


@dataclass
class Position:
    """Represents a 2D position on screen."""
    x: float
    y: float


@dataclass
class Size:
    """Represents width and height dimensions."""
    width: float
    height: float


@dataclass
class Color:
    """Represents an RGB color."""
    r: int
    g: int 
    b: int
    a: int = 255  # Alpha channel, 0-255
    
    def to_hex(self) -> str:
        """Convert color to hex string."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"


class Clip(ABC):
    """
    Abstract base class for all clip types.
    
    A clip represents a piece of media content that can be placed
    on a timeline track with specific timing and properties.
    """
    
    def __init__(
        self,
        start_time: float = 0.0,
        duration: Optional[float] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize a clip.
        
        Args:
            start_time: When the clip starts on the timeline (in seconds)
            duration: How long the clip lasts (in seconds)
            name: Optional name for the clip
        """
        self.start_time = start_time
        self.duration = duration
        self.name = name
        self._properties: Dict[str, Any] = {}
    
    @property
    def end_time(self) -> float:
        """Calculate the end time of the clip."""
        if self.duration is None:
            raise ValueError("Cannot calculate end_time without duration")
        return self.start_time + self.duration
    
    def set_property(self, key: str, value: Any) -> None:
        """Set a custom property on the clip."""
        self._properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a custom property from the clip."""
        return self._properties.get(key, default)
    
    @abstractmethod
    def get_type(self) -> str:
        """Return the type of clip."""
        pass


class VideoClip(Clip):
    """
    Represents a video source file.
    
    Contains properties for trimming, scaling, and positioning
    video content on the timeline.
    """
    
    def __init__(
        self,
        source_path: str,
        start_time: float = 0.0,
        duration: Optional[float] = None,
        trim_start: float = 0.0,
        trim_end: Optional[float] = None,
        scale: float = 1.0,
        position: Optional[Position] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize a video clip.
        
        Args:
            source_path: Path to the video file
            start_time: When the clip starts on the timeline
            duration: Duration of the clip (if None, uses source duration - trim)
            trim_start: Start offset within the source video (seconds)
            trim_end: End offset within the source video (seconds)
            scale: Scale factor for the video (1.0 = original size)
            position: Position of the video on screen
            name: Optional name for the clip
        """
        super().__init__(start_time, duration, name)
        self.source_path = Path(source_path)
        self.trim_start = trim_start
        self.trim_end = trim_end
        self.scale = scale
        self.position = position or Position(0, 0)
        
        # Video-specific properties
        self.opacity = 1.0
        self.rotation = 0.0
        self.crop_box: Optional[Tuple[int, int, int, int]] = None  # (x, y, width, height)
    
    def get_type(self) -> str:
        return "video"
    
    def set_opacity(self, opacity: float) -> 'VideoClip':
        """Set the opacity of the video clip (0.0 to 1.0)."""
        self.opacity = max(0.0, min(1.0, opacity))
        return self
    
    def set_rotation(self, degrees: float) -> 'VideoClip':
        """Set the rotation of the video clip in degrees."""
        self.rotation = degrees % 360
        return self
    
    def set_crop(self, x: int, y: int, width: int, height: int) -> 'VideoClip':
        """Set a crop box for the video."""
        self.crop_box = (x, y, width, height)
        return self


class AudioClip(Clip):
    """
    Represents an audio source file.
    
    Contains properties for audio-specific manipulations like
    volume control and audio effects.
    """
    
    def __init__(
        self,
        source_path: str,
        start_time: float = 0.0,
        duration: Optional[float] = None,
        trim_start: float = 0.0,
        trim_end: Optional[float] = None,
        volume: float = 1.0,
        name: Optional[str] = None,
    ):
        """
        Initialize an audio clip.
        
        Args:
            source_path: Path to the audio file
            start_time: When the clip starts on the timeline
            duration: Duration of the clip
            trim_start: Start offset within the source audio
            trim_end: End offset within the source audio
            volume: Volume multiplier (1.0 = original volume)
            name: Optional name for the clip
        """
        super().__init__(start_time, duration, name)
        self.source_path = Path(source_path)
        self.trim_start = trim_start
        self.trim_end = trim_end
        self.volume = volume
        
        # Audio-specific properties
        self.fade_in_duration = 0.0
        self.fade_out_duration = 0.0
        self.muted = False
    
    def get_type(self) -> str:
        return "audio"
    
    def set_volume(self, volume: float) -> 'AudioClip':
        """Set the volume of the audio clip."""
        self.volume = max(0.0, volume)
        return self
    
    def set_fade_in(self, duration: float) -> 'AudioClip':
        """Set fade-in duration in seconds."""
        self.fade_in_duration = max(0.0, duration)
        return self
    
    def set_fade_out(self, duration: float) -> 'AudioClip':
        """Set fade-out duration in seconds."""
        self.fade_out_duration = max(0.0, duration)
        return self
    
    def mute(self, muted: bool = True) -> 'AudioClip':
        """Mute or unmute the audio clip."""
        self.muted = muted
        return self


class ImageClip(Clip):
    """
    Represents a static image with a specified duration.
    
    Can be used for still images, logos, or other static visual content.
    """
    
    def __init__(
        self,
        source_path: str,
        duration: float,
        start_time: float = 0.0,
        scale: float = 1.0,
        position: Optional[Position] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize an image clip.
        
        Args:
            source_path: Path to the image file
            duration: How long to show the image
            start_time: When the clip starts on the timeline
            scale: Scale factor for the image
            position: Position of the image on screen
            name: Optional name for the clip
        """
        super().__init__(start_time, duration, name)
        self.source_path = Path(source_path)
        self.scale = scale
        self.position = position or Position(0, 0)
        
        # Image-specific properties
        self.opacity = 1.0
        self.rotation = 0.0
    
    def get_type(self) -> str:
        return "image"
    
    def set_opacity(self, opacity: float) -> 'ImageClip':
        """Set the opacity of the image clip."""
        self.opacity = max(0.0, min(1.0, opacity))
        return self
    
    def set_rotation(self, degrees: float) -> 'ImageClip':
        """Set the rotation of the image clip."""
        self.rotation = degrees % 360
        return self


class TextClip(Clip):
    """
    Represents text overlay with formatting properties.
    
    Can be used for titles, subtitles, captions, or other text content.
    """
    
    def __init__(
        self,
        text: str,
        duration: float,
        start_time: float = 0.0,
        font_size: int = 24,
        font_family: str = "Arial",
        color: Optional[Color] = None,
        position: Optional[Position] = None,
        size: Optional[Size] = None,
        name: Optional[str] = None,
    ):
        """
        Initialize a text clip.
        
        Args:
            text: The text content to display
            duration: How long to show the text
            start_time: When the clip starts on the timeline
            font_size: Font size in points
            font_family: Font family name
            color: Text color
            position: Position of the text on screen
            size: Size of the text box
            name: Optional name for the clip
        """
        super().__init__(start_time, duration, name)
        self.text = text
        self.font_size = font_size
        self.font_family = font_family
        self.color = color or Color(255, 255, 255)  # White by default
        self.position = position or Position(0, 0)
        self.size = size
        
        # Text-specific properties
        self.bold = False
        self.italic = False
        self.underline = False
        self.alignment = "left"  # left, center, right
        self.background_color: Optional[Color] = None
        self.opacity = 1.0
    
    def get_type(self) -> str:
        return "text"
    
    def set_bold(self, bold: bool = True) -> 'TextClip':
        """Set text to bold."""
        self.bold = bold
        return self
    
    def set_italic(self, italic: bool = True) -> 'TextClip':
        """Set text to italic."""
        self.italic = italic
        return self
    
    def set_alignment(self, alignment: str) -> 'TextClip':
        """Set text alignment ('left', 'center', 'right')."""
        if alignment not in ['left', 'center', 'right']:
            raise ValueError("Alignment must be 'left', 'center', or 'right'")
        self.alignment = alignment
        return self
    
    def set_background(self, color: Color) -> 'TextClip':
        """Set background color for the text."""
        self.background_color = color
        return self
