"""
Renderer port interface for video rendering engines.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.timeline import Timeline


class RenderOptions:
    """Configuration options for rendering."""
    
    def __init__(
        self,
        codec: str = "libx264",
        bitrate: Optional[str] = None,
        quality: Optional[str] = None,
        preset: str = "medium",
        audio_codec: str = "aac",
        audio_bitrate: str = "128k",
        output_format: Optional[str] = None,
        temp_audiofile: Optional[str] = None,
        remove_temp: bool = True,
        verbose: bool = False,
        threads: Optional[int] = None,
        logger: Optional[Any] = None,
    ):
        """
        Initialize render options.
        
        Args:
            codec: Video codec to use (e.g., 'libx264', 'libx265')
            bitrate: Video bitrate (e.g., '2000k', '5M')
            quality: Quality setting (e.g., 'low', 'medium', 'high')
            preset: Encoding preset affecting speed/quality tradeoff
            audio_codec: Audio codec to use
            audio_bitrate: Audio bitrate
            output_format: Force output format (inferred from extension if None)
            temp_audiofile: Path for temporary audio file
            remove_temp: Whether to remove temporary files
            verbose: Enable verbose output
            threads: Number of threads to use
            logger: Logger instance for output
        """
        self.codec = codec
        self.bitrate = bitrate
        self.quality = quality
        self.preset = preset
        self.audio_codec = audio_codec
        self.audio_bitrate = audio_bitrate
        self.output_format = output_format
        self.temp_audiofile = temp_audiofile
        self.remove_temp = remove_temp
        self.verbose = verbose
        self.threads = threads
        self.logger = logger
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert options to dictionary."""
        return {
            'codec': self.codec,
            'bitrate': self.bitrate,
            'quality': self.quality,
            'preset': self.preset,
            'audio_codec': self.audio_codec,
            'audio_bitrate': self.audio_bitrate,
            'output_format': self.output_format,
            'temp_audiofile': self.temp_audiofile,
            'remove_temp': self.remove_temp,
            'verbose': self.verbose,
            'threads': self.threads,
        }
    
    @classmethod
    def web_optimized(cls) -> 'RenderOptions':
        """Preset for web-optimized video."""
        return cls(
            codec="libx264",
            preset="medium",
            bitrate="2000k",
            quality="medium"
        )
    
    @classmethod
    def high_quality(cls) -> 'RenderOptions':
        """Preset for high quality video."""
        return cls(
            codec="libx264",
            preset="slow",
            bitrate="8000k",
            quality="high"
        )
    
    @classmethod
    def fast_preview(cls) -> 'RenderOptions':
        """Preset for fast preview rendering."""
        return cls(
            codec="libx264",
            preset="veryfast",
            bitrate="1000k",
            quality="low"
        )


class Renderer(ABC):
    """
    Abstract interface for video rendering engines.
    
    This port defines the contract that all rendering adapters must implement.
    It allows the core domain to remain independent of specific rendering libraries.
    """
    
    @abstractmethod
    def render(
        self, 
        timeline: Timeline, 
        output_path: Path, 
        options: Optional[RenderOptions] = None
    ) -> None:
        """
        Render a timeline to a video file.
        
        Args:
            timeline: The timeline to render
            output_path: Path where the rendered video should be saved
            options: Optional rendering configuration
            
        Raises:
            RenderError: If rendering fails
            FileNotFoundError: If source files are missing
            PermissionError: If unable to write to output path
        """
        pass
    
    @abstractmethod
    def can_render(self, timeline: Timeline) -> bool:
        """
        Check if this renderer can handle the given timeline.
        
        Args:
            timeline: Timeline to check
            
        Returns:
            True if this renderer supports the timeline's features
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported output formats.
        
        Returns:
            List of file extensions (e.g., ['.mp4', '.mov', '.avi'])
        """
        pass
    
    @abstractmethod
    def estimate_render_time(self, timeline: Timeline, options: Optional[RenderOptions] = None) -> float:
        """
        Estimate rendering time in seconds.
        
        Args:
            timeline: Timeline to estimate for
            options: Rendering options
            
        Returns:
            Estimated render time in seconds (rough estimate)
        """
        pass
    
    def get_name(self) -> str:
        """Get the name of this renderer."""
        return self.__class__.__name__
    
    def get_version(self) -> str:
        """Get version information for this renderer."""
        return "unknown"


class RenderError(Exception):
    """Exception raised when rendering fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class RenderProgress:
    """Class for tracking render progress."""
    
    def __init__(self):
        self.current_time = 0.0
        self.total_time = 0.0
        self.current_frame = 0
        self.total_frames = 0
        self.message = ""
        self.is_complete = False
        self.error = None
    
    @property
    def progress_percent(self) -> float:
        """Get progress as percentage (0.0 to 100.0)."""
        if self.total_time <= 0:
            return 0.0
        return min(100.0, (self.current_time / self.total_time) * 100.0)
    
    def update(self, current_time: float, message: str = "") -> None:
        """Update progress."""
        self.current_time = current_time
        self.message = message
        if self.current_time >= self.total_time:
            self.is_complete = True
