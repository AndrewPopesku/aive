# Aive - Modern Video Automation Library

**Aive** is a modern, developer-first Python library designed to automate and scale video creation. It provides a high-level, object-oriented interface for defining and manipulating video timelines, abstracting the complexities of underlying editing and format-conversion tools.

## 🌟 Features

- **🎬 Intuitive Timeline API**: Create complex video compositions with simple Python objects
- **🔧 Hexagonal Architecture**: Pluggable adapters for different video tools and services
- **📱 Professional Format Support**: Import/export Final Cut Pro XML, AAF, EDL via OpenTimelineIO
- **🎨 Template System**: Create reusable video templates with dynamic placeholders
- **⚡ Batch Processing**: Render multiple videos in parallel with job queues
- **🗣️ AI Subtitles**: Automatic subtitle generation using Groq Whisper API
- **🎯 Type Safe**: Full type hints and modern Python features

## 🚀 Quick Start

### Installation

```bash
# Basic installation
pip install aive

# Install with all adapters
pip install "aive[all]"

# Install specific adapters
pip install "aive[moviepy]"    # For video rendering
pip install "aive[otio]"       # For professional formats
pip install "aive[whisper]"    # For AI transcription
```

### Simple Video Creation

```python
import aive

# Create a timeline
timeline = aive.Timeline(width=1920, height=1080, framerate=30)

# Add a video track
track = timeline.add_track()

# Add clips
video_clip = aive.VideoClip("input.mp4", start_time=0, duration=10)
text_clip = aive.TextClip("Hello World!", duration=3, start_time=2)

track.add_clip(video_clip)
track.add_clip(text_clip)

# Render the video
aive.quick_render(timeline, "output.mp4", quality="high")
```

### Using the High-Level API

```python
from aive import VideoAutomator

# Initialize with automatic adapter detection
automator = VideoAutomator()

# Create timeline
timeline = automator.create_timeline(name="My Project")

# Add content and render
automator.render_video(timeline, "final_video.mp4", quality="web")
```

## 📖 Core Concepts

### Timeline and Tracks

A **Timeline** is the main container that holds multiple **Tracks**. Each track contains **Clips** arranged chronologically:

```python
timeline = aive.Timeline(width=1920, height=1080, framerate=30)

# Add different types of tracks
video_track = timeline.add_track(track_type=aive.TrackType.VIDEO)
audio_track = timeline.add_track(track_type=aive.TrackType.AUDIO)
text_track = timeline.add_track(track_type=aive.TrackType.TEXT)
```

### Clips

Four types of clips are supported:

```python
# Video from file
video = aive.VideoClip("video.mp4", start_time=0, duration=5)

# Audio from file  
audio = aive.AudioClip("music.wav", start_time=2, duration=8, volume=0.5)

# Image with duration
image = aive.ImageClip("logo.png", duration=3, start_time=1)

# Text overlay
text = aive.TextClip(
    "Welcome!", 
    duration=2, 
    font_size=48, 
    color=aive.Color(255, 255, 255)
)
```

### Transitions

Add smooth transitions between clips:

```python
from aive import CrossfadeTransition, WipeTransition

# Add crossfade between clips
crossfade = CrossfadeTransition(duration=1.0, curve="ease_in_out")
track.add_transition(clip_index=0, transition=crossfade)

# Wipe transition
wipe = WipeTransition(duration=0.5, direction=aive.WipeDirection.LEFT_TO_RIGHT)
track.add_transition(clip_index=1, transition=wipe)
```

## 🎯 Advanced Features

### Video Templates

Create reusable templates with dynamic content:

```python
from aive.templates import VideoTemplate, PlaceholderText, PlaceholderVideo

# Create base timeline
template_timeline = aive.Timeline()
track = template_timeline.add_track()

# Create template with placeholders
template = VideoTemplate(template_timeline, info=TemplateInfo(
    name="News Template",
    description="Template for news videos"
))

# Add placeholders
title_placeholder = PlaceholderText(
    key="title",
    duration=3.0,
    font_size=48,
    position=Position(100, 100)
)

video_placeholder = PlaceholderVideo(
    key="main_video", 
    start_time=2.0,
    duration=15.0
)

template.add_placeholder(title_placeholder, track_index=0)
template.add_placeholder(video_placeholder, track_index=0)

# Fill template with data
data = {
    "title": "Breaking News",
    "main_video": "news_footage.mp4"
}

final_timeline = template.fill(data)
```

### Batch Processing

Process multiple videos efficiently:

```python
from aive.pipeline import RenderQueue, QueueMode

# Create render queue
queue = RenderQueue()

# Add multiple jobs
for i in range(10):
    timeline = create_video_timeline(f"input_{i}.mp4")
    queue.add_job(timeline, f"output_{i}.mp4")

# Process in parallel
queue.run(mode=QueueMode.PARALLEL_THREAD, workers=4)

# Monitor progress
stats = queue.get_stats()
print(f"Completed: {stats['completed']}/{stats['total_jobs']}")
```

### AI-Powered Subtitles

Automatically generate subtitles using AI:

