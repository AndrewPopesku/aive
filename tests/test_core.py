"""
Tests for core domain functionality.
"""
import pytest
from pathlib import Path

from aive.core.timeline import Timeline
from aive.core.track import Track, TrackType
from aive.core.clips import VideoClip, AudioClip, ImageClip, TextClip, Color, Position
from aive.core.transitions import CrossfadeTransition, WipeTransition, WipeDirection


class TestTimeline:
    """Tests for Timeline class."""
    
    def test_timeline_creation(self):
        """Test basic timeline creation."""
        timeline = Timeline(width=1920, height=1080, framerate=30.0, name="Test")
        
        assert timeline.width == 1920
        assert timeline.height == 1080
        assert timeline.framerate == 30.0
        assert timeline.name == "Test"
        assert len(timeline.tracks) == 0
        assert timeline.duration == 0.0
    
    def test_timeline_presets(self):
        """Test timeline preset creation methods."""
        hd_timeline = Timeline.create_standard_hd("HD Test")
        assert hd_timeline.width == 1920
        assert hd_timeline.height == 1080
        assert hd_timeline.name == "HD Test"
        
        uhd_timeline = Timeline.create_standard_4k("4K Test")
        assert uhd_timeline.width == 3840
        assert uhd_timeline.height == 2160
        
        square_timeline = Timeline.create_square(1080, "Square Test")
        assert square_timeline.width == 1080
        assert square_timeline.height == 1080
        
        vertical_timeline = Timeline.create_vertical("Vertical Test")
        assert vertical_timeline.width == 1080
        assert vertical_timeline.height == 1920
    
    def test_add_tracks(self):
        """Test adding tracks to timeline."""
        timeline = Timeline()
        
        # Add different types of tracks
        video_track = timeline.add_track(track_type=TrackType.VIDEO)
        audio_track = timeline.add_track(track_type=TrackType.AUDIO)
        text_track = timeline.add_track(track_type=TrackType.TEXT)
        
        assert len(timeline.tracks) == 3
        assert video_track.track_type == TrackType.VIDEO
        assert audio_track.track_type == TrackType.AUDIO
        assert text_track.track_type == TrackType.TEXT
    
    def test_timeline_duration_calculation(self):
        """Test that timeline duration is calculated correctly."""
        timeline = Timeline()
        track = timeline.add_track()
        
        # Add clips with different end times
        clip1 = TextClip("Test 1", duration=5.0, start_time=0.0)
        clip2 = TextClip("Test 2", duration=3.0, start_time=7.0)  # Ends at 10.0
        
        track.add_clip(clip1)
        track.add_clip(clip2)
        
        assert timeline.duration == 10.0


class TestTrack:
    """Tests for Track class."""
    
    def test_track_creation(self):
        """Test basic track creation."""
        track = Track(TrackType.VIDEO, "Video Track", enabled=True)
        
        assert track.track_type == TrackType.VIDEO
        assert track.name == "Video Track"
        assert track.enabled is True
        assert len(track.clips) == 0
        assert track.duration == 0.0
    
    def test_add_clips_to_track(self):
        """Test adding clips to a track."""
        track = Track(TrackType.COMPOSITE)
        
        text_clip = TextClip("Hello", duration=5.0)
        track.add_clip(text_clip)
        
        assert len(track.clips) == 1
        assert track.duration == 5.0
    
    def test_track_type_validation(self):
        """Test that track validates clip types."""
        video_track = Track(TrackType.VIDEO)
        audio_track = Track(TrackType.AUDIO)
        text_track = Track(TrackType.TEXT)
        
        # This should work - compatible types
        video_clip = VideoClip("test.mp4", duration=5.0)
        video_track.add_clip(video_clip)
        
        audio_clip = AudioClip("test.wav", duration=5.0)
        audio_track.add_clip(audio_clip)
        
        text_clip = TextClip("Test", duration=5.0)
        text_track.add_clip(text_clip)
        
        # This should fail - incompatible types
        with pytest.raises(ValueError):
            video_track.add_clip(audio_clip)  # Audio clip on video track
        
        with pytest.raises(ValueError):
            audio_track.add_clip(video_clip)  # Video clip on audio track
    
    def test_transitions(self):
        """Test adding transitions between clips."""
        track = Track(TrackType.VIDEO)
        
        # Add two clips
        clip1 = VideoClip("video1.mp4", duration=5.0)
        clip2 = VideoClip("video2.mp4", duration=5.0, start_time=5.0)
        
        track.add_clip(clip1)
        track.add_clip(clip2)
        
        # Add transition between them
        transition = CrossfadeTransition(duration=1.0)
        track.add_transition(0, transition)
        
        assert track.get_transition(0) == transition
    
    def test_find_clips_at_time(self):
        """Test finding clips at specific time."""
        track = Track()
        
        clip1 = TextClip("First", duration=5.0, start_time=0.0)   # 0-5
        clip2 = TextClip("Second", duration=3.0, start_time=4.0)  # 4-7 (overlap)
        clip3 = TextClip("Third", duration=2.0, start_time=8.0)   # 8-10
        
        track.add_clip(clip1)
        track.add_clip(clip2)
        track.add_clip(clip3)
        
        # Test different time points
        clips_at_0 = track.find_clips_at_time(0.0)
        assert len(clips_at_0) == 1
        assert clips_at_0[0] == clip1
        
        clips_at_4_5 = track.find_clips_at_time(4.5)  # Overlap time
        assert len(clips_at_4_5) == 2
        assert clip1 in clips_at_4_5
        assert clip2 in clips_at_4_5
        
        clips_at_9 = track.find_clips_at_time(9.0)
        assert len(clips_at_9) == 1
        assert clips_at_9[0] == clip3
        
        clips_at_15 = track.find_clips_at_time(15.0)  # No clips
        assert len(clips_at_15) == 0


