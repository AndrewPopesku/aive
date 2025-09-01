"""
Groq Whisper adapter that implements the TranscriptionService port.
"""
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..ports.transcription_service import (
    TranscriptionService, TranscriptionOptions, TranscriptionResult,
    SubtitleSegment, TranscriptionLanguage, TranscriptionError,
    ServiceUnavailableError, QuotaExceededError, UnsupportedFormatError
)

try:
    from groq import Groq
    import requests
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None
    requests = None


class GroqWhisperTranscriber(TranscriptionService):
    """
    Groq Whisper-based transcription service implementing the TranscriptionService port.
    
    This adapter uses the Groq API to run Whisper models for fast, accurate
    speech-to-text transcription with timestamps.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Groq Whisper transcriber.
        
        Args:
            api_key: Groq API key. If None, looks for GROQ_API_KEY environment variable
        """
        if not GROQ_AVAILABLE:
            raise ImportError(
                "Groq is required for GroqWhisperTranscriber. "
                "Install it with: pip install aive[whisper]"
            )
        
        # Get API key
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Groq API key is required. Set GROQ_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        
        # Model configuration
        self.default_model = "whisper-large-v3"
        self.available_models = [
            "whisper-large-v3",
            "whisper-large-v3-turbo",
        ]
        
        # File size limits (25MB for Groq)
        self.max_file_size = 25 * 1024 * 1024
    
    def transcribe(
        self, 
        audio_file_path: Path, 
        options: Optional[TranscriptionOptions] = None
    ) -> TranscriptionResult:
        """
        Transcribe audio file to text with timestamps using Groq Whisper.
        
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
        if not self.validate_audio_file(audio_file_path):
            if not audio_file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            else:
                raise UnsupportedFormatError(
                    f"Unsupported audio format: {audio_file_path.suffix}"
                )
        
        if not self.is_available():
            raise ServiceUnavailableError("Groq service is not available")
        
        if options is None:
            options = TranscriptionOptions()
        
        # Check file size
        file_size = audio_file_path.stat().st_size
        if file_size > self.max_file_size:
            raise TranscriptionError(
                f"File size {file_size / 1024 / 1024:.1f}MB exceeds "
                f"maximum {self.max_file_size / 1024 / 1024:.1f}MB"
            )
        
        try:
            start_time = time.time()
            
            # Prepare transcription parameters
            transcribe_params = self._prepare_transcription_params(options)
            
            # Open and transcribe the audio file
            with open(audio_file_path, 'rb') as audio_file:
                transcription = self.client.audio.transcriptions.create(
                    file=(audio_file_path.name, audio_file),
                    **transcribe_params
                )
            
            processing_time = time.time() - start_time
            
            # Convert response to TranscriptionResult
            return self._convert_response(
                transcription, 
                options, 
                processing_time,
                audio_file_path
            )
            
        except Exception as e:
            # Handle specific Groq API errors
            error_message = str(e)
            
            if "quota" in error_message.lower() or "rate limit" in error_message.lower():
                raise QuotaExceededError(f"Groq API quota exceeded: {error_message}")
            elif "unauthorized" in error_message.lower():
                raise ServiceUnavailableError(f"Invalid Groq API key: {error_message}")
            else:
                raise TranscriptionError(
                    f"Groq transcription failed: {error_message}",
                    {
                        'file_path': str(audio_file_path),
                        'file_size': file_size,
                        'options': self._options_to_dict(options)
                    }
                ) from e
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported audio formats.
        
        Returns:
            List of file extensions supported by Groq Whisper
        """
        return [
            '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.wav', '.webm',
            '.aac', '.flac', '.ogg', '.opus', '.wma'
        ]
    
    def get_supported_languages(self) -> List[TranscriptionLanguage]:
        """
        Get list of supported languages.
        
        Returns:
            List of supported language codes
        """
        # Whisper supports many languages
        return [
            TranscriptionLanguage.AUTO,
            TranscriptionLanguage.ENGLISH,
            TranscriptionLanguage.SPANISH,
            TranscriptionLanguage.FRENCH,
            TranscriptionLanguage.GERMAN,
            TranscriptionLanguage.ITALIAN,
            TranscriptionLanguage.PORTUGUESE,
            TranscriptionLanguage.JAPANESE,
            TranscriptionLanguage.CHINESE,
            TranscriptionLanguage.KOREAN,
            TranscriptionLanguage.DUTCH,
            TranscriptionLanguage.TURKISH,
            TranscriptionLanguage.POLISH,
            TranscriptionLanguage.SWEDISH,
            TranscriptionLanguage.UKRAINIAN,
            TranscriptionLanguage.DANISH,
            TranscriptionLanguage.NORWEGIAN,
            TranscriptionLanguage.FINNISH,
        ]
    
    def is_available(self) -> bool:
        """
        Check if the Groq transcription service is available.
        
        Returns:
            True if service can be used (API key set, network available, etc.)
        """
        if not GROQ_AVAILABLE or not self.api_key:
            return False
        
        try:
            # Test API connectivity with a simple request
            # Note: This doesn't actually test transcription, just API access
            models = self.client.models.list()
            return True
        except Exception:
            return False
    
    def estimate_cost(
        self, 
        audio_file_path: Path, 
        options: Optional[TranscriptionOptions] = None
    ) -> Optional[float]:
        """
        Estimate the cost of transcription.
        
        Args:
            audio_file_path: Path to audio file
            options: Transcription options
            
        Returns:
            Estimated cost in USD (Groq is currently free, so returns 0.0)
        """
        # Groq is currently free for Whisper API
        # This may change in the future
        return 0.0
    
    def get_name(self) -> str:
        """Get the name of this transcription service."""
        return "Groq Whisper Transcriber"
    
    def get_version(self) -> str:
        """Get version information for this service."""
        if GROQ_AVAILABLE:
            # Try to get Groq version, fallback to generic
            try:
                import groq
                return f"Groq {groq.__version__}"
            except:
                return "Groq (version unknown)"
        return "Groq not available"
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models."""
        return self.available_models.copy()
    
    def set_default_model(self, model: str) -> None:
        """
        Set the default model to use.
        
        Args:
            model: Model name to use as default
        """
        if model in self.available_models:
            self.default_model = model
        else:
            raise ValueError(f"Unknown model: {model}. Available: {self.available_models}")
    
    def _prepare_transcription_params(self, options: TranscriptionOptions) -> Dict[str, Any]:
        """Prepare parameters for Groq transcription API."""
        params = {
            'model': options.model or self.default_model,
            'response_format': 'verbose_json',  # Always use verbose for timestamps
            'temperature': options.temperature,
        }
        
        # Language parameter
        if options.language != TranscriptionLanguage.AUTO:
            params['language'] = options.language.value
        
        # Timestamp granularities
        if options.timestamp_granularities:
            # Groq supports 'segment' and 'word' granularities
            valid_granularities = [g for g in options.timestamp_granularities 
                                  if g in ['segment', 'word']]
            if valid_granularities:
                params['timestamp_granularities'] = valid_granularities
        
        return params
    
    def _convert_response(
        self, 
        transcription: Any, 
        options: TranscriptionOptions,
        processing_time: float,
        audio_file_path: Path
    ) -> TranscriptionResult:
        """Convert Groq API response to TranscriptionResult."""
        segments = []
        
        # Handle different response formats
        if hasattr(transcription, 'segments') and transcription.segments:
            # Segment-level timestamps available
            for segment in transcription.segments:
                subtitle_segment = SubtitleSegment(
                    text=segment.text.strip(),
                    start_time=segment.start,
                    end_time=segment.end,
                    confidence=getattr(segment, 'avg_logprob', None),
                    language=getattr(transcription, 'language', None)
                )
                segments.append(subtitle_segment)
        
        else:
            # Fallback: create single segment from full text
            duration = self._estimate_audio_duration(audio_file_path)
            segments.append(SubtitleSegment(
                text=transcription.text.strip(),
                start_time=0.0,
                end_time=duration,
                language=getattr(transcription, 'language', None)
            ))
        
        # Post-process segments based on options
        if options.min_segment_length:
            segments = self._merge_short_segments(segments, options.min_segment_length)
        
        if options.max_segment_length:
            segments = self._split_long_segments(segments, options.max_segment_length)
        
        # Create result
        result = TranscriptionResult(
            segments=segments,
            language=getattr(transcription, 'language', 'unknown'),
            duration=segments[-1].end_time if segments else 0.0,
            processing_time=processing_time,
            model_used=options.model or self.default_model,
            metadata={
                'groq_api': True,
                'file_name': audio_file_path.name,
                'file_size': audio_file_path.stat().st_size,
                'options': self._options_to_dict(options)
            }
        )
        
        return result
    
    def _merge_short_segments(
        self, 
        segments: List[SubtitleSegment], 
        min_duration: float
    ) -> List[SubtitleSegment]:
        """Merge segments that are shorter than min_duration."""
        if not segments:
            return segments
        
        merged_segments = []
        current_segment = segments[0]
        
        for segment in segments[1:]:
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
                    language=current_segment.language
                )
            else:
                merged_segments.append(current_segment)
                current_segment = segment
        
        merged_segments.append(current_segment)
        return merged_segments
    
    def _split_long_segments(
        self, 
        segments: List[SubtitleSegment], 
        max_duration: float
    ) -> List[SubtitleSegment]:
        """Split segments that are longer than max_duration."""
        split_segments = []
        
        for segment in segments:
            if segment.duration <= max_duration:
                split_segments.append(segment)
            else:
                # Simple word-based splitting
                words = segment.text.split()
                if len(words) <= 1:
                    # Can't split single word, keep as is
                    split_segments.append(segment)
                    continue
                
                # Split into roughly equal parts
                words_per_segment = max(1, len(words) // 2)
                word_chunks = [
                    words[i:i + words_per_segment] 
                    for i in range(0, len(words), words_per_segment)
                ]
                
                # Create segments from word chunks
                time_per_chunk = segment.duration / len(word_chunks)
                current_start = segment.start_time
                
                for chunk in word_chunks:
                    chunk_segment = SubtitleSegment(
                        text=' '.join(chunk),
                        start_time=current_start,
                        end_time=current_start + time_per_chunk,
                        confidence=segment.confidence,
                        language=segment.language
                    )
                    split_segments.append(chunk_segment)
                    current_start += time_per_chunk
        
        return split_segments
    
    def _estimate_audio_duration(self, audio_file_path: Path) -> float:
        """Estimate audio file duration (simplified implementation)."""
        # This is a simplified implementation
        # In practice, you'd use a library like librosa or ffprobe
        try:
            file_size = audio_file_path.stat().st_size
            # Very rough estimate based on file size
            # Assumes ~1MB per minute for typical audio
            return max(1.0, file_size / (1024 * 1024) * 60)
        except:
            return 60.0  # Default fallback
    
    def _options_to_dict(self, options: TranscriptionOptions) -> Dict[str, Any]:
        """Convert TranscriptionOptions to dictionary for metadata."""
        return {
            'language': options.language.value,
            'model': options.model,
            'temperature': options.temperature,
            'response_format': options.response_format,
            'timestamp_granularities': options.timestamp_granularities,
            'max_segment_length': options.max_segment_length,
            'min_segment_length': options.min_segment_length,
            'speaker_detection': options.speaker_detection,
            'word_timestamps': options.word_timestamps,
            'punctuation': options.punctuation,
            'profanity_filter': options.profanity_filter,
        }
    
    @staticmethod
    def is_available_static() -> bool:
        """Static method to check if Groq Whisper is available."""
        return GROQ_AVAILABLE and bool(os.getenv('GROQ_API_KEY'))
