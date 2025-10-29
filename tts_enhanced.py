"""
Enhanced TTS Module with Multiple Engine Support

Supports:
- pyttsx3: Offline, fast, lower quality
- gTTS: Online, Google TTS, decent quality
- Edge-TTS: Online, Microsoft Edge TTS, high quality, FREE
- Coqui TTS: Offline, neural, high quality (optional, large models)
- Bark: Offline, high quality with emotions (optional, very large)
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Literal, Optional
import logging

from utils import ensure_dirs, timestamped_filename, OUTPUT_AUDIO_DIR

logger = logging.getLogger(__name__)

# Core engines (lightweight)
try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False
    logger.debug("pyttsx3 not available")

try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False
    logger.debug("gTTS not available")

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
    logger.debug("edge-tts not available")

# Advanced engines (optional, heavy)
try:
    from TTS.api import TTS as CoquiTTS
    HAS_COQUI = True
except ImportError:
    HAS_COQUI = False
    logger.debug("Coqui TTS not available")

try:
    from bark import SAMPLE_RATE, generate_audio, preload_models
    from scipy.io.wavfile import write as write_wav
    HAS_BARK = True
except ImportError:
    HAS_BARK = False
    logger.debug("Bark not available")


EngineName = Literal["pyttsx3", "gtts", "edge-tts", "coqui", "bark"]


# Edge-TTS voices - high quality, free, natural
EDGE_VOICES = {
    "en-US-female": "en-US-JennyNeural",      # Natural, conversational
    "en-US-male": "en-US-GuyNeural",          # Clear, professional
    "en-GB-female": "en-GB-SoniaNeural",      # British English
    "en-GB-male": "en-GB-RyanNeural",         # British English
    "en-AU-female": "en-AU-NatashaNeural",    # Australian
    "en-IN-female": "en-IN-NeerjaNeural",     # Indian accent
}


def validate_text(text: str) -> str:
    """Validate and clean text for TTS."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Cannot synthesize empty text")
    return text


def synthesize_pyttsx3(
    text: str,
    basename: str = "speech",
    rate: Optional[int] = None,
    voice_id: Optional[str] = None,
) -> Path:
    """Offline TTS using pyttsx3 (SAPI5 on Windows)."""
    if not HAS_PYTTSX3:
        raise RuntimeError("pyttsx3 not installed. Install: pip install pyttsx3")
    
    text = validate_text(text)
    engine = pyttsx3.init()
    
    if rate is not None:
        engine.setProperty("rate", rate)
    if voice_id is not None:
        engine.setProperty("voice", voice_id)
    
    out_path = OUTPUT_AUDIO_DIR / f"{timestamped_filename(basename, 'pyttsx3')}.wav"
    engine.save_to_file(text, str(out_path))
    engine.runAndWait()
    
    logger.info(f"Synthesized with pyttsx3: {out_path}")
    return out_path


def synthesize_gtts(
    text: str,
    basename: str = "speech",
    language: str = "en",
) -> Path:
    """Online TTS using Google Translate TTS."""
    if not HAS_GTTS:
        raise RuntimeError("gTTS not installed. Install: pip install gtts")
    
    text = validate_text(text)
    tts = gTTS(text=text, lang=language, slow=False)
    
    out_path = OUTPUT_AUDIO_DIR / f"{timestamped_filename(basename, 'gtts')}.mp3"
    tts.save(str(out_path))
    
    logger.info(f"Synthesized with gTTS: {out_path}")
    return out_path


def synthesize_edge_tts(
    text: str,
    basename: str = "speech",
    voice: str = "en-US-JennyNeural",
) -> Path:
    """
    Online TTS using Microsoft Edge TTS (FREE, high quality).
    
    Recommended voices:
    - en-US-JennyNeural (female, natural)
    - en-US-GuyNeural (male, professional)
    """
    if not HAS_EDGE_TTS:
        raise RuntimeError("edge-tts not installed. Install: pip install edge-tts")
    
    text = validate_text(text)
    out_path = OUTPUT_AUDIO_DIR / f"{timestamped_filename(basename, 'edge-tts')}.mp3"
    
    # Edge-TTS requires async
    async def _generate():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(out_path))
    
    asyncio.run(_generate())
    
    logger.info(f"Synthesized with Edge-TTS ({voice}): {out_path}")
    return out_path


def synthesize_coqui(
    text: str,
    basename: str = "speech",
    model_name: str = "tts_models/en/ljspeech/tacotron2-DDC",
) -> Path:
    """
    Offline neural TTS using Coqui TTS.
    High quality but requires model download (can be large).
    """
    if not HAS_COQUI:
        raise RuntimeError(
            "Coqui TTS not installed. Install: pip install TTS\n"
            "Note: Models are large (~100MB+) and download on first use."
        )
    
    text = validate_text(text)
    tts = CoquiTTS(model_name)
    
    out_path = OUTPUT_AUDIO_DIR / f"{timestamped_filename(basename, 'coqui')}.wav"
    tts.tts_to_file(text=text, file_path=str(out_path))
    
    logger.info(f"Synthesized with Coqui ({model_name}): {out_path}")
    return out_path


