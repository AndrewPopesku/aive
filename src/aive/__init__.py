"""
aive - A modern, developer-first Python library for automated video creation and editing.

This library provides a high-level, object-oriented interface for defining and 
manipulating video timelines, abstracting the complexities of underlying editing 
and format-conversion tools.
"""

__version__ = "0.1.0"
__author__ = "Andrii Popesku"

# Core domain exports
from .core.timeline import Timeline
from .core.track import Track, TrackType
from .core.clips import VideoClip, AudioClip, ImageClip, TextClip, Color, Position, Size
from .core.transitions import (
    Transition, CrossfadeTransition, WipeTransition, FadeTransition, SlideTransition,
    TransitionType, WipeDirection
)

# Port interfaces
from .ports.renderer import Renderer
from .ports.timeline_format import TimelineFormat
from .ports.transcription_service import TranscriptionService

# Pipeline and templates
from .pipeline.render_queue import RenderQueue, QueueMode
from .templates.placeholder import (
    PlaceholderText, PlaceholderVideo, VideoTemplate, TemplateInfo
)

# Application layer and convenience functions
from .app import VideoAutomator, quick_render, create_simple_video

__all__ = [
    # Core domain
    "Timeline",
    "Track", 
    "TrackType",
    "VideoClip",
    "AudioClip", 
    "ImageClip",
    "TextClip",
    "Color",
    "Position", 
    "Size",
    "Transition",
    "CrossfadeTransition",
    "WipeTransition",
    "FadeTransition",
    "SlideTransition",
    "TransitionType",
    "WipeDirection",
    
    # Ports
    "Renderer",
    "TimelineFormat", 
    "TranscriptionService",
    
    # Pipeline and Templates
    "RenderQueue",
    "QueueMode",
    "PlaceholderText",
    "PlaceholderVideo",
    "VideoTemplate",
    "TemplateInfo",
    
    # Application layer
    "VideoAutomator",
    "quick_render",
    "create_simple_video",
]

# Adapter imports (optional dependencies)
try:
    from .adapters.moviepy_renderer import MoviePyRenderer
    __all__.append("MoviePyRenderer")
except ImportError:
    pass

try:
    from .adapters.otio_formatter import OTIOFormatter
    __all__.append("OTIOFormatter")
except ImportError:
    pass

try:
    from .adapters.groq_whisper_transcriber import GroqWhisperTranscriber
    __all__.append("GroqWhisperTranscriber")
except ImportError:
    pass