```python
import os
from aive import VideoAutomator
from aive.ports.transcription_service import TranscriptionOptions

# Set up Groq API key
os.environ['GROQ_API_KEY'] = 'your-api-key'

automator = VideoAutomator()

# Create timeline with audio
timeline = aive.Timeline()
audio_track = timeline.add_track(track_type=aive.TrackType.AUDIO)
audio_clip = aive.AudioClip("speech.wav", duration=60)
audio_track.add_clip(audio_clip)

# Generate subtitles
options = TranscriptionOptions(
    language=aive.TranscriptionLanguage.ENGLISH,
    max_segment_length=10.0
)

timeline_with_subs = automator.generate_subtitles(
    timeline, 
    audio_track_index=0, 
    options=options
)

# Render with burned-in subtitles
automator.render_video(timeline_with_subs, "video_with_subs.mp4")
```

### Professional Format Integration

Work with industry-standard formats:

```python
from aive.adapters import OTIOFormatter

formatter = OTIOFormatter()

# Import from Final Cut Pro
timeline = formatter.read("project.fcpxml")

# Modify the timeline
text_clip = aive.TextClip("Added by Aive", duration=5)
timeline.get_track(0).add_clip(text_clip)

# Export back to FCPXML
formatter.write(timeline, "modified_project.fcpxml")

# Also supports AAF, EDL, etc.
formatter.write(timeline, "project.aaf")
```

## 🔧 Architecture

Aive follows a **Hexagonal Architecture** (Ports and Adapters) pattern:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Application   │    │   Core Domain    │    │    Adapters     │
│                 │◄──►│                  │◄──►│                 │
│ • VideoAutomator│    │ • Timeline       │    │ • MoviePyRenderer│
│ • Quick functions│    │ • Track/Clips    │    │ • OTIOFormatter │
│ • Templates     │    │ • Transitions    │    │ • GroqWhisper   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

This design allows you to:
- **Swap implementations**: Use different rendering engines
- **Extend functionality**: Add new format support
- **Test easily**: Mock adapters for unit tests

## 📦 Available Adapters

| Adapter | Purpose | Install Command | Status |
|---------|---------|-----------------|--------|
| MoviePyRenderer | Video rendering with MoviePy | `pip install "aive[moviepy]"` | ✅ Ready |
| OTIOFormatter | Professional format I/O | `pip install "aive[otio]"` | ✅ Ready |
| GroqWhisperTranscriber | AI transcription | `pip install "aive[whisper]"` | ✅ Ready |

## 💡 Examples

### Simple News Video

```python
import aive

# Create news video template
def create_news_video(headline, footage_path, output_path):
    timeline = aive.Timeline(name="News Video")
    
    # Add tracks
    video_track = timeline.add_track()
    text_track = timeline.add_track()
    
    # Main footage
    footage = aive.VideoClip(footage_path, duration=20)
    video_track.add_clip(footage)
    
    # Headline
    title = aive.TextClip(
        headline, 
        duration=5,
        start_time=1,
        font_size=48,
        position=aive.Position(100, 100),
        color=aive.Color(255, 255, 255)
    )
    text_track.add_clip(title)
    
    # Lower third
    lower_third = aive.TextClip(
        "Breaking News",
        duration=15,
        start_time=5,
        font_size=24,
        position=aive.Position(100, 800)
    )
    text_track.add_clip(lower_third)
    
    # Render
    aive.quick_render(timeline, output_path, quality="high")

# Use it
create_news_video(
    "Major Technology Breakthrough", 
    "tech_footage.mp4", 
    "news_report.mp4"
)
```

### Social Media Content Pipeline

```python
from aive import VideoAutomator, RenderQueue, QueueMode
from aive.templates import VideoTemplate

def create_social_media_pipeline():
    automator = VideoAutomator()
    
    # Create different format versions
    formats = [
        {"name": "YouTube", "size": (1920, 1080), "duration": 60},
        {"name": "Instagram", "size": (1080, 1080), "duration": 30},
        {"name": "TikTok", "size": (1080, 1920), "duration": 15}
    ]
    
    source_video = "content.mp4"
    
    # Create jobs for each format
    jobs = []
    for fmt in formats:
        timeline = aive.Timeline(
            width=fmt["size"][0], 
            height=fmt["size"][1]
        )
        
        # Add content (simplified)
        track = timeline.add_track()
        clip = aive.VideoClip(
            source_video, 
            duration=fmt["duration"]
        )
        track.add_clip(clip)
        
        jobs.append({
            "timeline": timeline,
            "output_path": f"output_{fmt['name'].lower()}.mp4"
        })
    
    # Batch render
    automator.batch_render(jobs, mode=QueueMode.PARALLEL_THREAD)

create_social_media_pipeline()
```

## 🧪 Testing

Run the test suite:

```bash
# Install dev dependencies
pip install "aive[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=aive --cov-report=html
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/andriipopesku/aive.git
cd aive

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev,all]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **MoviePy**: For video processing capabilities
- **OpenTimelineIO**: For professional format interchange
- **Groq**: For fast AI transcription services

**Made with ❤️ for video automation**
