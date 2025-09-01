"""
TranscriptionService port interface for AI speech-to-text services.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from enum import Enum


class TranscriptionLanguage(Enum):
    """Supported languages for transcription."""
    AUTO = "auto"
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    JAPANESE = "ja"
    CHINESE = "zh"
    KOREAN = "ko"
    DUTCH = "nl"
    TURKISH = "tr"
    POLISH = "pl"
    SWEDISH = "sv"
    UKRAINIAN = "ua"
    DANISH = "da"
    NORWEGIAN = "no"
    FINNISH = "fi"


@dataclass
class SubtitleSegment:
    """Represents a single subtitle segment with timing and text."""
    text: str
    start_time: float  # in seconds
    end_time: float    # in seconds
    confidence: Optional[float] = None  # 0.0 to 1.0
    speaker_id: Optional[str] = None
    language: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Get the duration of this segment."""
        return self.end_time - self.start_time
    
    def to_srt_format(self, index: int) -> str:
        """Convert to SRT format string."""
        start_time = self._seconds_to_srt_time(self.start_time)
        end_time = self._seconds_to_srt_time(self.end_time)
        return f"{index}\n{start_time} --> {end_time}\n{self.text}\n\n"
    
    def to_vtt_format(self) -> str:
        """Convert to WebVTT format string."""
        start_time = self._seconds_to_vtt_time(self.start_time)
        end_time = self._seconds_to_vtt_time(self.end_time)
        return f"{start_time} --> {end_time}\n{self.text}\n\n"
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to VTT time format (HH:MM:SS.mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"


@dataclass
class TranscriptionResult:
    """Complete transcription result with metadata."""
    segments: List[SubtitleSegment]
    language: str
    duration: float
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def full_text(self) -> str:
        """Get the complete transcribed text."""
        return " ".join(segment.text for segment in self.segments)
    
    def to_srt(self) -> str:
        """Convert to SRT subtitle format."""
        srt_content = ""
        for i, segment in enumerate(self.segments, 1):
            srt_content += segment.to_srt_format(i)
        return srt_content
    
    def to_vtt(self) -> str:
        """Convert to WebVTT subtitle format."""
        vtt_content = "WEBVTT\n\n"
        for segment in self.segments:
            vtt_content += segment.to_vtt_format()
        return vtt_content
    
    def filter_by_confidence(self, min_confidence: float) -> 'TranscriptionResult':
        """Filter segments by minimum confidence level."""
        filtered_segments = [
            segment for segment in self.segments 
            if segment.confidence is None or segment.confidence >= min_confidence
        ]
        
        return TranscriptionResult(
            segments=filtered_segments,
            language=self.language,
            duration=self.duration,
            confidence=self.confidence,
            processing_time=self.processing_time,
            model_used=self.model_used,
            metadata=self.metadata.copy()
        )
    
    def merge_short_segments(self, min_duration: float = 1.0) -> 'TranscriptionResult':
        """Merge segments that are shorter than min_duration."""
        if not self.segments:
            return self
        
        merged_segments = []
        current_segment = self.segments[0]
        
        for segment in self.segments[1:]:
            if current_segment.duration < min_duration:
                # Merge with next segment
                current_segment = SubtitleSegment(
                    text=f"{current_segment.text} {segment.text}",
                    start_time=current_segment.start_time,
                    end_time=segment.end_time,
                    confidence=min(
                        current_segment.confidence or 1.0,
                        segment.confidence or 1.0
                    ) if current_segment.confidence and segment.confidence else None,
                    speaker_id=current_segment.speaker_id,
                    language=current_segment.language
                )
            else:
                merged_segments.append(current_segment)
                current_segment = segment
        
        merged_segments.append(current_segment)
        
        return TranscriptionResult(
            segments=merged_segments,
            language=self.language,
            duration=self.duration,
            confidence=self.confidence,
            processing_time=self.processing_time,
            model_used=self.model_used,
            metadata=self.metadata.copy()
        )


class TranscriptionOptions:
    """Configuration options for transcription services."""
    
    def __init__(
        self,
        language: TranscriptionLanguage = TranscriptionLanguage.AUTO,
        model: Optional[str] = None,
        temperature: float = 0.0,
        response_format: str = "segments",
        timestamp_granularities: Optional[List[str]] = None,
        max_segment_length: Optional[float] = None,
        min_segment_length: Optional[float] = None,
        speaker_detection: bool = False,
        word_timestamps: bool = True,
        punctuation: bool = True,
        profanity_filter: bool = False,
    ):
        """
        Initialize transcription options.
        
        Args:
            language: Language for transcription
            model: Specific model to use (service-dependent)
            temperature: Sampling temperature (0.0 to 1.0)
            response_format: Format of the response
            timestamp_granularities: Level of timestamp detail
            max_segment_length: Maximum segment duration in seconds
            min_segment_length: Minimum segment duration in seconds
            speaker_detection: Enable speaker identification
            word_timestamps: Include word-level timestamps
            punctuation: Add punctuation to transcription
            profanity_filter: Filter profanity from results
        """
        self.language = language
        self.model = model
        self.temperature = temperature
        self.response_format = response_format
        self.timestamp_granularities = timestamp_granularities or ["segment"]
        self.max_segment_length = max_segment_length
        self.min_segment_length = min_segment_length
        self.speaker_detection = speaker_detection
        self.word_timestamps = word_timestamps
        self.punctuation = punctuation
        self.profanity_filter = profanity_filter


class TranscriptionService(ABC):
    """
    Abstract interface for speech-to-text transcription services.
    
    This port defines the contract for AI transcription adapters,
    enabling automatic subtitle generation from audio content.
    """
    
    @abstractmethod
    def transcribe(
        self, 
        audio_file_path: Path, 
        options: Optional[TranscriptionOptions] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text with timestamps.
        
        Args:
            audio_file_path: Path to audio file to transcribe
            options: Optional transcription configuration
            
        Returns:
            Transcription result with segments and metadata
            
        Raises:
            TranscriptionError: If transcription fails
            FileNotFoundError: If audio file doesn't exist
            UnsupportedFormatError: If audio format is not supported
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats.
        
        Returns:
            List of file extensions (e.g., ['.wav', '.mp3', '.m4a'])
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[TranscriptionLanguage]:
        """
        Get list of supported languages.
        
        Returns:
            List of supported language codes
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the transcription service is available.
        
        Returns:
            True if service can be used (API keys set, network available, etc.)
        """
        pass
    
    def validate_audio_file(self, audio_file_path: Path) -> bool:
        """
        Validate that audio file can be transcribed.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            True if file is valid for transcription
        """
        if not audio_file_path.exists():
            return False
        
        extension = audio_file_path.suffix.lower()
        return extension in self.get_supported_formats()
    
    def estimate_cost(
        self, 
        audio_file_path: Path, 
        options: Optional[TranscriptionOptions] = None
    ) -> Optional[float]:
        """
        Estimate the cost of transcription (if applicable).
        
        Args:
            audio_file_path: Path to audio file
            options: Transcription options
            
        Returns:
            Estimated cost in USD, or None if not applicable
        """
        return None  # Default implementation
    
    def get_name(self) -> str:
        """Get the name of this transcription service."""
        return self.__class__.__name__
    
    def get_version(self) -> str:
        """Get version information for this service."""
        return "unknown"


class TranscriptionError(Exception):
    """Exception raised when transcription fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}


class UnsupportedFormatError(TranscriptionError):
    """Exception raised when audio format is not supported."""
    pass


class ServiceUnavailableError(TranscriptionError):
    """Exception raised when transcription service is unavailable."""
    pass


class QuotaExceededError(TranscriptionError):
    """Exception raised when service quota is exceeded."""
    pass
