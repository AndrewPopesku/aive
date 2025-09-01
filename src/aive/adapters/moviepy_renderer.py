"""
MoviePy adapter that implements the Renderer port.
"""
import time
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..core.timeline import Timeline
from ..core.clips import VideoClip, AudioClip, ImageClip, TextClip
from ..core.track import TrackType
from ..ports.renderer import Renderer, RenderOptions, RenderError

try:
    import moviepy.editor as mp
    from moviepy.config import check_config
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    mp = None


class MoviePyRenderer(Renderer):
    """
    MoviePy-based renderer implementing the Renderer port.
    
    This adapter translates aive Timeline objects into MoviePy CompositeVideoClip
    objects and handles the rendering process.
    """
    
    def __init__(self):
        """Initialize the MoviePy renderer."""
        if not MOVIEPY_AVAILABLE:
            raise ImportError(
                "MoviePy is required for MoviePyRenderer. "
                "Install it with: pip install aive[moviepy]"
            )
        
        # Check MoviePy configuration
        self._check_moviepy_setup()
    
    def render(
        self, 
        timeline: Timeline, 
        output_path: Path, 
        options: Optional[RenderOptions] = None
    ) -> None:
        """
        Render a timeline to a video file using MoviePy.
        
        Args:
            timeline: The timeline to render
            output_path: Path where the rendered video should be saved
            options: Optional rendering configuration
            
        Raises:
            RenderError: If rendering fails
            FileNotFoundError: If source files are missing
            PermissionError: If unable to write to output path
        """
        if not self.can_render(timeline):
            raise RenderError("Timeline contains unsupported features for MoviePy renderer")
        
        if options is None:
            options = RenderOptions()
        
        try:
            # Create MoviePy clip from timeline
            composite_clip = self._create_composite_clip(timeline)
            
            # Set up render parameters
            render_params = self._prepare_render_params(options, output_path)
            
            # Perform the rendering
            composite_clip.write_videofile(
                str(output_path),
                **render_params
            )
            
            # Clean up
            composite_clip.close()
            
        except Exception as e:
            raise RenderError(f"MoviePy rendering failed: {str(e)}", {
                'timeline_duration': timeline.duration,
                'output_path': str(output_path),
                'options': options.to_dict() if options else None
            }) from e
    
    def can_render(self, timeline: Timeline) -> bool:
        """
        Check if this renderer can handle the given timeline.
        
        Args:
            timeline: Timeline to check
            
        Returns:
            True if this renderer supports the timeline's features
        """
        if not MOVIEPY_AVAILABLE:
            return False
        
        # Check for unsupported features
        for track in timeline.tracks:
            if not track.enabled:
                continue
            
            for clip in track.clips:
                # Check if source files exist (for file-based clips)
                if hasattr(clip, 'source_path'):
                    if not clip.source_path.exists():
                        return False
                
                # Check for unsupported clip types or features
                if isinstance(clip, TextClip):
                    # MoviePy has some limitations with text clips
                    if clip.font_family not in self._get_available_fonts():
                        # Use fallback font instead of failing
                        pass
        
        return True
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported output formats.
        
        Returns:
            List of file extensions supported by MoviePy
        """
        return ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.ogv', '.3gp']
    
    def estimate_render_time(
        self, 
        timeline: Timeline, 
        options: Optional[RenderOptions] = None
    ) -> float:
        """
        Estimate rendering time in seconds.
        
        This is a rough estimate based on timeline duration and complexity.
        
        Args:
            timeline: Timeline to estimate for
            options: Rendering options
            
        Returns:
            Estimated render time in seconds
        """
        # Base estimate: roughly real-time for simple content
        base_time = timeline.duration
        
        # Adjust for complexity
        complexity_factor = 1.0
        
        # More tracks = more complexity
        track_count = len([t for t in timeline.tracks if t.enabled])
        complexity_factor += (track_count - 1) * 0.2
        
        # Count clips for additional complexity
        total_clips = sum(len(t.clips) for t in timeline.tracks if t.enabled)
        complexity_factor += total_clips * 0.1
        
        # Adjust for quality settings
        if options:
            if options.quality == "high":
                complexity_factor *= 2.0
            elif options.quality == "low":
                complexity_factor *= 0.5
            
            if options.preset in ["slow", "veryslow"]:
                complexity_factor *= 1.5
            elif options.preset in ["fast", "veryfast"]:
                complexity_factor *= 0.7
        
        return base_time * complexity_factor
    
    def get_name(self) -> str:
        """Get the name of this renderer."""
        return "MoviePy Renderer"
    
    def get_version(self) -> str:
        """Get version information for this renderer."""
        if MOVIEPY_AVAILABLE:
            return f"MoviePy {mp.__version__}"
        return "MoviePy not available"
    
    def _create_composite_clip(self, timeline: Timeline) -> 'mp.CompositeVideoClip':
        """Create a MoviePy CompositeVideoClip from a Timeline."""
        video_clips = []
        audio_clips = []
        
        for track in timeline.tracks:
            if not track.enabled:
                continue
            
            track_clips = self._process_track(track, timeline)
            
            # Separate video and audio clips
            for clip in track_clips:
                if hasattr(clip, 'audio') and clip.audio is not None:
                    audio_clips.append(clip.audio)
                
                # All clips can contribute to video (even if just visual)
                video_clips.append(clip)
        
        # Create composite video clip
        if video_clips:
            composite_video = mp.CompositeVideoClip(
                video_clips, 
                size=(timeline.width, timeline.height)
            )
        else:
            # Create a blank video clip if no video content
            composite_video = mp.ColorClip(
                size=(timeline.width, timeline.height),
                color=timeline.background_color,
                duration=timeline.duration
            )
        
        # Add composite audio if we have audio clips
        if audio_clips:
            composite_audio = mp.CompositeAudioClip(audio_clips)
            composite_video = composite_video.set_audio(composite_audio)
        
        # Set duration
        composite_video = composite_video.set_duration(timeline.duration)
        composite_video = composite_video.set_fps(timeline.framerate)
        
        return composite_video
    
    def _process_track(self, track, timeline: Timeline) -> List['mp.VideoClip']:
        """Process a track and return list of MoviePy clips."""
        clips = []
        
        for clip in track.clips:
            moviepy_clip = self._convert_clip(clip)
            if moviepy_clip is not None:
                # Apply track-level properties
                if track.opacity != 1.0:
                    moviepy_clip = moviepy_clip.set_opacity(track.opacity)
                
                clips.append(moviepy_clip)
        
        return clips
    
    def _convert_clip(self, clip) -> Optional['mp.VideoClip']:
        """Convert an aive clip to a MoviePy clip."""
        try:
            if isinstance(clip, VideoClip):
                return self._convert_video_clip(clip)
            elif isinstance(clip, AudioClip):
                return self._convert_audio_clip(clip)
            elif isinstance(clip, ImageClip):
                return self._convert_image_clip(clip)
            elif isinstance(clip, TextClip):
                return self._convert_text_clip(clip)
            else:
                # Unknown clip type
                return None
                
        except Exception as e:
            print(f"Warning: Failed to convert clip {clip.name}: {e}")
            return None
    
    def _convert_video_clip(self, clip: VideoClip) -> 'mp.VideoFileClip':
        """Convert VideoClip to MoviePy VideoFileClip."""
        moviepy_clip = mp.VideoFileClip(str(clip.source_path))
        
        # Apply trimming
        if clip.trim_start > 0 or clip.trim_end is not None:
            end_time = clip.trim_end or moviepy_clip.duration
            moviepy_clip = moviepy_clip.subclip(clip.trim_start, end_time)
        
        # Apply duration if specified
        if clip.duration is not None:
            moviepy_clip = moviepy_clip.set_duration(clip.duration)
        
        # Apply position and timing
        moviepy_clip = moviepy_clip.set_start(clip.start_time)
        moviepy_clip = moviepy_clip.set_position((clip.position.x, clip.position.y))
        
        # Apply transformations
        if clip.scale != 1.0:
            moviepy_clip = moviepy_clip.resize(clip.scale)
        
        if clip.opacity != 1.0:
            moviepy_clip = moviepy_clip.set_opacity(clip.opacity)
        
        if clip.rotation != 0:
            moviepy_clip = moviepy_clip.rotate(clip.rotation)
        
        return moviepy_clip
    
    def _convert_audio_clip(self, clip: AudioClip) -> 'mp.VideoClip':
        """Convert AudioClip to MoviePy AudioFileClip wrapped in a transparent video."""
        # Load audio
        audio_clip = mp.AudioFileClip(str(clip.source_path))
        
        # Apply trimming
        if clip.trim_start > 0 or clip.trim_end is not None:
            end_time = clip.trim_end or audio_clip.duration
            audio_clip = audio_clip.subclip(clip.trim_start, end_time)
        
        # Apply duration if specified
        if clip.duration is not None:
            audio_clip = audio_clip.set_duration(clip.duration)
        
        # Apply audio properties
        if clip.volume != 1.0:
            audio_clip = audio_clip.volumex(clip.volume)
        
        # Apply fade effects
        if clip.fade_in_duration > 0:
            audio_clip = audio_clip.fadein(clip.fade_in_duration)
        
        if clip.fade_out_duration > 0:
            audio_clip = audio_clip.fadeout(clip.fade_out_duration)
        
        if clip.muted:
            audio_clip = audio_clip.volumex(0)
        
        # Create transparent video clip with this audio
        transparent_clip = mp.ColorClip(
            size=(1, 1),  # Minimal size
            color=(0, 0, 0),
            duration=audio_clip.duration
        ).set_opacity(0)
        
        return transparent_clip.set_audio(audio_clip).set_start(clip.start_time)
    
    def _convert_image_clip(self, clip: ImageClip) -> 'mp.ImageClip':
        """Convert ImageClip to MoviePy ImageClip."""
        moviepy_clip = mp.ImageClip(str(clip.source_path))
        
        # Set duration
        moviepy_clip = moviepy_clip.set_duration(clip.duration)
        
        # Apply position and timing
        moviepy_clip = moviepy_clip.set_start(clip.start_time)
        moviepy_clip = moviepy_clip.set_position((clip.position.x, clip.position.y))
        
        # Apply transformations
        if clip.scale != 1.0:
            moviepy_clip = moviepy_clip.resize(clip.scale)
        
        if clip.opacity != 1.0:
            moviepy_clip = moviepy_clip.set_opacity(clip.opacity)
        
        if clip.rotation != 0:
            moviepy_clip = moviepy_clip.rotate(clip.rotation)
        
        return moviepy_clip
    
    def _convert_text_clip(self, clip: TextClip) -> 'mp.TextClip':
        """Convert TextClip to MoviePy TextClip."""
        # Prepare text clip parameters
        text_params = {
            'txt': clip.text,
            'fontsize': clip.font_size,
            'font': clip.font_family,
            'color': clip.color.to_hex(),
        }
        
        # Handle alignment
        if clip.alignment == 'center':
            text_params['method'] = 'caption'
            text_params['align'] = 'center'
        
        moviepy_clip = mp.TextClip(**text_params)
        
        # Set duration
        moviepy_clip = moviepy_clip.set_duration(clip.duration)
        
        # Apply position and timing
        moviepy_clip = moviepy_clip.set_start(clip.start_time)
        moviepy_clip = moviepy_clip.set_position((clip.position.x, clip.position.y))
        
        # Apply opacity
        if clip.opacity != 1.0:
            moviepy_clip = moviepy_clip.set_opacity(clip.opacity)
        
        return moviepy_clip
    
    def _prepare_render_params(self, options: RenderOptions, output_path: Path) -> Dict[str, Any]:
        """Prepare MoviePy render parameters from RenderOptions."""
        params = {}
        
        # Codec settings
        if options.codec:
            params['codec'] = options.codec
        
        # Bitrate settings
        if options.bitrate:
            params['bitrate'] = options.bitrate
        
        # Audio settings
        if options.audio_codec:
            params['audio_codec'] = options.audio_codec
        
        if options.audio_bitrate:
            params['audio_bitrate'] = options.audio_bitrate
        
        # Preset settings
        if options.preset:
            # Map our preset names to ffmpeg presets
            preset_mapping = {
                'fast_preview': 'ultrafast',
                'fast': 'fast',
                'medium': 'medium',
                'slow': 'slow',
                'high_quality': 'slow'
            }
            params['preset'] = preset_mapping.get(options.preset, options.preset)
        
        # Threading
        if options.threads:
            params['threads'] = options.threads
        
        # Verbose output
        params['verbose'] = options.verbose
        
        # Logger
        if options.logger:
            params['logger'] = options.logger
        
        return params
    
    def _get_available_fonts(self) -> List[str]:
        """Get list of available fonts for text rendering."""
        # This is a simplified implementation
        # In practice, you'd query the system for available fonts
        return [
            'Arial', 'Helvetica', 'Times-Roman', 'Courier',
            'DejaVu-Sans', 'DejaVu-Serif', 'DejaVu-Sans-Mono'
        ]
    
    def _check_moviepy_setup(self) -> None:
        """Check MoviePy setup and dependencies."""
        try:
            # This will check for ffmpeg and other dependencies
            check_config()
        except Exception as e:
            print(f"Warning: MoviePy configuration issue: {e}")
            print("Some features may not work correctly.")
    
    @staticmethod
    def is_available() -> bool:
        """Check if MoviePy renderer is available."""
        return MOVIEPY_AVAILABLE
