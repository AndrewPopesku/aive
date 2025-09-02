#!/usr/bin/env python3
"""
Working Video Example - Aive Video Automation Library

This example creates a simple working video with centered text that should display properly.
"""

import aive
from pathlib import Path

def main():
    print("🎬 Creating Working Video with Centered Text")
    print("=" * 50)
    
    # Create a timeline with standard HD resolution
    timeline = aive.Timeline.create_standard_hd("Working Video")
    
    # Add a text track
    text_track = timeline.add_track(track_type=aive.TrackType.TEXT)
    text_track.name = "Centered Text"
    
    # Create simple centered text clips
    clip1 = aive.TextClip(
        text="Hello World!",
        duration=3.0,
        start_time=0.0,
        font_size=48,
        font_family="Arial",
        color=aive.Color(255, 255, 255),  # White
        position=aive.Position(x=960, y=540),  # Center
        name="Hello"
    )
    text_track.add_clip(clip1)
    
    clip2 = aive.TextClip(
        text="This is Aive!",
        duration=3.0,
        start_time=4.0,
        font_size=48,
        color=aive.Color(255, 0, 0),  # Red
        position=aive.Position(x=960, y=540),  # Center
        name="Aive"
    )
    text_track.add_clip(clip2)
    
    clip3 = aive.TextClip(
        text="Video Created!",
        duration=2.0,
        start_time=8.0,
        font_size=48,
        color=aive.Color(0, 255, 0),  # Green
        position=aive.Position(x=960, y=540),  # Center
        name="Created"
    )
    text_track.add_clip(clip3)
    
    print(f"Created timeline with {len(text_track.clips)} clips")
    print(f"Total duration: {timeline.duration:.1f} seconds")
    
    # Render the video
    try:
        automator = aive.VideoAutomator()
        
        if not automator.renderer:
            print("❌ No renderer available")
            return
        
        output_path = Path("working_video.mp4")
        print(f"\n🎥 Rendering to: {output_path.absolute()}")
        
        automator.render_video(timeline, output_path, quality="medium")
        
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024  # KB
            print(f"\n✅ Video rendered successfully!")
            print(f"📁 File: {output_path}")
            print(f"📊 Size: {file_size:.1f} KB")
            print(f"🎬 Duration: {timeline.duration:.1f} seconds")
        else:
            print(f"\n❌ Video file not found")
            
    except Exception as e:
        print(f"\n❌ Rendering failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
