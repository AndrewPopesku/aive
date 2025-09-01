"""
Placeholder classes and video template system for automated content generation.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import copy

from ..core.timeline import Timeline
from ..core.clips import Clip, VideoClip, AudioClip, ImageClip, TextClip, Position, Color
from ..core.track import Track


class Placeholder(ABC):
    """
    Abstract base class for template placeholders.
    
    Placeholders represent dynamic elements in a video template
    that can be replaced with actual content when the template is filled.
    """
    
    def __init__(self, key: str, description: Optional[str] = None):
        """
        Initialize a placeholder.
        
        Args:
            key: Unique key identifying this placeholder
            description: Human-readable description of the placeholder
        """
        self.key = key
        self.description = description
    
    @abstractmethod
    def create_clip(self, data: Dict[str, Any]) -> Clip:
        """
        Create a clip from template data.
        
        Args:
            data: Dictionary containing the data to fill this placeholder
            
        Returns:
            Clip instance created from the data
        """
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate that the provided data can fill this placeholder.
        
        Args:
            data: Dictionary containing the data to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        pass


class PlaceholderVideo(Placeholder):
    """
    Placeholder for video clips.
    
    Represents a video that will be provided when the template is filled.
    """
    
    def __init__(
        self,
        key: str,
        start_time: float = 0.0,
        duration: Optional[float] = None,
        scale: float = 1.0,
        position: Optional[Position] = None,
        description: Optional[str] = None,
        required_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        allowed_formats: Optional[List[str]] = None,
    ):
        """
        Initialize a video placeholder.
        
        Args:
            key: Unique key identifying this placeholder
            start_time: When the video starts on the timeline
            duration: Duration of the video (if None, uses source duration)
            scale: Scale factor for the video
            position: Position of the video on screen
            description: Human-readable description
            required_duration: Required duration for validation
            max_duration: Maximum allowed duration
            allowed_formats: List of allowed video formats
        """
        super().__init__(key, description)
        self.start_time = start_time
        self.duration = duration
        self.scale = scale
        self.position = position or Position(0, 0)
        self.required_duration = required_duration
        self.max_duration = max_duration
        self.allowed_formats = allowed_formats or ['.mp4', '.mov', '.avi', '.mkv']
    
    def create_clip(self, data: Dict[str, Any]) -> VideoClip:
        """Create a video clip from template data."""
        if self.key not in data:
            raise ValueError(f"Missing required placeholder data: {self.key}")
        
        source_path = data[self.key]
        if isinstance(source_path, dict):
            # Handle complex data structure
            path = source_path.get('path') or source_path.get('file')
            duration = source_path.get('duration', self.duration)
            start_time = source_path.get('start_time', self.start_time)
            scale = source_path.get('scale', self.scale)
        else:
            # Simple path string
            path = source_path
            duration = self.duration
            start_time = self.start_time
            scale = self.scale
        
        return VideoClip(
            source_path=str(path),
            start_time=start_time,
            duration=duration,
            scale=scale,
            position=self.position,
            name=f"{self.key}_video"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate video placeholder data."""
        errors = []
        
        if self.key not in data:
            errors.append(f"Missing required placeholder: {self.key}")
            return errors
        
        source_data = data[self.key]
        if isinstance(source_data, dict):
            path = source_data.get('path') or source_data.get('file')
            duration = source_data.get('duration')
        else:
            path = source_data
            duration = None
        
        if not path:
            errors.append(f"Missing path for placeholder: {self.key}")
        else:
            # Check file extension
            path_str = str(path).lower()
            if not any(path_str.endswith(fmt) for fmt in self.allowed_formats):
                errors.append(
                    f"Invalid format for {self.key}. "
                    f"Allowed: {', '.join(self.allowed_formats)}"
                )
        
        # Validate duration constraints
        if self.required_duration and duration != self.required_duration:
            errors.append(f"Video {self.key} must have duration {self.required_duration}s")
        
        if self.max_duration and duration and duration > self.max_duration:
            errors.append(f"Video {self.key} duration exceeds maximum {self.max_duration}s")
        
        return errors