class TestClips:
    """Tests for clip classes."""
    
    def test_text_clip_creation(self):
        """Test TextClip creation and properties."""
        clip = TextClip(
            text="Hello World",
            duration=5.0,
            start_time=1.0,
            font_size=48,
            font_family="Arial",
            color=Color(255, 255, 255),
            position=Position(100, 200),
            name="Test Text"
        )
        
        assert clip.text == "Hello World"
        assert clip.duration == 5.0
        assert clip.start_time == 1.0
        assert clip.end_time == 6.0
        assert clip.font_size == 48
        assert clip.font_family == "Arial"
        assert clip.color.r == 255
        assert clip.position.x == 100
        assert clip.position.y == 200
        assert clip.name == "Test Text"
        assert clip.get_type() == "text"
    
    def test_text_clip_methods(self):
        """Test TextClip chainable methods."""
        clip = TextClip("Test", duration=3.0)
        
        result = clip.set_bold(True).set_italic(True).set_alignment("center")
        
        assert result == clip  # Should return self for chaining
        assert clip.bold is True
        assert clip.italic is True
        assert clip.alignment == "center"
    
    def test_video_clip_creation(self):
        """Test VideoClip creation."""
        clip = VideoClip(
            source_path="/path/to/video.mp4",
            start_time=2.0,
            duration=10.0,
            trim_start=1.0,
            trim_end=15.0,
            scale=1.5,
            position=Position(50, 100),
            name="Test Video"
        )
        
        assert str(clip.source_path) == "/path/to/video.mp4"
        assert clip.start_time == 2.0
        assert clip.duration == 10.0
        assert clip.end_time == 12.0
        assert clip.trim_start == 1.0
        assert clip.trim_end == 15.0
        assert clip.scale == 1.5
        assert clip.position.x == 50
        assert clip.get_type() == "video"
    
    def test_audio_clip_creation(self):
        """Test AudioClip creation."""
        clip = AudioClip(
            source_path="/path/to/audio.wav",
            start_time=0.0,
            duration=30.0,
            volume=0.8,
            name="Test Audio"
        )
        
        assert str(clip.source_path) == "/path/to/audio.wav"
        assert clip.duration == 30.0
        assert clip.volume == 0.8
        assert clip.get_type() == "audio"
    
    def test_audio_clip_methods(self):
        """Test AudioClip chainable methods."""
        clip = AudioClip("test.wav", duration=5.0)
        
        result = clip.set_volume(0.5).set_fade_in(1.0).set_fade_out(2.0).mute(True)
        
        assert result == clip
        assert clip.volume == 0.5
        assert clip.fade_in_duration == 1.0
        assert clip.fade_out_duration == 2.0
        assert clip.muted is True
    
    def test_image_clip_creation(self):
        """Test ImageClip creation."""
        clip = ImageClip(
            source_path="/path/to/image.jpg",
            duration=5.0,
            start_time=1.0,
            scale=0.5,
            position=Position(200, 300)
        )
        
        assert str(clip.source_path) == "/path/to/image.jpg"
        assert clip.duration == 5.0
        assert clip.start_time == 1.0
        assert clip.scale == 0.5
        assert clip.position.x == 200
        assert clip.get_type() == "image"
    
    def test_clip_properties(self):
        """Test clip custom properties."""
        clip = TextClip("Test", duration=1.0)
        
        clip.set_property("custom_prop", "custom_value")
        clip.set_property("number_prop", 42)
        
        assert clip.get_property("custom_prop") == "custom_value"
        assert clip.get_property("number_prop") == 42
        assert clip.get_property("missing_prop") is None
        assert clip.get_property("missing_prop", "default") == "default"