def synthesize_bark(
    text: str,
    basename: str = "speech",
    voice_preset: str = "v2/en_speaker_6",
) -> Path:
    """
    Offline TTS using Bark (Suno AI).
    Very high quality with emotions, but slow and requires GPU for best performance.
    
    Voice presets: v2/en_speaker_0 to v2/en_speaker_9
    """
    if not HAS_BARK:
        raise RuntimeError(
            "Bark not installed. Install: pip install git+https://github.com/suno-ai/bark.git\n"
            "Note: Models are very large (>2GB) and slow without GPU."
        )
    
    text = validate_text(text)
    
    # Preload models (only once)
    preload_models()
    
    # Generate audio
    audio_array = generate_audio(text, history_prompt=voice_preset)
    
    out_path = OUTPUT_AUDIO_DIR / f"{timestamped_filename(basename, 'bark')}.wav"
    write_wav(str(out_path), SAMPLE_RATE, audio_array)
    
    logger.info(f"Synthesized with Bark ({voice_preset}): {out_path}")
    return out_path


def tts_synthesize(
    text: str,
    engine: EngineName = "edge-tts",
    basename: str = "speech",
    **kwargs,
) -> Path:
    """
    Synthesize speech with specified engine.
    
    Args:
        text: Text to synthesize
        engine: TTS engine to use
        basename: Base filename for output
        **kwargs: Engine-specific parameters
        
    Returns:
        Path to generated audio file
        
    Recommended engines (in order of quality/naturalness):
    1. edge-tts: FREE, high quality, natural voices (requires internet)
    2. coqui: Offline, neural, good quality (large models)
    3. bark: Offline, best quality with emotions (very slow, large)
    4. gtts: Online, Google TTS, decent (requires internet)
    5. pyttsx3: Offline, fast, lower quality
    """
    ensure_dirs()
    
    if engine == "pyttsx3":
        return synthesize_pyttsx3(text, basename, **kwargs)
    elif engine == "gtts":
        return synthesize_gtts(text, basename, **kwargs)
    elif engine == "edge-tts":
        return synthesize_edge_tts(text, basename, **kwargs)
    elif engine == "coqui":
        return synthesize_coqui(text, basename, **kwargs)
    elif engine == "bark":
        return synthesize_bark(text, basename, **kwargs)
    else:
        raise ValueError(f"Unknown engine: {engine}")


def list_available_engines() -> dict[str, dict]:
    """List all available TTS engines with their status."""
    return {
        "pyttsx3": {
            "available": HAS_PYTTSX3,
            "quality": "Low-Medium",
            "speed": "Fast",
            "type": "Offline",
            "cost": "Free",
            "notes": "System TTS, robotic sound",
        },
        "gtts": {
            "available": HAS_GTTS,
            "quality": "Medium",
            "speed": "Medium",
            "type": "Online",
            "cost": "Free",
            "notes": "Google TTS, requires internet",
        },
        "edge-tts": {
            "available": HAS_EDGE_TTS,
            "quality": "High",
            "speed": "Fast",
            "type": "Online",
            "cost": "Free",
            "notes": "Microsoft Edge TTS, natural voices ⭐ RECOMMENDED",
        },
        "coqui": {
            "available": HAS_COQUI,
            "quality": "High",
            "speed": "Medium",
            "type": "Offline",
            "cost": "Free",
            "notes": "Neural TTS, large models, download required",
        },
        "bark": {
            "available": HAS_BARK,
            "quality": "Very High",
            "speed": "Slow",
            "type": "Offline",
            "cost": "Free",
            "notes": "Best quality with emotions, GPU recommended, very large models",
        },
    }


def get_recommended_engine() -> EngineName:
    """Get the best available TTS engine."""
    if HAS_EDGE_TTS:
        return "edge-tts"  # Best free option: high quality, fast, natural
    elif HAS_COQUI:
        return "coqui"
    elif HAS_GTTS:
        return "gtts"
    elif HAS_PYTTSX3:
        return "pyttsx3"
    else:
        raise RuntimeError("No TTS engine available. Install at least one: pip install edge-tts")


if __name__ == "__main__":
    # Test and compare engines
    print("=" * 60)
    print("TTS Engines Status")
    print("=" * 60)
    
    engines = list_available_engines()
    for name, info in engines.items():
        status = "✓" if info["available"] else "✗"
        print(f"{status} {name:12} | Quality: {info['quality']:12} | {info['notes']}")
    
    print("\n" + "=" * 60)
    print(f"Recommended engine: {get_recommended_engine()}")
    print("=" * 60)
