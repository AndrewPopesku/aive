"""
OpenTimelineIO adapter that implements the TimelineFormat port.
"""
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..core.timeline import Timeline
from ..core.track import Track, TrackType
from ..core.clips import VideoClip, AudioClip, ImageClip, TextClip
from ..core.transitions import Transition, TransitionType
from ..ports.timeline_format import (
    TimelineFormat, SupportedFormat, FormatCapability,
    ImportOptions, ExportOptions, FormatError
)

try:
    import opentimelineio as otio
    OTIO_AVAILABLE = True
except ImportError:
    OTIO_AVAILABLE = False
    otio = None


class OTIOFormatter(TimelineFormat):
    """
    OpenTimelineIO-based formatter implementing the TimelineFormat port.
    
    This adapter enables reading and writing professional video editing formats
    like Final Cut Pro XML, AAF, EDL, and OTIO's native JSON format.
    """
    
    def __init__(self):
        """Initialize the OTIO formatter."""
        if not OTIO_AVAILABLE:
            raise ImportError(
                "OpenTimelineIO is required for OTIOFormatter. "
                "Install it with: pip install aive[otio]"
            )
        
        # Check available adapters
        self._available_adapters = otio.adapters.available_adapter_names()
    
    def read(self, file_path: Path, options: Optional[ImportOptions] = None) -> Timeline:
        """
        Read a timeline from a file using OpenTimelineIO.
        
        Args:
            file_path: Path to the file to read
            options: Optional import configuration
            
        Returns:
            Timeline object created from the file
            
        Raises:
            FormatError: If the file format is invalid or unsupported
            FileNotFoundError: If the file doesn't exist
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not self.can_read(file_path):
            raise FormatError(f"Cannot read file format: {file_path.suffix}")
        
        if options is None:
            options = ImportOptions()
        
        try:
            # Read the file using OTIO
            otio_timeline = otio.adapters.read_from_file(str(file_path))
            
            # Convert OTIO timeline to aive Timeline
            return self._convert_from_otio(otio_timeline, options)
            
        except Exception as e:
            raise FormatError(f"Failed to read {file_path}: {str(e)}", {
                'file_path': str(file_path),
                'error': str(e)
            }) from e
    
    def write(
        self, 
        timeline: Timeline, 
        file_path: Path, 
        options: Optional[ExportOptions] = None
    ) -> None:
        """
        Write a timeline to a file using OpenTimelineIO.
        
        Args:
            timeline: Timeline to export
            file_path: Path where the file should be written
            options: Optional export configuration
            
        Raises:
            FormatError: If the timeline cannot be represented in this format
            PermissionError: If unable to write to the file path
        """
        if not self.can_write(timeline):
            raise FormatError("Timeline contains features not supported by target format")
        
        if options is None:
            options = ExportOptions()
        
        try:
            # Convert aive Timeline to OTIO timeline
            otio_timeline = self._convert_to_otio(timeline, options)
            
            # Write the file using OTIO
            otio.adapters.write_to_file(otio_timeline, str(file_path))
            
        except Exception as e:
            raise FormatError(f"Failed to write {file_path}: {str(e)}", {
                'file_path': str(file_path),
                'timeline_name': timeline.name,
                'error': str(e)
            }) from e
    
    def can_read(self, file_path: Path) -> bool:
        """
        Check if this adapter can read the specified file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if this adapter can handle the file
        """
        if not OTIO_AVAILABLE:
            return False
        
        extension = file_path.suffix.lower()
        
        # Check supported extensions
        supported_extensions = self.get_file_extensions()
        if extension not in supported_extensions:
            return False
        
        # Check if OTIO has an appropriate adapter
        try:
            adapter_name = otio.adapters.from_filepath(str(file_path))
            return adapter_name in self._available_adapters
        except:
            return False
    
    def can_write(self, timeline: Timeline) -> bool:
        """
        Check if this adapter can write the specified timeline.
        
        Args:
            timeline: Timeline to check
            
        Returns:
            True if this adapter can represent the timeline
        """
        if not OTIO_AVAILABLE:
            return False
        
        # Basic validation - OTIO is quite flexible
        # Most aive features can be represented in OTIO
        return True
    
    def get_supported_formats(self) -> List[SupportedFormat]:
        """
        Get list of supported formats.
        
        Returns:
            List of supported format types
        """
        formats = [SupportedFormat.OTIO_JSON]
        
        if OTIO_AVAILABLE:
            # Check which adapters are available
            if 'fcp_xml' in self._available_adapters:
                formats.append(SupportedFormat.FCPXML)
            if 'ale' in self._available_adapters:
                formats.append(SupportedFormat.ALE)
            if 'aaf' in self._available_adapters:
                formats.append(SupportedFormat.AAF)
            if 'edl' in self._available_adapters:
                formats.append(SupportedFormat.EDL)
        
        return formats
    
    def get_format_capabilities(self, format_type: SupportedFormat) -> FormatCapability:
        """
        Get capabilities of a specific format.
        
        Args:
            format_type: Format to query
            
        Returns:
            Capability description for the format
        """
        capabilities = {
            SupportedFormat.OTIO_JSON: FormatCapability(
                supports_video=True,
                supports_audio=True,
                supports_text=True,
                supports_transitions=True,
                supports_effects=True,
                supports_metadata=True,
                supports_markers=True,
            ),
            SupportedFormat.FCPXML: FormatCapability(
                supports_video=True,
                supports_audio=True,
                supports_text=True,
                supports_transitions=True,
                supports_effects=False,  # Limited
                supports_metadata=True,
                supports_markers=True,
            ),
            SupportedFormat.ALE: FormatCapability(
                supports_video=False,
                supports_audio=False,
                supports_text=False,
                supports_transitions=False,
                supports_effects=False,
                supports_metadata=True,
                supports_markers=False,
                read_only=True,  # ALE is primarily metadata
            ),
            SupportedFormat.EDL: FormatCapability(
                supports_video=True,
                supports_audio=True,
                supports_text=False,
                supports_transitions=True,
                supports_effects=False,
                supports_metadata=False,
                supports_markers=False,
            ),
            SupportedFormat.AAF: FormatCapability(
                supports_video=True,
                supports_audio=True,
                supports_text=False,  # Limited
                supports_transitions=True,
                supports_effects=True,
                supports_metadata=True,
                supports_markers=True,
            ),
        }
        
        return capabilities.get(format_type, FormatCapability())
    
    def get_name(self) -> str:
        """Get the name of this format adapter."""
        return "OpenTimelineIO Formatter"
    
    def get_version(self) -> str:
        """Get version information for this adapter."""
        if OTIO_AVAILABLE:
            return f"OpenTimelineIO {otio.__version__}"
        return "OpenTimelineIO not available"
    
    def _convert_from_otio(self, otio_timeline: 'otio.schema.Timeline', options: ImportOptions) -> Timeline:
        """Convert an OTIO timeline to an aive Timeline."""
        # Create aive Timeline
        timeline = Timeline(
            width=1920,  # Default, may be overridden by metadata
            height=1080,
            framerate=24.0,  # Default, may be overridden
            name=otio_timeline.name or "Imported Timeline"
        )
        
        # Extract metadata
        if otio_timeline.metadata:
            metadata = otio_timeline.metadata
            if 'width' in metadata:
                timeline.width = int(metadata['width'])
            if 'height' in metadata:
                timeline.height = int(metadata['height'])
            if 'frame_rate' in metadata:
                timeline.framerate = float(metadata['frame_rate'])
        
        # Convert tracks
        for otio_track in otio_timeline.tracks:
            aive_track = self._convert_track_from_otio(otio_track, options)
            timeline.add_track(aive_track)
        
        return timeline
    
    def _convert_to_otio(self, timeline: Timeline, options: ExportOptions) -> 'otio.schema.Timeline':
        """Convert an aive Timeline to an OTIO timeline."""
        # Create OTIO timeline
        otio_timeline = otio.schema.Timeline(
            name=timeline.name or "Exported Timeline"
        )
        
        # Set metadata
        otio_timeline.metadata = {
            'width': timeline.width,
            'height': timeline.height,
            'frame_rate': timeline.framerate,
            'background_color': timeline.background_color,
            'audio_sample_rate': timeline.audio_sample_rate,
            'audio_channels': timeline.audio_channels,
        }
        
        # Convert tracks
        for aive_track in timeline.tracks:
            if not aive_track.enabled and not options.include_disabled_tracks:
                continue
            
            otio_track = self._convert_track_to_otio(aive_track, options)
            otio_timeline.tracks.append(otio_track)
        
        return otio_timeline
    
    def _convert_track_from_otio(self, otio_track: 'otio.schema.Track', options: ImportOptions) -> Track:
        """Convert an OTIO track to an aive Track."""
        # Determine track type
        if otio_track.kind == otio.schema.TrackKind.Video:
            track_type = TrackType.VIDEO
        elif otio_track.kind == otio.schema.TrackKind.Audio:
            track_type = TrackType.AUDIO
        else:
            track_type = TrackType.COMPOSITE
        
        # Create aive Track
        track = Track(
            track_type=track_type,
            name=otio_track.name,
            enabled=otio_track.enabled if hasattr(otio_track, 'enabled') else True
        )
        
        # Convert clips
        for otio_item in otio_track:
            if isinstance(otio_item, otio.schema.Clip):
                aive_clip = self._convert_clip_from_otio(otio_item, options)
                if aive_clip:
                    track.add_clip(aive_clip)
            elif isinstance(otio_item, otio.schema.Transition):
                # Handle transitions
                transition = self._convert_transition_from_otio(otio_item)
                if transition:
                    # Add transition to the last clip
                    clip_index = len(track.clips) - 1
                    if clip_index >= 0:
                        track.add_transition(clip_index, transition)
        
        return track
    
    def _convert_track_to_otio(self, track: Track, options: ExportOptions) -> 'otio.schema.Track':
        """Convert an aive Track to an OTIO track."""
        # Determine OTIO track kind
        if track.track_type == TrackType.VIDEO:
            kind = otio.schema.TrackKind.Video
        elif track.track_type == TrackType.AUDIO:
            kind = otio.schema.TrackKind.Audio
        else:
            kind = otio.schema.TrackKind.Video  # Default
        
        # Create OTIO track
        otio_track = otio.schema.Track(
            name=track.name,
            kind=kind
        )
        
        # Convert clips
        for i, clip in enumerate(track.clips):
            otio_clip = self._convert_clip_to_otio(clip, options)
            if otio_clip:
                otio_track.append(otio_clip)
                
                # Add transition if exists
                transition = track.get_transition(i)
                if transition:
                    otio_transition = self._convert_transition_to_otio(transition)
                    if otio_transition:
                        otio_track.append(otio_transition)
        
        return otio_track
    
    def _convert_clip_from_otio(self, otio_clip: 'otio.schema.Clip', options: ImportOptions):
        """Convert an OTIO clip to an aive clip."""
        try:
            # Get media reference
            media_ref = otio_clip.media_reference
            if not media_ref:
                return None
            
            # Get timing information
            source_range = otio_clip.source_range
            if source_range:
                start_time = source_range.start_time.to_seconds()
                duration = source_range.duration.to_seconds()
            else:
                start_time = 0.0
                duration = None
            
            # Handle different media reference types
            if isinstance(media_ref, otio.schema.ExternalReference):
                source_path = media_ref.target_url
                
                # Determine clip type based on file extension or metadata
                if source_path:
                    path = Path(source_path)
                    ext = path.suffix.lower()
                    
                    if ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
                        return VideoClip(
                            source_path=source_path,
                            start_time=start_time,
                            duration=duration,
                            name=otio_clip.name
                        )
                    elif ext in ['.wav', '.mp3', '.m4a', '.aac']:
                        return AudioClip(
                            source_path=source_path,
                            start_time=start_time,
                            duration=duration,
                            name=otio_clip.name
                        )
                    elif ext in ['.jpg', '.jpeg', '.png', '.tiff']:
                        return ImageClip(
                            source_path=source_path,
                            duration=duration or 5.0,  # Default duration for images
                            start_time=start_time,
                            name=otio_clip.name
                        )
            
            elif isinstance(media_ref, otio.schema.GeneratorReference):
                # Handle generated content (like color clips, text, etc.)
                generator_kind = media_ref.generator_kind
                
                if generator_kind == "SolidColor":
                    # Create a simple image clip as placeholder
                    return ImageClip(
                        source_path="",  # Placeholder
                        duration=duration or 5.0,
                        start_time=start_time,
                        name=otio_clip.name
                    )
        
        except Exception as e:
            print(f"Warning: Failed to convert OTIO clip {otio_clip.name}: {e}")
            return None
        
        return None
    
    def _convert_clip_to_otio(self, clip, options: ExportOptions) -> Optional['otio.schema.Clip']:
        """Convert an aive clip to an OTIO clip."""
        try:
            # Create media reference
            if hasattr(clip, 'source_path') and clip.source_path:
                source_path = str(clip.source_path)
                
                # Adjust paths if requested
                if options.make_paths_relative and options.relative_to:
                    try:
                        rel_path = Path(source_path).relative_to(options.relative_to)
                        source_path = str(rel_path)
                    except ValueError:
                        pass  # Keep absolute path if relative conversion fails
                
                media_ref = otio.schema.ExternalReference(target_url=source_path)
            else:
                # Create generator reference for clips without source files (like text)
                media_ref = otio.schema.GeneratorReference(
                    generator_kind="SolidColor",
                    parameters={"color": "black"}
                )
            
            # Create time range
            if clip.duration is not None:
                source_range = otio.opentime.TimeRange(
                    start_time=otio.opentime.RationalTime(clip.start_time, 24),
                    duration=otio.opentime.RationalTime(clip.duration, 24)
                )
            else:
                source_range = None
            
            # Create OTIO clip
            otio_clip = otio.schema.Clip(
                name=clip.name or f"{clip.get_type()}_clip",
                media_reference=media_ref,
                source_range=source_range
            )
            
            # Add metadata for clip-specific properties
            metadata = {}
            
            if hasattr(clip, 'scale') and clip.scale != 1.0:
                metadata['scale'] = clip.scale
            
            if hasattr(clip, 'position'):
                metadata['position'] = {'x': clip.position.x, 'y': clip.position.y}
            
            if hasattr(clip, 'opacity') and clip.opacity != 1.0:
                metadata['opacity'] = clip.opacity
            
            if isinstance(clip, TextClip):
                metadata['text'] = clip.text
                metadata['font_size'] = clip.font_size
                metadata['font_family'] = clip.font_family
                metadata['color'] = {
                    'r': clip.color.r,
                    'g': clip.color.g,
                    'b': clip.color.b,
                    'a': clip.color.a
                }
            
            if metadata:
                otio_clip.metadata = metadata
            
            return otio_clip
            
        except Exception as e:
            print(f"Warning: Failed to convert clip to OTIO: {e}")
            return None
    
    def _convert_transition_from_otio(self, otio_transition: 'otio.schema.Transition') -> Optional[Transition]:
        """Convert an OTIO transition to an aive transition."""
        # This is a simplified implementation
        # OTIO transitions are complex and may need more detailed conversion
        try:
            duration = otio_transition.in_offset.to_seconds() + otio_transition.out_offset.to_seconds()
            
            from ..core.transitions import CrossfadeTransition
            return CrossfadeTransition(duration=duration, name=otio_transition.name)
            
        except Exception as e:
            print(f"Warning: Failed to convert OTIO transition: {e}")
            return None
    
    def _convert_transition_to_otio(self, transition: Transition) -> Optional['otio.schema.Transition']:
        """Convert an aive transition to an OTIO transition."""
        try:
            # Create OTIO transition
            otio_transition = otio.schema.Transition(
                name=transition.name,
                transition_type=transition.get_type().value,
                in_offset=otio.opentime.RationalTime(transition.duration / 2, 24),
                out_offset=otio.opentime.RationalTime(transition.duration / 2, 24)
            )
            
            # Add transition-specific metadata
            otio_transition.metadata = transition.get_parameters()
            
            return otio_transition
            
        except Exception as e:
            print(f"Warning: Failed to convert transition to OTIO: {e}")
            return None
    
    @staticmethod
    def is_available() -> bool:
        """Check if OTIO formatter is available."""
        return OTIO_AVAILABLE
