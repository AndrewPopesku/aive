"""
Timeline class - the main container for organizing video projects.
"""
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from .track import Track, TrackType
from .clips import Clip, VideoClip, AudioClip, TextClip


class Timeline:
    """
    The main container for a video project.
    
    A timeline contains multiple tracks and manages global settings
    like resolution, framerate, and duration. It provides the primary
    interface for building video compositions.
    """
    
    def __init__(
        self,
        width: int = 1920,
        height: int = 1080,
        framerate: float = 30.0,
        name: Optional[str] = None,
    ):
        """
        Initialize a timeline.
        
        Args:
            width: Video width in pixels
            height: Video height in pixels  
            framerate: Video framerate (fps)
            name: Optional name for the timeline
        """
        self.width = width
        self.height = height
        self.framerate = framerate
        self.name = name
        self._tracks: List[Track] = []
        self._properties: Dict[str, Any] = {}
        
        # Timeline settings
        self.background_color = (0, 0, 0)  # RGB black
        self.audio_sample_rate = 44100
        self.audio_channels = 2  # Stereo
    
    @property
    def tracks(self) -> List[Track]:
        """Get all tracks in the timeline."""
        return self._tracks.copy()
    
    @property
    def duration(self) -> float:
        """Calculate the total duration of the timeline."""
        if not self._tracks:
            return 0.0
        return max(track.duration for track in self._tracks if track.enabled)
    
    @property
    def resolution(self) -> tuple:
        """Get the resolution as (width, height) tuple."""
        return (self.width, self.height)
    
    def add_track(self, track: Optional[Track] = None, track_type: TrackType = TrackType.COMPOSITE) -> Track:
        """
        Add a track to the timeline.
        
        Args:
            track: Track to add (if None, creates a new track)
            track_type: Type of track to create if track is None
            
        Returns:
            The added track
        """
        if track is None:
            track = Track(track_type=track_type)
        
        self._tracks.append(track)
        return track
    
    def remove_track(self, track: Union[Track, int]) -> 'Timeline':
        """
        Remove a track from the timeline.
        
        Args:
            track: Track instance or index to remove
            
        Returns:
            Self for method chaining
        """
        if isinstance(track, int):
            if 0 <= track < len(self._tracks):
                self._tracks.pop(track)
        else:
            try:
                self._tracks.remove(track)
            except ValueError:
                pass  # Track not found, ignore
        
        return self
    
    def get_track(self, index: int) -> Optional[Track]:
        """Get a track by index."""
        if 0 <= index < len(self._tracks):
            return self._tracks[index]
        return None
    
    def insert_track(self, track: Track, index: int) -> 'Timeline':
        """Insert a track at a specific index."""
        self._tracks.insert(index, track)
        return self
    
    def move_track(self, from_index: int, to_index: int) -> 'Timeline':
        """Move a track from one index to another."""
        if 0 <= from_index < len(self._tracks) and 0 <= to_index < len(self._tracks):
            track = self._tracks.pop(from_index)
            self._tracks.insert(to_index, track)
        return self
    
    def add_clip(self, clip: Clip, track_index: Optional[int] = None) -> 'Timeline':
        """
        Add a clip to a track.
        
        Args:
            clip: The clip to add
            track_index: Index of track to add to (creates new track if None)
            
        Returns:
            Self for method chaining
        """
        if track_index is None:
            # Create appropriate track type based on clip type
            if isinstance(clip, VideoClip):
                track_type = TrackType.VIDEO
            elif isinstance(clip, AudioClip):
                track_type = TrackType.AUDIO
            elif isinstance(clip, TextClip):
                track_type = TrackType.TEXT
            else:
                track_type = TrackType.COMPOSITE
            
            track = self.add_track(track_type=track_type)
        else:
            track = self.get_track(track_index)
            if track is None:
                raise IndexError(f"Track index {track_index} out of range")
        
        track.add_clip(clip)
        return self
    
    def find_clips_at_time(self, time: float) -> Dict[int, List[Clip]]:
        """
        Find all clips active at a specific time across all tracks.
        
        Args:
            time: Time in seconds to check
            
        Returns:
            Dictionary mapping track indices to lists of active clips
        """
        result = {}
        for i, track in enumerate(self._tracks):
            if track.enabled:
                clips = track.find_clips_at_time(time)
                if clips:
                    result[i] = clips
        return result
    
    def get_all_clips(self) -> List[Clip]:
        """Get all clips from all tracks."""
        all_clips = []
        for track in self._tracks:
            all_clips.extend(track.clips)
        return all_clips
    
    def get_clips_by_type(self, clip_type: type) -> List[Clip]:
        """Get all clips of a specific type from all tracks."""
        clips = []
        for track in self._tracks:
            clips.extend(track.get_clips_by_type(clip_type))
        return clips
    
    def clear_all_tracks(self) -> 'Timeline':
        """Remove all clips from all tracks."""
        for track in self._tracks:
            track.clear()
        return self
    
    def remove_all_tracks(self) -> 'Timeline':
        """Remove all tracks from the timeline."""
        self._tracks.clear()
        return self
    
    def set_resolution(self, width: int, height: int) -> 'Timeline':
        """Set the timeline resolution."""
        self.width = width
        self.height = height
        return self
    
    def set_framerate(self, framerate: float) -> 'Timeline':
        """Set the timeline framerate."""
        self.framerate = framerate
        return self
    
    def set_background_color(self, r: int, g: int, b: int) -> 'Timeline':
        """Set the background color."""
        self.background_color = (r, g, b)
        return self
    
    def set_audio_settings(self, sample_rate: int, channels: int) -> 'Timeline':
        """Set audio settings."""
        self.audio_sample_rate = sample_rate
        self.audio_channels = channels
        return self
    
    def generate_subtitles(
        self, 
        track_index: int = 0, 
        transcription_service: Optional[Any] = None
    ) -> 'Timeline':
        """
        Generate subtitles for an audio track.
        
        This is a placeholder method that will be implemented in the application layer
        once the transcription service ports and adapters are available.
        
        Args:
            track_index: Index of the audio track to transcribe
            transcription_service: Service to use for transcription
            
        Returns:
            Self for method chaining
        """
        # This will be implemented later with proper dependency injection
        raise NotImplementedError("Subtitle generation will be implemented in application layer")
    
    def set_property(self, key: str, value: Any) -> None:
        """Set a custom property on the timeline."""
        self._properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a custom property from the timeline."""
        return self._properties.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert timeline to dictionary representation."""
        return {
            'name': self.name,
            'width': self.width,
            'height': self.height,
            'framerate': self.framerate,
            'background_color': self.background_color,
            'audio_sample_rate': self.audio_sample_rate,
            'audio_channels': self.audio_channels,
            'tracks': len(self._tracks),
            'duration': self.duration,
            'properties': self._properties.copy()
        }
    
    @classmethod
    def create_standard_hd(cls, name: Optional[str] = None) -> 'Timeline':
        """Create a standard 1080p timeline."""
        return cls(1920, 1080, 30.0, name)
    
    @classmethod 
    def create_standard_4k(cls, name: Optional[str] = None) -> 'Timeline':
        """Create a standard 4K timeline."""
        return cls(3840, 2160, 30.0, name)
    
    @classmethod
    def create_square(cls, size: int = 1080, name: Optional[str] = None) -> 'Timeline':
        """Create a square timeline (for social media)."""
        return cls(size, size, 30.0, name)
    
    @classmethod
    def create_vertical(cls, name: Optional[str] = None) -> 'Timeline':
        """Create a vertical timeline (for mobile/stories)."""
        return cls(1080, 1920, 30.0, name)
    
    def __len__(self) -> int:
        """Return the number of tracks."""
        return len(self._tracks)
    
    def __getitem__(self, index: int) -> Track:
        """Get a track by index using bracket notation."""
        return self._tracks[index]
    
    def __repr__(self) -> str:
        """String representation of the timeline."""
        name_part = f" '{self.name}'" if self.name else ""
        return (f"Timeline({self.width}x{self.height}@{self.framerate}fps{name_part}, "
               f"{len(self._tracks)} tracks, {self.duration:.2f}s)")
