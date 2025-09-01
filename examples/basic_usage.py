#!/usr/bin/env python3
"""
Basic Usage Example - Aive Video Automation Library

This example demonstrates the core functionality of Aive:
- Creating timelines and tracks
- Adding different types of clips
- Applying transitions
- Rendering videos
"""

from pathlib import Path
import aive

def main():
    print("🎬 Aive Basic Usage Example")
    print("=" * 40)
    
    # Create a timeline with standard HD resolution
    timeline = aive.Timeline.create_standard_hd("Basic Example")
    
    print(f"Created timeline: {timeline}")
    
    # Add a video track
    video_track = timeline.add_track(track_type=aive.TrackType.VIDEO)
    video_track.name = "Main Video"
    
    # Add a text track
    text_track = timeline.add_track(track_type=aive.TrackType.TEXT)
    text_track.name = "Titles"
    
    print(f"Added {len(timeline.tracks)} tracks")
    
    # Create some clips (using placeholder paths - replace with real files)
    
    # Opening title
    opening_title = aive.TextClip(
        text="Welcome to Aive!",
        duration=3.0,
        start_time=0.0,
        font_size=64,
        font_family="Arial",
        color=aive.Color(255, 255, 255),  # White
        position=aive.Position(x=960, y=200),  # Centered horizontally
        name="Opening Title"
    ).set_bold(True).set_alignment("center")
    
    text_track.add_clip(opening_title)
    
    # Main content title
    main_title = aive.TextClip(
        text="Creating Amazing Videos with Python",
        duration=5.0,
        start_time=4.0,
        font_size=48,
        color=aive.Color(255, 255, 0),  # Yellow
        position=aive.Position(x=100, y=100),
        name="Main Title"
    )
    
    text_track.add_clip(main_title)
    
    # Subtitle
    subtitle = aive.TextClip(
        text="Powered by Aive Library",
        duration=4.0,
        start_time=5.0,
        font_size=24,
        color=aive.Color(200, 200, 200),  # Light gray
        position=aive.Position(x=100, y=900),
        name="Subtitle"
    )
    
    text_track.add_clip(subtitle)
    
    # Add transitions between text clips
    crossfade = aive.CrossfadeTransition(duration=0.5, curve="ease_in_out")
    text_track.add_transition(clip_index=0, transition=crossfade)
    
    fade_out = aive.FadeTransition(duration=1.0, fade_color=(0, 0, 0))
    text_track.add_transition(clip_index=1, transition=fade_out)
    
    print(f"Added {len(text_track.clips)} text clips with transitions")
    
    # If you have actual media files, you can add them like this:
    """
    # Video clip example
    if Path("sample_video.mp4").exists():
        video_clip = aive.VideoClip(
            source_path="sample_video.mp4",
            start_time=0.0,
            duration=10.0,
            scale=1.0,
            name="Main Video"
        )
        video_track.add_clip(video_clip)
        print("Added video clip")
    
    # Image clip example
    if Path("logo.png").exists():
        logo = aive.ImageClip(
            source_path="logo.png",
            duration=8.0,
            start_time=1.0,
            scale=0.3,
            position=aive.Position(x=1600, y=50),  # Top right corner
            name="Logo"
        )
        video_track.add_clip(logo)
        print("Added logo image")
    """
    
    # Display timeline information
    print(f"\nTimeline Summary:")
    print(f"- Resolution: {timeline.width}x{timeline.height}")
    print(f"- Framerate: {timeline.framerate} fps")
    print(f"- Duration: {timeline.duration:.2f} seconds")
    print(f"- Tracks: {len(timeline.tracks)}")
    
    for i, track in enumerate(timeline.tracks):
        print(f"  Track {i}: {track.name} ({track.track_type.value}) - {len(track.clips)} clips")
    
    # Try to render (will only work if MoviePy is installed)
    try:
        print("\n🎥 Attempting to render...")
        automator = aive.VideoAutomator()
        
        if automator.renderer:
            output_path = "basic_example_output.mp4"
            automator.render_video(timeline, output_path, quality="medium")
            print(f"✅ Successfully rendered to: {output_path}")
        else:
            print("⚠️  No renderer available. Install MoviePy: pip install aive[moviepy]")
    
    except Exception as e:
        print(f"❌ Render failed: {e}")
        print("💡 This is normal if you don't have media files or MoviePy installed")
    
    # Show available adapters
    print("\n🔧 Available Adapters:")
    automator = aive.VideoAutomator()
    adapters = automator.get_available_adapters()
    for name, available in adapters.items():
        status = "✅" if available else "❌"
        print(f"  {status} {name}")
    
    print("\n✨ Example completed!")

if __name__ == "__main__":
    main()
