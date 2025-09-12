import os
import tempfile
import logging
import speech_recognition as sr
from faster_whisper import WhisperModel
from typing import Optional, Union, List, Dict

logger = logging.getLogger(__name__)


class FastSTT:
    """
    Hybrid Speech-to-Text using SpeechRecognition (mic input)
    and Faster-Whisper (transcription).

    Supports:
    - Microphone input (real-time)
    - Audio file input (WAV, MP3, etc.)
    - Optional timestamps
    - Manual or auto language detection
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        raise_on_error: bool = False,
    ):
        """
        Initialize FastSTT.

        Args:
            model_size (str): Size of the Whisper model (tiny, base, small, medium, large).
            device (str): Device for inference ("cpu" or "cuda").
            compute_type (str): Precision type ("int8", "float16", "int8_float16", ...)
            raise_on_error (bool): If True, raise exceptions instead of returning None.
        """
        self.recognizer = sr.Recognizer()
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.model_size = model_size
        self.raise_on_error = raise_on_error

        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def listen_and_transcribe(
        self,
        timeout: int = 5,
        phrase_time_limit: Optional[int] = None,
        beam_size: int = 5,
        with_timestamps: bool = False,
        language: Optional[str] = None,
        sample_rate: int = 16000,
        device_index: Optional[int] = None,
    ) -> Optional[Union[Dict[str, str], List[Dict[str, Union[float, str]]]]]:
        """
        Listen from the microphone and transcribe.

        Args:
            timeout (int): Seconds to wait for phrase before timeout.
            phrase_time_limit (int, optional): Maximum phrase length in seconds.
            beam_size (int): Beam size for decoding.
            with_timestamps (bool): If True, return list of dicts with timestamps.
            language (str, optional): Force transcription in a specific language (e.g., "en", "fr", "ta", "hi"). If None, auto-detect.
            sample_rate (int): Microphone recording sample rate. Defaults to 16000 (recommended for Whisper).
            device_index (int, optional): Microphone device index. If None, uses the default system microphone.

        Returns:
            dict | list[dict] | None
                - dict: {"text": str, "language": str} if with_timestamps=False
                - list[dict]: [{"start": float, "end": float, "text": str, "language": str}] if with_timestamps=True
                - None if transcription fails or times out

        Example:
            >>> stt = FastSTT()
            >>> stt.listen_and_transcribe()
            {'text': 'hello world', 'language': 'en'}
        """
        with sr.Microphone(sample_rate=sample_rate, device_index=device_index) as source:
            logger.info("Listening...")
            try:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            except sr.WaitTimeoutError:
                logger.warning("Listening timed out")
                return None

        audio_path = self._save_temp_wav(audio)
        try:
            transcription = self.transcribe(audio_path, beam_size, with_timestamps, language)
        finally:
            os.remove(audio_path)
        return transcription

    def listen_from_file(
        self,
        file_path: str,
        beam_size: int = 5,
        with_timestamps: bool = False,
        language: Optional[str] = None,
    ) -> Optional[Union[Dict[str, str], List[Dict[str, Union[float, str]]]]]:
        """
        Transcribe audio from a given file path.

        Args:
            file_path (str): Path to audio file (WAV, MP3, M4A, etc.)
            beam_size (int): Beam size for decoding.
            with_timestamps (bool): Return timestamps if True.
            language (str, optional): Force transcription in a specific language (e.g., "en", "fr", "ta", "hi"). If None, auto-detect.

        Returns:
            dict | list[dict] | None
                - dict: {"text": str, "language": str} if with_timestamps=False
                - list[dict]: [{"start": float, "end": float, "text": str, "language": str}] if with_timestamps=True
                - None if transcription fails or times out

        Example:
            >>> stt = FastSTT()
            >>> stt.listen_from_file("sample.wav")
            {'text': 'hello world', 'language': 'en'}
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Transcribing file: {file_path}")
        return self.transcribe(file_path, beam_size, with_timestamps, language)

    def transcribe(
        self,
        audio_path: str,
        beam_size: int = 5,
        with_timestamps: bool = False,
        language: Optional[str] = None,
    ) -> Optional[Union[Dict[str, str], List[Dict[str, Union[float, str]]]]]:
        """
        Core transcription method.

        Args:
            audio_path (str): Path to audio file.
            beam_size (int): Beam size for decoding.
            with_timestamps (bool): If True, return list of dicts with timestamps.
            language (str, optional): Force transcription in a specific language (e.g., "en", "fr", "ta", "hi"). If None, auto-detect.

        Returns:
            dict | list[dict] | None
                - dict: {"text": str, "language": str} if with_timestamps=False
                - list[dict]: [{"start": float, "end": float, "text": str, "language": str}] if with_timestamps=True
                - None if transcription fails or times out
        """
        try:
            segments, info = self.model.transcribe(
                audio_path, beam_size=beam_size, language=language
            )
            if info.language != "en" and self.model_size in ["tiny", "base"]:
                logger.warning(
                    f"Detected language '{info.language}'. "
                    "Consider using 'small', 'medium', or 'large' for better multilingual accuracy."
                )

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            if self.raise_on_error:
                raise
            return None

        if with_timestamps:
            return [
                {
                    "start": s.start,
                    "end": s.end,
                    "text": s.text.strip(),
                    "language": info.language,
                }
                for s in segments
            ]

        transcription = " ".join([s.text for s in segments]).strip()
        return {"text": transcription, "language": info.language}

    @staticmethod
    def _save_temp_wav(audio):
        """Save SpeechRecognition audio to a temp WAV file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(audio.get_wav_data())
            return tmp.name