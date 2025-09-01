"""
Track class for organizing clips in layers on a timeline.
"""
from typing import List, Optional, Union, Iterator, Dict, Any
from enum import Enum

from .clips import Clip, VideoClip, AudioClip, ImageClip, TextClip
from .transitions import Transition


class TrackType(Enum):
    """Types of tracks that can exist on a timeline."""
    VIDEO = "video"
    AUDIO = "audio"
    TEXT = "text"
    COMPOSITE = "composite"  # Can hold multiple clip types


class Track:
    """
    Represents a track on a timeline that contains clips and transitions.
    
    A track is essentially a layer where clips are placed in chronological order.
    Different track types can hold different kinds of clips.
    """
    
    def __init__(
        self,
        track_type: TrackType = TrackType.COMPOSITE,
        name: Optional[str] = None,
        enabled: bool = True,
    ):
        """
        Initialize a track.
        
        Args:
            track_type: The type of track (video, audio, text, composite)
            name: Optional name for the track
            enabled: Whether the track is enabled/visible
        """
        self.track_type = track_type
        self.name = name
        self.enabled = enabled
        self._clips: List[Clip] = []
        self._transitions: Dict[int, Transition] = {}  # clip_index -> transition
        self._properties: Dict[str, Any] = {}
        
        # Track-level properties
        self.opacity = 1.0
        self.muted = False
        self.locked = False
    
    @property
    def clips(self) -> List[Clip]:
        """Get all clips on this track."""
        return self._clips.copy()
    
    @property
    def duration(self) -> float:
        """Calculate the total duration of the track."""
        if not self._clips:
            return 0.0
        return max(clip.end_time for clip in self._clips if clip.duration is not None)
    
    def add_clip(self, clip: Clip, index: Optional[int] = None) -> 'Track':
        """
        Add a clip to the track.
        
        Args:
            clip: The clip to add
            index: Optional index to insert at (default: append)
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If clip type doesn't match track type restrictions
        """
        self._validate_clip_type(clip)
        
        if index is None:
            self._clips.append(clip)
        else:
            self._clips.insert(index, clip)
        
        return self
    
    def remove_clip(self, clip: Union[Clip, int]) -> 'Track':
        """
        Remove a clip from the track.
        
        Args:
            clip: Clip instance or index to remove
            
        Returns:
            Self for method chaining
        """
        if isinstance(clip, int):
            if 0 <= clip < len(self._clips):
                # Remove any transition associated with this clip
                if clip in self._transitions:
                    del self._transitions[clip]
                self._clips.pop(clip)
        else:
            try:
                index = self._clips.index(clip)
                if index in self._transitions:
                    del self._transitions[index]
                self._clips.remove(clip)
            except ValueError:
                pass  # Clip not found, ignore
        
        return self
    
    def insert_clip(self, clip: Clip, index: int) -> 'Track':
        """Insert a clip at a specific index."""
        return self.add_clip(clip, index)
    
    def get_clip(self, index: int) -> Optional[Clip]:
        """Get a clip by index."""
        if 0 <= index < len(self._clips):
            return self._clips[index]
        return None
    
    def find_clips_at_time(self, time: float) -> List[Clip]:
        """Find all clips that are active at a specific time."""
        active_clips = []
        for clip in self._clips:
            if clip.duration is not None:
                if clip.start_time <= time < clip.end_time:
                    active_clips.append(clip)
        return active_clips
    
    def add_transition(self, clip_index: int, transition: Transition) -> 'Track':
        """
        Add a transition after a specific clip.
        
        Args:
            clip_index: Index of the clip after which to add the transition
            transition: The transition to add
            
        Returns:
            Self for method chaining
        """
        if 0 <= clip_index < len(self._clips) - 1:  # Can't add transition after last clip
            self._transitions[clip_index] = transition
        return self
    
    def remove_transition(self, clip_index: int) -> 'Track':
        """Remove a transition after a specific clip."""
        if clip_index in self._transitions:
            del self._transitions[clip_index]
        return self
    
    def get_transition(self, clip_index: int) -> Optional[Transition]:
        """Get the transition after a specific clip."""
        return self._transitions.get(clip_index)
    
    def clear(self) -> 'Track':
        """Remove all clips and transitions from the track."""
        self._clips.clear()
        self._transitions.clear()
        return self
    
    def set_opacity(self, opacity: float) -> 'Track':
        """Set the opacity of the entire track (0.0 to 1.0)."""
        self.opacity = max(0.0, min(1.0, opacity))
        return self
    
    def set_muted(self, muted: bool) -> 'Track':
        """Mute or unmute the track."""
        self.muted = muted
        return self
    
    def set_locked(self, locked: bool) -> 'Track':
        """Lock or unlock the track (prevents modifications)."""
        self.locked = locked
        return self
    
    def set_enabled(self, enabled: bool) -> 'Track':
        """Enable or disable the track."""
        self.enabled = enabled
        return self
    
    def sort_clips_by_time(self) -> 'Track':
        """Sort clips by their start time."""
        self._clips.sort(key=lambda clip: clip.start_time)
        return self
    
    def get_clips_by_type(self, clip_type: type) -> List[Clip]:
        """Get all clips of a specific type."""
        return [clip for clip in self._clips if isinstance(clip, clip_type)]
    
    def set_property(self, key: str, value: Any) -> None:
        """Set a custom property on the track."""
        self._properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a custom property from the track."""
        return self._properties.get(key, default)
    
    def _validate_clip_type(self, clip: Clip) -> None:
        """Validate that the clip type is compatible with the track type."""
        if self.track_type == TrackType.COMPOSITE:
            return  # Composite tracks accept all clip types
        
        valid_types = {
            TrackType.VIDEO: (VideoClip, ImageClip),
            TrackType.AUDIO: (AudioClip,),
            TrackType.TEXT: (TextClip,),
        }
        
        if self.track_type in valid_types:
            allowed_types = valid_types[self.track_type]
            if not isinstance(clip, allowed_types):
                raise ValueError(
                    f"Track type {self.track_type.value} cannot contain {type(clip).__name__}"
                )
    
    def __len__(self) -> int:
        """Return the number of clips on the track."""
        return len(self._clips)
    
    def __iter__(self) -> Iterator[Clip]:
        """Iterate over clips on the track."""
        return iter(self._clips)
    
    def __getitem__(self, index: int) -> Clip:
        """Get a clip by index using bracket notation."""
        return self._clips[index]
    
    def __repr__(self) -> str:
        """String representation of the track."""
        name_part = f" '{self.name}'" if self.name else ""
        return f"Track({self.track_type.value}{name_part}, {len(self._clips)} clips)"
