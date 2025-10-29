"""
TTS Engine Test - Tests available TTS engines
"""
import sys

print("Testing TTS engines...")
print("=" * 60)

# Test pyttsx3
try:
    import pyttsx3
    print("✓ pyttsx3 available (offline, fast, lower quality)")
except ImportError:
    print("✗ pyttsx3 not installed")

# Test gTTS
try:
    from gtts import gTTS
    print("✓ gTTS available (online, decent quality) ⭐")
except ImportError:
    print("✗ gTTS not installed")

# Test edge-tts
try:
    import edge_tts
    print("✓ edge-tts available (online, high quality)")
except ImportError:
    print("✗ edge-tts not installed")

# Test Coqui
try:
    from TTS.api import TTS
    print("✓ Coqui TTS available (offline, neural, high quality)")
except ImportError:
    print("✗ Coqui TTS not installed")

print("=" * 60)

# Test actual TTS generation
print("\nTesting gTTS generation...")
try:
    from gtts import gTTS
    from pathlib import Path
    
    # Create outputs directory
    Path("outputs/audio").mkdir(parents=True, exist_ok=True)
    
    # Generate test audio
    text = "Hello! This is a test of the AI Audiobook Generator. The text-to-speech quality sounds natural and clear."
    tts = gTTS(text=text, lang='en', slow=False)
    
    output_file = "outputs/audio/test_gtts.mp3"
    tts.save(output_file)
    
    file_size = Path(output_file).stat().st_size / 1024
    print(f"✓ Generated test audio: {output_file} ({file_size:.1f} KB)")
    print("\n🎵 Play this file to hear the quality!")
    
except Exception as e:
    print(f"✗ Failed to generate test audio: {e}")
    sys.exit(1)