class PlaceholderAudio(Placeholder):
    """Placeholder for audio clips."""
    
    def __init__(
        self,
        key: str,
        start_time: float = 0.0,
        duration: Optional[float] = None,
        volume: float = 1.0,
        description: Optional[str] = None,
    ):
        super().__init__(key, description)
        self.start_time = start_time
        self.duration = duration
        self.volume = volume
    
    def create_clip(self, data: Dict[str, Any]) -> AudioClip:
        """Create an audio clip from template data."""
        if self.key not in data:
            raise ValueError(f"Missing required placeholder data: {self.key}")
        
        source_path = data[self.key]
        return AudioClip(
            source_path=str(source_path),
            start_time=self.start_time,
            duration=self.duration,
            volume=self.volume,
            name=f"{self.key}_audio"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate audio placeholder data."""
        errors = []
        if self.key not in data:
            errors.append(f"Missing required placeholder: {self.key}")
        return errors


class PlaceholderImage(Placeholder):
    """Placeholder for image clips."""
    
    def __init__(
        self,
        key: str,
        duration: float,
        start_time: float = 0.0,
        scale: float = 1.0,
        position: Optional[Position] = None,
        description: Optional[str] = None,
    ):
        super().__init__(key, description)
        self.duration = duration
        self.start_time = start_time
        self.scale = scale
        self.position = position or Position(0, 0)
    
    def create_clip(self, data: Dict[str, Any]) -> ImageClip:
        """Create an image clip from template data."""
        if self.key not in data:
            raise ValueError(f"Missing required placeholder data: {self.key}")
        
        source_path = data[self.key]
        return ImageClip(
            source_path=str(source_path),
            duration=self.duration,
            start_time=self.start_time,
            scale=self.scale,
            position=self.position,
            name=f"{self.key}_image"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate image placeholder data."""
        errors = []
        if self.key not in data:
            errors.append(f"Missing required placeholder: {self.key}")
        return errors


class PlaceholderText(Placeholder):
    """
    Placeholder for text clips.
    
    Represents text that will be provided when the template is filled.
    """
    
    def __init__(
        self,
        key: str,
        duration: float,
        start_time: float = 0.0,
        font_size: int = 24,
        font_family: str = "Arial",
        color: Optional[Color] = None,
        position: Optional[Position] = None,
        description: Optional[str] = None,
        max_length: Optional[int] = None,
        required: bool = True,
    ):
        """
        Initialize a text placeholder.
        
        Args:
            key: Unique key identifying this placeholder
            duration: How long to show the text
            start_time: When the text starts on the timeline
            font_size: Font size in points
            font_family: Font family name
            color: Text color
            position: Position of the text on screen
            description: Human-readable description
            max_length: Maximum allowed text length
            required: Whether this placeholder must be filled
        """
        super().__init__(key, description)
        self.duration = duration
        self.start_time = start_time
        self.font_size = font_size
        self.font_family = font_family
        self.color = color or Color(255, 255, 255)
        self.position = position or Position(0, 0)
        self.max_length = max_length
        self.required = required
    
    def create_clip(self, data: Dict[str, Any]) -> TextClip:
        """Create a text clip from template data."""
        if self.key not in data:
            if self.required:
                raise ValueError(f"Missing required placeholder data: {self.key}")
            text = ""  # Use empty text for optional placeholders
        else:
            text_data = data[self.key]
            if isinstance(text_data, dict):
                text = text_data.get('text', '')
                font_size = text_data.get('font_size', self.font_size)
                font_family = text_data.get('font_family', self.font_family)
                color_data = text_data.get('color')
                if color_data:
                    if isinstance(color_data, dict):
                        color = Color(**color_data)
                    else:
                        color = self.color
                else:
                    color = self.color
            else:
                text = str(text_data)
                font_size = self.font_size
                font_family = self.font_family
                color = self.color
        
        return TextClip(
            text=text,
            duration=self.duration,
            start_time=self.start_time,
            font_size=font_size,
            font_family=font_family,
            color=color,
            position=self.position,
            name=f"{self.key}_text"
        )
    
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Validate text placeholder data."""
        errors = []
        
        if self.key not in data:
            if self.required:
                errors.append(f"Missing required placeholder: {self.key}")
            return errors
        
        text_data = data[self.key]
        if isinstance(text_data, dict):
            text = text_data.get('text', '')
        else:
            text = str(text_data)
        
        if self.max_length and len(text) > self.max_length:
            errors.append(f"Text for {self.key} exceeds maximum length {self.max_length}")
        
        return errors


@dataclass
class TemplateInfo:
    """Information about a video template."""
    name: str
    description: str
    version: str = "1.0"
    author: Optional[str] = None
    tags: List[str] = None
    duration: Optional[float] = None
    resolution: Optional[tuple] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class VideoTemplate:
    """
    A reusable video template with placeholders.
    
    Templates define the structure of a video with placeholder elements
    that can be filled with dynamic content to generate multiple videos
    from the same template.
    """
    
    def __init__(
        self,
        timeline: Timeline,
        info: Optional[TemplateInfo] = None,
    ):
        """
        Initialize a video template.
        
        Args:
            timeline: Base timeline for the template
            info: Template metadata
        """
        self.timeline = timeline
        self.info = info or TemplateInfo("Untitled Template", "No description")
        self._placeholders: Dict[str, Placeholder] = {}
        self._placeholder_positions: Dict[str, tuple] = {}  # (track_index, clip_index)
        
        # Scan timeline for existing placeholders
        self._scan_for_placeholders()
    
    def add_placeholder(
        self, 
        placeholder: Placeholder, 
        track_index: int, 
        clip_index: Optional[int] = None
    ) -> 'VideoTemplate':
        """
        Add a placeholder to the template.
        
        Args:
            placeholder: Placeholder to add
            track_index: Index of the track to add to
            clip_index: Index within the track (appends if None)
            
        Returns:
            Self for method chaining
        """
        self._placeholders[placeholder.key] = placeholder
        
        # Add to timeline
        if clip_index is None:
            clip_index = len(self.timeline.get_track(track_index).clips)
        
        self._placeholder_positions[placeholder.key] = (track_index, clip_index)
        return self
    
    def remove_placeholder(self, key: str) -> 'VideoTemplate':
        """Remove a placeholder from the template."""
        if key in self._placeholders:
            del self._placeholders[key]
            if key in self._placeholder_positions:
                del self._placeholder_positions[key]
        return self
    
    def get_placeholder(self, key: str) -> Optional[Placeholder]:
        """Get a placeholder by key."""
        return self._placeholders.get(key)
    
    def list_placeholders(self) -> List[str]:
        """Get list of all placeholder keys."""
        return list(self._placeholders.keys())
    
    def fill(self, data: Dict[str, Any]) -> Timeline:
        """
        Fill the template with data to create a concrete timeline.
        
        Args:
            data: Dictionary mapping placeholder keys to their values
            
        Returns:
            New timeline with placeholders replaced by actual content
            
        Raises:
            ValueError: If required placeholders are missing or invalid
        """
        # Validate all placeholders
        all_errors = []
        for placeholder in self._placeholders.values():
            errors = placeholder.validate_data(data)
            all_errors.extend(errors)
        
        if all_errors:
            raise ValueError(f"Template validation failed: {'; '.join(all_errors)}")
        
        # Create a deep copy of the timeline
        filled_timeline = copy.deepcopy(self.timeline)
        
        # Replace placeholders with actual clips
        for key, placeholder in self._placeholders.items():
            if key in self._placeholder_positions:
                track_index, clip_index = self._placeholder_positions[key]
                
                # Create the actual clip
                actual_clip = placeholder.create_clip(data)
                
                # Replace the placeholder in the timeline
                track = filled_timeline.get_track(track_index)
                if track and clip_index < len(track.clips):
                    track._clips[clip_index] = actual_clip
        
        return filled_timeline
    
    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate template data without creating a timeline.
        
        Args:
            data: Dictionary mapping placeholder keys to their values
            
        Returns:
            List of validation error messages (empty if valid)
        """
        all_errors = []
        for placeholder in self._placeholders.values():
            errors = placeholder.validate_data(data)
            all_errors.extend(errors)
        return all_errors
    
    def get_required_data_keys(self) -> List[str]:
        """Get list of required data keys for this template."""
        required_keys = []
        for key, placeholder in self._placeholders.items():
            if isinstance(placeholder, PlaceholderText) and not placeholder.required:
                continue  # Skip optional text placeholders
            required_keys.append(key)
        return required_keys
    
    def get_template_info(self) -> Dict[str, Any]:
        """Get template information as dictionary."""
        return {
            'name': self.info.name,
            'description': self.info.description,
            'version': self.info.version,
            'author': self.info.author,
            'tags': self.info.tags,
            'duration': self.info.duration or self.timeline.duration,
            'resolution': self.info.resolution or (self.timeline.width, self.timeline.height),
            'placeholders': len(self._placeholders),
            'required_keys': self.get_required_data_keys(),
        }
    
    def _scan_for_placeholders(self) -> None:
        """Scan the timeline for existing placeholder clips."""
        # This would be implemented to detect special placeholder clips
        # in the timeline and convert them to Placeholder objects
        pass
    
    @classmethod
    def create_simple_text_template(
        cls,
        name: str,
        text_key: str = "title",
        duration: float = 5.0,
        resolution: tuple = (1920, 1080),
    ) -> 'VideoTemplate':
        """
        Create a simple text-only template.
        
        Args:
            name: Template name
            text_key: Key for the text placeholder
            duration: Duration of the text
            resolution: Video resolution
            
        Returns:
            VideoTemplate with a single text placeholder
        """
        timeline = Timeline(width=resolution[0], height=resolution[1])
        track = timeline.add_track()
        
        template = cls(
            timeline=timeline,
            info=TemplateInfo(name, f"Simple text template with {text_key} placeholder")
        )
        
        # Add text placeholder
        text_placeholder = PlaceholderText(
            key=text_key,
            duration=duration,
            font_size=48,
            position=Position(resolution[0]//4, resolution[1]//2)
        )
        
        template.add_placeholder(text_placeholder, 0)
        return template
    
    def __repr__(self) -> str:
        """String representation of the template."""
        return (f"VideoTemplate('{self.info.name}', "
               f"{len(self._placeholders)} placeholders, "
               f"{self.timeline.duration:.2f}s)")


class TemplateLibrary:
    """Collection of video templates with search and organization features."""
    
    def __init__(self):
        self._templates: Dict[str, VideoTemplate] = {}
        self._categories: Dict[str, List[str]] = {}  # category -> template names
    
    def add_template(self, template: VideoTemplate, category: str = "general") -> None:
        """Add a template to the library."""
        name = template.info.name
        self._templates[name] = template
        
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)
    
    def get_template(self, name: str) -> Optional[VideoTemplate]:
        """Get a template by name."""
        return self._templates.get(name)
    
    def list_templates(self, category: Optional[str] = None) -> List[str]:
        """List all templates, optionally filtered by category."""
        if category is None:
            return list(self._templates.keys())
        return self._categories.get(category, [])
    
    def search_templates(
        self, 
        query: str, 
        search_tags: bool = True, 
        search_description: bool = True
    ) -> List[str]:
        """Search templates by name, tags, or description."""
        query_lower = query.lower()
        matches = []
        
        for name, template in self._templates.items():
            # Search name
            if query_lower in name.lower():
                matches.append(name)
                continue
            
            # Search tags
            if search_tags and any(query_lower in tag.lower() for tag in template.info.tags):
                matches.append(name)
                continue
            
            # Search description
            if search_description and query_lower in template.info.description.lower():
                matches.append(name)
        
        return matches
