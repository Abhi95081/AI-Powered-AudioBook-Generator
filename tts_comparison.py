"""
TTS Engine Comparison Tool

Tests multiple TTS engines on sample text and helps you choose the best one.
"""
import time
from pathlib import Path
from tts_enhanced import (
    tts_synthesize,
    list_available_engines,
    HAS_PYTTSX3,
    HAS_GTTS,
    HAS_EDGE_TTS,
    HAS_COQUI,
    HAS_BARK,
)


SAMPLE_TEXT = """
Welcome to the AI Audiobook Generator. This is a test of text-to-speech quality.
The quick brown fox jumps over the lazy dog. Can you hear the naturalness and clarity of this voice?
"""


def test_engine(engine_name: str, sample_text: str = SAMPLE_TEXT) -> dict:
    """Test a single TTS engine and return metrics."""
    print(f"\n{'='*60}")
    print(f"Testing: {engine_name}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        audio_path = tts_synthesize(
            text=sample_text,
            engine=engine_name,
            basename=f"test_{engine_name}",
        )
        elapsed = time.time() - start_time
        
        file_size = audio_path.stat().st_size / 1024  # KB
        
        result = {
            "success": True,
            "time": elapsed,
            "file_size_kb": file_size,
            "path": audio_path,
            "error": None,
        }
        
        print(f"✓ Success!")
        print(f"  Time: {elapsed:.2f}s")
        print(f"  Size: {file_size:.1f} KB")
        print(f"  File: {audio_path}")
        
        return result
        
    except Exception as e:
        print(f"✗ Failed: {e}")
        return {
            "success": False,
            "time": 0,
            "file_size_kb": 0,
            "path": None,
            "error": str(e),
        }


def compare_all_engines(sample_text: str = SAMPLE_TEXT):
    """Compare all available TTS engines."""
    print("\n" + "="*60)
    print("TTS ENGINE COMPARISON")
    print("="*60)
    
    engines_to_test = []
    if HAS_PYTTSX3:
        engines_to_test.append("pyttsx3")
    if HAS_GTTS:
        engines_to_test.append("gtts")
    if HAS_EDGE_TTS:
        engines_to_test.append("edge-tts")
    if HAS_COQUI:
        engines_to_test.append("coqui")
    if HAS_BARK:
        engines_to_test.append("bark")
    
    if not engines_to_test:
        print("❌ No TTS engines available!")
        print("\nInstall at least one:")
        print("  pip install edge-tts          # Recommended: fast, high quality")
        print("  pip install gtts               # Simple, decent quality")
        print("  pip install pyttsx3            # Offline, lower quality")
        return
    
    results = {}
    for engine in engines_to_test:
        results[engine] = test_engine(engine, sample_text)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    # Get engine info
    engines_info = list_available_engines()
    
    print(f"\n{'Engine':<15} {'Status':<10} {'Time':<10} {'Size':<12} {'Quality'}")
    print("-" * 70)
    
    for engine, result in results.items():
        status = "✓ Success" if result["success"] else "✗ Failed"
        time_str = f"{result['time']:.2f}s" if result["success"] else "N/A"
        size_str = f"{result['file_size_kb']:.1f} KB" if result["success"] else "N/A"
        quality = engines_info[engine]["quality"]
        
        print(f"{engine:<15} {status:<10} {time_str:<10} {size_str:<12} {quality}")
    
    # Recommendation
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    successful = [e for e, r in results.items() if r["success"]]
    
    if "edge-tts" in successful:
        print("🥇 BEST CHOICE: edge-tts")
        print("   ✓ High quality natural voices")
        print("   ✓ Fast generation")
        print("   ✓ Free (requires internet)")
        print("   ✓ Best balance of quality and speed")
    elif "coqui" in successful:
        print("🥇 BEST CHOICE: coqui")
        print("   ✓ High quality neural TTS")
        print("   ✓ Offline (no internet needed)")
        print("   ⚠ Requires model download (~100MB)")
    elif "gtts" in successful:
        print("🥇 BEST CHOICE: gtts")
        print("   ✓ Decent quality")
        print("   ✓ Simple and reliable")
        print("   ⚠ Requires internet")
    elif "pyttsx3" in successful:
        print("🥇 AVAILABLE: pyttsx3")
        print("   ✓ Offline and fast")
        print("   ⚠ Lower quality (robotic)")
    
    if "bark" in successful:
        print("\n🎭 PREMIUM OPTION: bark")
        print("   ✓ Highest quality with emotions")
        print("   ⚠ Very slow without GPU")
        print("   ⚠ Large models (>2GB)")
    
    print("\n" + "="*60)
    print(f"Audio files saved to: outputs/audio/")
    print("Listen to them to judge quality yourself!")
    print("="*60)


if __name__ == "__main__":
    compare_all_engines()
