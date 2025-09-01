"""
Application layer that orchestrates Core Domain with configured Adapters.

This module provides high-level APIs that combine the core domain with
specific adapters, making it easy for users to accomplish common video
automation tasks.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from .core.timeline import Timeline
from .core.clips import TextClip, AudioClip
from .core.track import TrackType
from .ports.renderer import Renderer, RenderOptions
from .ports.timeline_format import TimelineFormat, ImportOptions, ExportOptions
from .ports.transcription_service import TranscriptionService, TranscriptionOptions
from .pipeline.render_queue import RenderQueue, QueueMode
from .templates.placeholder import VideoTemplate, TemplateLibrary


class VideoAutomator:
    """
    High-level interface for video automation tasks.
    
    This class provides a simple, batteries-included API for common video
    automation workflows, with sensible defaults and automatic adapter selection.
    """
    
    def __init__(
        self,
        renderer: Optional[Renderer] = None,
        timeline_formatter: Optional[TimelineFormat] = None,
        transcription_service: Optional[TranscriptionService] = None,
    ):
        """
        Initialize the video automator.
        
        Args:
            renderer: Video renderer to use (auto-detects if None)
            timeline_formatter: Timeline format handler (auto-detects if None)
            transcription_service: Transcription service (auto-detects if None)
        """
        self.renderer = renderer or self._auto_detect_renderer()
        self.timeline_formatter = timeline_formatter or self._auto_detect_formatter()
        self.transcription_service = transcription_service or self._auto_detect_transcriber()
        
        # Initialize render queue with default renderer
        self.render_queue = RenderQueue(default_renderer=self.renderer)
        
        # Initialize template library
        self.template_library = TemplateLibrary()
    
    def create_timeline(
        self, 
        width: int = 1920, 
        height: int = 1080, 
        framerate: float = 30.0,
        name: Optional[str] = None
    ) -> Timeline:
        """
        Create a new timeline with specified parameters.
        
        Args:
            width: Video width in pixels
            height: Video height in pixels
            framerate: Video framerate
            name: Optional name for the timeline
            
        Returns:
            New Timeline instance
        """
        return Timeline(width=width, height=height, framerate=framerate, name=name)
    
    def render_video(
        self,
        timeline: Timeline,
        output_path: Union[str, Path],
        options: Optional[RenderOptions] = None,
        quality: str = "medium"
    ) -> None:
        """
        Render a timeline to a video file.
        
        Args:
            timeline: Timeline to render
            output_path: Path where video should be saved
            options: Custom render options (overrides quality preset)
            quality: Quality preset ("low", "medium", "high", "web")
        """
        if not self.renderer:
            raise RuntimeError("No renderer available. Install moviepy: pip install aive[moviepy]")
        
        if options is None:
            options = self._get_quality_preset(quality)
        
        self.renderer.render(timeline, Path(output_path), options)
    
    def batch_render(
        self,
        jobs: List[Dict[str, Any]],
        mode: QueueMode = QueueMode.SEQUENTIAL,
        workers: Optional[int] = None
    ) -> None:
        """
        Render multiple videos in batch.
        
        Args:
            jobs: List of job dictionaries with 'timeline', 'output_path', and optional 'options'
            mode: Processing mode (sequential or parallel)
            workers: Number of workers for parallel processing
        """
        # Clear any existing jobs
        self.render_queue.clear_completed()
        
        # Add jobs to queue
        for job in jobs:
            self.render_queue.add_job(
                timeline=job['timeline'],
                output_path=job['output_path'],
                options=job.get('options')
            )
        
        # Process the queue
        self.render_queue.run(mode=mode, workers=workers)
    
    def generate_subtitles(
        self,
        timeline: Timeline,
        audio_track_index: int = 0,
        options: Optional[TranscriptionOptions] = None,
        text_track_index: Optional[int] = None
    ) -> Timeline:
        """
        Generate subtitles for a timeline using AI transcription.
        
        Args:
            timeline: Timeline to add subtitles to
            audio_track_index: Index of audio track to transcribe
            options: Transcription options
            text_track_index: Index of track to add text clips to (creates new if None)
            
        Returns:
            Timeline with added subtitle clips
        """
        if not self.transcription_service:
            raise RuntimeError(
                "No transcription service available. "
                "Install groq: pip install aive[whisper] and set GROQ_API_KEY"
            )
        
        # Extract audio track
        if audio_track_index >= len(timeline.tracks):
            raise IndexError(f"Audio track index {audio_track_index} out of range")
        
        audio_track = timeline.get_track(audio_track_index)
        if not audio_track:
            raise ValueError("Audio track not found")
        
        # Find audio clips in the track
        audio_clips = [clip for clip in audio_track.clips if isinstance(clip, AudioClip)]
        if not audio_clips:
            raise ValueError("No audio clips found in specified track")
        
        # For simplicity, process the first audio clip
        # In a full implementation, you'd handle multiple clips and merging
        audio_clip = audio_clips[0]
        
        if options is None:
            options = TranscriptionOptions()
        
        # Transcribe the audio
        result = self.transcription_service.transcribe(audio_clip.source_path, options)
        
        # Create text track if needed
        if text_track_index is None:
            text_track = timeline.add_track(track_type=TrackType.TEXT)
            text_track.name = "Generated Subtitles"
        else:
            text_track = timeline.get_track(text_track_index)
            if not text_track:
                raise IndexError(f"Text track index {text_track_index} out of range")
        
        # Add subtitle clips
        for segment in result.segments:
            text_clip = TextClip(
                text=segment.text,
                duration=segment.duration,
                start_time=segment.start_time + audio_clip.start_time,
                font_size=24,
                name=f"subtitle_{len(text_track.clips)}"
            )
            text_track.add_clip(text_clip)
        
        return timeline
    
    def load_timeline(
        self,
        file_path: Union[str, Path],
        options: Optional[ImportOptions] = None
    ) -> Timeline:
        """
        Load a timeline from a professional video editing format.
        
        Args:
            file_path: Path to the timeline file
            options: Import options
            
        Returns:
            Loaded Timeline instance
        """
        if not self.timeline_formatter:
            raise RuntimeError(
                "No timeline formatter available. "
                "Install opentimelineio: pip install aive[otio]"
            )
        
        return self.timeline_formatter.read(Path(file_path), options)
    
    def save_timeline(
        self,
        timeline: Timeline,
        file_path: Union[str, Path],
        options: Optional[ExportOptions] = None
    ) -> None:
        """
        Save a timeline to a professional video editing format.
        
        Args:
            timeline: Timeline to save
            file_path: Path where timeline should be saved
            options: Export options
        """
        if not self.timeline_formatter:
            raise RuntimeError(
                "No timeline formatter available. "
                "Install opentimelineio: pip install aive[otio]"
            )
        
        self.timeline_formatter.write(timeline, Path(file_path), options)
    
    def create_template_from_timeline(
        self,
        timeline: Timeline,
        name: str,
        description: str = ""
    ) -> VideoTemplate:
        """
        Create a video template from a timeline.
        
        Args:
            timeline: Timeline to use as template base
            name: Template name
            description: Template description
            
        Returns:
            VideoTemplate instance
        """
        from .templates.placeholder import TemplateInfo
        
        info = TemplateInfo(
            name=name,
            description=description,
            resolution=(timeline.width, timeline.height),
            duration=timeline.duration
        )
        
        template = VideoTemplate(timeline=timeline, info=info)
        
        # Add to library
        self.template_library.add_template(template, "user_created")
        
        return template
    
    def render_template(
        self,
        template: VideoTemplate,
        data: Dict[str, Any],
        output_path: Union[str, Path],
        options: Optional[RenderOptions] = None
    ) -> None:
        """
        Fill a template with data and render it.
        
        Args:
            template: Video template to use
            data: Data to fill template placeholders
            output_path: Path where video should be saved
            options: Render options
        """
        # Fill template to create timeline
        timeline = template.fill(data)
        
        # Render the timeline
        self.render_video(timeline, output_path, options)
    
    def get_available_adapters(self) -> Dict[str, bool]:
        """
        Get information about available adapters.
        
        Returns:
            Dictionary showing which adapters are available
        """
        adapters = {}
        
        # Check MoviePy renderer
        try:
            from .adapters.moviepy_renderer import MoviePyRenderer
            adapters['moviepy_renderer'] = MoviePyRenderer.is_available()
        except ImportError:
            adapters['moviepy_renderer'] = False
        
        # Check OTIO formatter
        try:
            from .adapters.otio_formatter import OTIOFormatter
            adapters['otio_formatter'] = OTIOFormatter.is_available()
        except ImportError:
            adapters['otio_formatter'] = False
        
        # Check Groq transcriber
        try:
            from .adapters.groq_whisper_transcriber import GroqWhisperTranscriber
            adapters['groq_transcriber'] = GroqWhisperTranscriber.is_available_static()
        except ImportError:
            adapters['groq_transcriber'] = False
        
        return adapters
    
    def _auto_detect_renderer(self) -> Optional[Renderer]:
        """Auto-detect and return available renderer."""
        try:
            from .adapters.moviepy_renderer import MoviePyRenderer
            if MoviePyRenderer.is_available():
                return MoviePyRenderer()
        except ImportError:
            pass
        return None
    
    def _auto_detect_formatter(self) -> Optional[TimelineFormat]:
        """Auto-detect and return available timeline formatter."""
        try:
            from .adapters.otio_formatter import OTIOFormatter
            if OTIOFormatter.is_available():
                return OTIOFormatter()
        except ImportError:
            pass
        return None
    
    def _auto_detect_transcriber(self) -> Optional[TranscriptionService]:
        """Auto-detect and return available transcription service."""
        try:
            from .adapters.groq_whisper_transcriber import GroqWhisperTranscriber
            if GroqWhisperTranscriber.is_available_static():
                return GroqWhisperTranscriber()
        except (ImportError, ValueError):
            pass
        return None
    
    def _get_quality_preset(self, quality: str) -> RenderOptions:
        """Get render options for quality preset."""
        presets = {
            "low": RenderOptions.fast_preview(),
            "medium": RenderOptions.web_optimized(),
            "high": RenderOptions.high_quality(),
            "web": RenderOptions.web_optimized(),
        }
        
        return presets.get(quality, RenderOptions.web_optimized())


# Convenience functions for common use cases

def quick_render(
    timeline: Timeline,
    output_path: Union[str, Path],
    quality: str = "medium"
) -> None:
    """
    Quick render function for simple use cases.
    
    Args:
        timeline: Timeline to render
        output_path: Output file path
        quality: Quality preset
    """
    automator = VideoAutomator()
    automator.render_video(timeline, output_path, quality=quality)


def create_simple_video(
    clips: List[Dict[str, Any]],
    output_path: Union[str, Path],
    resolution: tuple = (1920, 1080),
    framerate: float = 30.0
) -> None:
    """
    Create a simple video from a list of clip configurations.
    
    Args:
        clips: List of clip dictionaries with type, path, and timing info
        output_path: Output file path
        resolution: Video resolution (width, height)
        framerate: Video framerate
    """
    from .core.clips import VideoClip, AudioClip, ImageClip, TextClip
    
    # Create timeline
    timeline = Timeline(width=resolution[0], height=resolution[1], framerate=framerate)
    track = timeline.add_track()
    
    # Add clips
    current_time = 0.0
    for clip_config in clips:
        clip_type = clip_config['type']
        duration = clip_config.get('duration', 5.0)
        
        if clip_type == 'video':
            clip = VideoClip(
                source_path=clip_config['path'],
                start_time=current_time,
                duration=duration
            )
        elif clip_type == 'audio':
            clip = AudioClip(
                source_path=clip_config['path'],
                start_time=current_time,
                duration=duration
            )
        elif clip_type == 'image':
            clip = ImageClip(
                source_path=clip_config['path'],
                duration=duration,
                start_time=current_time
            )
        elif clip_type == 'text':
            clip = TextClip(
                text=clip_config['text'],
                duration=duration,
                start_time=current_time,
                font_size=clip_config.get('font_size', 48)
            )
        else:
            continue
        
        track.add_clip(clip)
        current_time += duration
    
    # Render
    quick_render(timeline, output_path)


def auto_subtitle_video(
    video_path: Union[str, Path],
    output_path: Union[str, Path],
    groq_api_key: Optional[str] = None
) -> None:
    """
    Automatically add subtitles to a video file.
    
    Args:
        video_path: Path to input video file
        output_path: Path for output video with subtitles
        groq_api_key: Groq API key for transcription
    """
    if groq_api_key:
        os.environ['GROQ_API_KEY'] = groq_api_key
    
    # Create timeline from video
    from .core.clips import VideoClip
    timeline = Timeline()
    video_track = timeline.add_track()
    audio_track = timeline.add_track()
    
    # Add video and audio clips
    video_clip = VideoClip(source_path=str(video_path))
    video_track.add_clip(video_clip)
    
    # For subtitle generation, we need the audio extracted
    # This is simplified - in practice you'd extract audio from the video
    automator = VideoAutomator()
    
    # Generate and render with subtitles
    timeline_with_subs = automator.generate_subtitles(timeline, audio_track_index=1)
    automator.render_video(timeline_with_subs, output_path)
