#!/usr/bin/env python3
"""
Simple Video Creation Example - Aive Video Automation Library

This example demonstrates basic video creation without transitions:
- Creating a timeline
- Adding text clips
- Creating a simple video sequence
"""

import aive

def main():
    print("🎬 Simple Video Creation Example")
    print("=" * 40)
    
    # Create a timeline with standard HD resolution
    timeline = aive.Timeline.create_standard_hd("Simple Video")
    
    print(f"Created timeline: {timeline}")
    
    # Add a text track
    text_track = timeline.add_track(track_type=aive.TrackType.TEXT)
    text_track.name = "Text Content"
    
    print(f"Added text track: {text_track.name}")
    
    # Create a sequence of simple text clips without transitions
    
    # Clip 1: Introduction
    intro_clip = aive.TextClip(
        text="Welcome to Simple Video Creation",
        duration=3.0,
        start_time=0.0,
        font_size=48,
        font_family="Arial",
        color=aive.Color(255, 255, 255),  # White
        position=aive.Position(x=960, y=540),  # Center of screen
        name="Introduction"
    )
    text_track.add_clip(intro_clip)
    
    # Clip 2: Main content
    content_clip = aive.TextClip(
        text="This is a simple text-based video",
        duration=4.0,
        start_time=3.5,  # Small gap between clips
        font_size=36,
        color=aive.Color(100, 200, 255),  # Light blue
        position=aive.Position(x=960, y=540),
        name="Main Content"
    )
    text_track.add_clip(content_clip)
    
    # Clip 3: Feature highlight
    feature_clip = aive.TextClip(
        text="Created with Python & Aive Library",
        duration=3.0,
        start_time=8.0,
        font_size=32,
        color=aive.Color(255, 200, 100),  # Orange
        position=aive.Position(x=960, y=540),
        name="Feature Highlight"
    )
    text_track.add_clip(feature_clip)
    
    # Clip 4: Closing
    closing_clip = aive.TextClip(
        text="Thank you for watching!",
        duration=2.5,
        start_time=11.5,
        font_size=40,
        color=aive.Color(100, 255, 100),  # Light green
        position=aive.Position(x=960, y=540),
        name="Closing"
    )
    text_track.add_clip(closing_clip)
    
    print(f"Added {len(text_track.clips)} text clips")
    
    # Display timeline information
    print(f"\nVideo Summary:")
    print(f"- Resolution: {timeline.width}x{timeline.height}")
    print(f"- Framerate: {timeline.framerate} fps")
    print(f"- Total duration: {timeline.duration:.1f} seconds")
    print(f"- Number of clips: {len(text_track.clips)}")
    
    print(f"\nClip Details:")
    for i, clip in enumerate(text_track.clips, 1):
        end_time = clip.start_time + clip.duration
        print(f"  {i}. {clip.name}")
        print(f"     Text: '{clip.text}'")
        print(f"     Time: {clip.start_time:.1f}s - {end_time:.1f}s ({clip.duration:.1f}s)")
        print(f"     Color: RGB({clip.color.r}, {clip.color.g}, {clip.color.b})")
        print()
    
    # Try to create video automator
    try:
        automator = aive.VideoAutomator()
        print(f"🔧 VideoAutomator ready")
        
        if automator.renderer:
            print("✅ Renderer available - could render video")
        else:
            print("❌ No renderer available")
            print("💡 To enable video rendering, install MoviePy:")
            print("   uv add moviepy")
            
    except Exception as e:
        print(f"❌ VideoAutomator error: {e}")
    
    print("\n✨ Simple video creation completed!")
    print("🎯 This creates a 14-second video with 4 text clips and no transitions")

if __name__ == "__main__":
    main()
