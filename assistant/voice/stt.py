import numpy as np
from faster_whisper import WhisperModel

from assistant.config import settings

# Cached model instance (loaded once on first call)
_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.whisper_model,
            device="auto",       # uses CUDA if available, else CPU
            compute_type="int8", # balanced speed/accuracy
        )
    return _model


def transcribe(audio: np.ndarray, sample_rate: int = 16000) -> str:
    """
    Transcribe a raw audio array (mono, any dtype) to Russian text.

    Args:
        audio:       1-D numpy array of audio samples.
        sample_rate: Original sample rate of *audio* (will be resampled to
                     16 kHz automatically if it differs).

    Returns:
        Transcribed text string (empty string if no speech detected).
    """
    # Resample to 16 kHz if needed
    if sample_rate != 16000:
        import scipy.signal

        n_target = int(len(audio) * 16000 / sample_rate)
        audio = scipy.signal.resample(audio, n_target)

    # Normalise to float32 in [-1.0, 1.0]
    audio = audio.astype(np.float32)
    if audio.max() > 1.0:
        audio = audio / 32768.0

    model = _get_model()
    segments, _ = model.transcribe(
        audio,
        language="ru",
        vad_filter=True,   # Silero VAD built into faster-whisper
        beam_size=5,
    )
    return " ".join(seg.text for seg in segments).strip()