class TestTransitions:
    """Tests for transition classes."""
    
    def test_crossfade_transition(self):
        """Test CrossfadeTransition creation."""
        transition = CrossfadeTransition(
            duration=2.0,
            curve="ease_in_out",
            name="Test Crossfade"
        )
        
        assert transition.duration == 2.0
        assert transition.curve == "ease_in_out"
        assert transition.name == "Test Crossfade"
        
        params = transition.get_parameters()
        assert params["curve"] == "ease_in_out"
        assert params["duration"] == 2.0
    
    def test_crossfade_curve_validation(self):
        """Test that CrossfadeTransition validates curve types."""
        # Valid curve should work
        transition = CrossfadeTransition(1.0, curve="linear")
        assert transition.curve == "linear"
        
        # Invalid curve should raise error
        with pytest.raises(ValueError):
            CrossfadeTransition(1.0, curve="invalid_curve")
    
    def test_wipe_transition(self):
        """Test WipeTransition creation."""
        transition = WipeTransition(
            duration=1.5,
            direction=WipeDirection.RIGHT_TO_LEFT,
            feather=0.3,
            name="Test Wipe"
        )
        
        assert transition.duration == 1.5
        assert transition.direction == WipeDirection.RIGHT_TO_LEFT
        assert transition.feather == 0.3
        assert transition.name == "Test Wipe"
        
        params = transition.get_parameters()
        assert params["direction"] == "right_to_left"
        assert params["feather"] == 0.3
    
    def test_wipe_transition_methods(self):
        """Test WipeTransition chainable methods."""
        transition = WipeTransition(1.0)
        
        result = transition.set_direction(WipeDirection.TOP_TO_BOTTOM).set_feather(0.8)
        
        assert result == transition
        assert transition.direction == WipeDirection.TOP_TO_BOTTOM
        assert transition.feather == 0.8  # Should be clamped to max 1.0
    
    def test_transition_feather_clamping(self):
        """Test that feather values are clamped to 0.0-1.0 range."""
        # Test constructor clamping
        transition = WipeTransition(1.0, feather=2.0)  # > 1.0
        assert transition.feather == 1.0
        
        transition = WipeTransition(1.0, feather=-0.5)  # < 0.0
        assert transition.feather == 0.0
        
        # Test setter clamping
        transition.set_feather(1.5)
        assert transition.feather == 1.0
        
        transition.set_feather(-0.2)
        assert transition.feather == 0.0


class TestColor:
    """Tests for Color class."""
    
    def test_color_creation(self):
        """Test Color creation and properties."""
        color = Color(255, 128, 64, 200)
        
        assert color.r == 255
        assert color.g == 128
        assert color.b == 64
        assert color.a == 200
    
    def test_color_hex_conversion(self):
        """Test Color to hex string conversion."""
        color = Color(255, 128, 64)
        hex_color = color.to_hex()
        
        assert hex_color == "#ff8040"
    
    def test_color_defaults(self):
        """Test Color default values."""
        color = Color(255, 255, 255)  # No alpha specified
        
        assert color.a == 255  # Should default to 255


class TestPosition:
    """Tests for Position class."""
    
    def test_position_creation(self):
        """Test Position creation."""
        pos = Position(100.5, 200.7)
        
        assert pos.x == 100.5
        assert pos.y == 200.7
