"""
TimelineFormat port interface for professional video format interchange.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
from enum import Enum

from ..core.timeline import Timeline


class SupportedFormat(Enum):
    """Supported professional video formats."""
    FCPXML = "fcpxml"  # Final Cut Pro XML
    ALE = "ale"        # Avid Log Exchange
    AAF = "aaf"        # Advanced Authoring Format
    OTIO_JSON = "otio_json"  # OpenTimelineIO JSON
    EDL = "edl"        # Edit Decision List
    XML = "xml"        # Generic XML


class FormatCapability:
    """Describes what features a format supports."""
    
    def __init__(
        self,
        supports_video: bool = True,
        supports_audio: bool = True,
        supports_text: bool = True,
        supports_transitions: bool = True,
        supports_effects: bool = False,
        supports_metadata: bool = True,
        supports_markers: bool = False,
        read_only: bool = False,
    ):
        self.supports_video = supports_video
        self.supports_audio = supports_audio
        self.supports_text = supports_text
        self.supports_transitions = supports_transitions
        self.supports_effects = supports_effects
        self.supports_metadata = supports_metadata
        self.supports_markers = supports_markers
        self.read_only = read_only


class ImportOptions:
    """Options for importing timeline formats."""
    
    def __init__(
        self,
        preserve_paths: bool = True,
        relative_to: Optional[Path] = None,
        ignore_missing_media: bool = False,
        default_framerate: float = 30.0,
        track_mapping: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize import options.
        
        Args:
            preserve_paths: Keep original file paths
            relative_to: Make paths relative to this directory
            ignore_missing_media: Continue import even if media files are missing
            default_framerate: Default framerate if not specified in format
            track_mapping: Map track names/types during import
        """
        self.preserve_paths = preserve_paths
        self.relative_to = relative_to
        self.ignore_missing_media = ignore_missing_media
        self.default_framerate = default_framerate
        self.track_mapping = track_mapping or {}


class ExportOptions:
    """Options for exporting timeline formats."""
    
    def __init__(
        self,
        include_disabled_tracks: bool = False,
        export_media_references: bool = True,
        make_paths_relative: bool = False,
        relative_to: Optional[Path] = None,
        include_metadata: bool = True,
        format_version: Optional[str] = None,
    ):
        """
        Initialize export options.
        
        Args:
            include_disabled_tracks: Export disabled tracks
            export_media_references: Include references to media files
            make_paths_relative: Convert absolute paths to relative
            relative_to: Base directory for relative paths
            include_metadata: Include timeline metadata
            format_version: Specific format version to target
        """
        self.include_disabled_tracks = include_disabled_tracks
        self.export_media_references = export_media_references
        self.make_paths_relative = make_paths_relative
        self.relative_to = relative_to
        self.include_metadata = include_metadata
        self.format_version = format_version


class TimelineFormat(ABC):
    """
    Abstract interface for timeline format adapters.
    
    This port defines the contract for reading and writing professional
    video editing formats, enabling interoperability with industry tools.
    """
    
    @abstractmethod
    def read(self, file_path: Path, options: Optional[ImportOptions] = None) -> Timeline:
        """
        Read a timeline from a file.
        
        Args:
            file_path: Path to the file to read
            options: Optional import configuration
            
        Returns:
            Timeline object created from the file
            
        Raises:
            FormatError: If the file format is invalid or unsupported
            FileNotFoundError: If the file doesn't exist
        """
        pass
    
    @abstractmethod
    def write(
        self, 
        timeline: Timeline, 
        file_path: Path, 
        options: Optional[ExportOptions] = None
    ) -> None:
        """
        Write a timeline to a file.
        
        Args:
            timeline: Timeline to export
            file_path: Path where the file should be written
            options: Optional export configuration
            
        Raises:
            FormatError: If the timeline cannot be represented in this format
            PermissionError: If unable to write to the file path
        """
        pass
    
    @abstractmethod
    def can_read(self, file_path: Path) -> bool:
        """
        Check if this adapter can read the specified file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if this adapter can handle the file
        """
        pass
    
    @abstractmethod
    def can_write(self, timeline: Timeline) -> bool:
        """
        Check if this adapter can write the specified timeline.
        
        Args:
            timeline: Timeline to check
            
        Returns:
            True if this adapter can represent the timeline
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[SupportedFormat]:
        """
        Get list of supported formats.
        
        Returns:
            List of supported format types
        """
        pass
    
    @abstractmethod
    def get_format_capabilities(self, format_type: SupportedFormat) -> FormatCapability:
        """
        Get capabilities of a specific format.
        
        Args:
            format_type: Format to query
            
        Returns:
            Capability description for the format
        """
        pass
    
    def get_file_extensions(self) -> List[str]:
        """
        Get supported file extensions.
        
        Returns:
            List of file extensions (e.g., ['.fcpxml', '.xml'])
        """
        # Default implementation based on supported formats
        extensions = []
        for fmt in self.get_supported_formats():
            if fmt == SupportedFormat.FCPXML:
                extensions.extend(['.fcpxml'])
            elif fmt == SupportedFormat.ALE:
                extensions.extend(['.ale'])
            elif fmt == SupportedFormat.AAF:
                extensions.extend(['.aaf'])
            elif fmt == SupportedFormat.OTIO_JSON:
                extensions.extend(['.otio'])
            elif fmt == SupportedFormat.EDL:
                extensions.extend(['.edl'])
            elif fmt == SupportedFormat.XML:
                extensions.extend(['.xml'])
        return extensions
    
    def get_name(self) -> str:
        """Get the name of this format adapter."""
        return self.__class__.__name__
    
    def get_version(self) -> str:
        """Get version information for this adapter."""
        return "unknown"
    
    def validate_timeline(self, timeline: Timeline) -> List[str]:
        """
        Validate a timeline for export compatibility.
        
        Args:
            timeline: Timeline to validate
            
        Returns:
            List of validation warnings/errors (empty if valid)
        """
        warnings = []
        
        # Basic validation
        if not timeline.tracks:
            warnings.append("Timeline has no tracks")
        
        if timeline.duration <= 0:
            warnings.append("Timeline has zero duration")
        
        # Check for unsupported clip types based on capabilities
        for track in timeline.tracks:
            for clip in track.clips:
                if clip.get_type() == "video" and not self.get_format_capabilities(
                    self.get_supported_formats()[0]
                ).supports_video:
                    warnings.append(f"Format does not support video clips")
                    break
        
        return warnings


class FormatError(Exception):
    """Exception raised when format operations fail."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class UnsupportedFeatureError(FormatError):
    """Exception raised when trying to use unsupported features."""
    pass


class ValidationError(FormatError):
    """Exception raised when timeline validation fails."""
    pass
