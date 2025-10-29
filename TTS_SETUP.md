# TTS Module Setup Guide

## Overview
This guide helps you set up the enhanced TTS (Text-to-Speech) module for the AI Audiobook Generator.

## Quick Setup (Recommended)

### Step 1: Install Core Dependencies
```bash
# Activate virtual environment
.\.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Install TTS engines
pip install gtts pyttsx3 edge-tts
```

### Step 2: Test Installation
```bash
python test_tts_simple.py
```

This will:
- Check which TTS engines are available
- Generate a test audio file
- Report any issues

### Step 3: Run Complete Pipeline
```bash
# Basic usage with gTTS
python pipeline.py your_document.pdf

# With AI enrichment
python pipeline.py your_document.pdf --enrich

# With specific TTS engine
python pipeline.py your_document.pdf --engine edge-tts

# List available engines
python pipeline.py --list-engines
```

---

## Available TTS Engines

### 1. gTTS (Recommended Default)
**Installation:**
```bash
pip install gtts
```

**Features:**
- ✅ Simple and reliable
- ✅ Good quality
- ✅ No API key required
- ✅ Free
- ⚠️ Requires internet

**Usage:**
```python
from tts import tts_synthesize

audio_path = tts_synthesize(
    text="Hello world",
    engine="gtts",
    language="en"
)
```

### 2. Edge-TTS (Best Quality)
**Installation:**
```bash
pip install edge-tts
```

**Features:**
- ✅ Excellent quality
- ✅ Natural voices
- ✅ Fast generation
- ✅ Free
- ⚠️ Requires internet

**Usage:**
```python
audio_path = tts_synthesize(
    text="Hello world",
    engine="edge-tts",
    voice_id="en-US-JennyNeural"  # Optional
)
```

**Available Voices:**
- `en-US-JennyNeural` - Female, natural (default)
- `en-US-GuyNeural` - Male, professional
- `en-GB-SoniaNeural` - British female
- `en-GB-RyanNeural` - British male
- `en-AU-NatashaNeural` - Australian female

### 3. pyttsx3 (Offline)
**Installation:**
```bash
pip install pyttsx3
```

**Features:**
- ✅ Completely offline
- ✅ Very fast
- ✅ No dependencies
- ⚠️ Lower quality (robotic)

**Usage:**
```python
audio_path = tts_synthesize(
    text="Hello world",
    engine="pyttsx3",
    rate=150  # Optional: speech rate
)
```

### 4. Coqui TTS (Advanced, Optional)
**Installation:**
```bash
pip install TTS
```

**Features:**
- ✅ High quality neural TTS
- ✅ Offline after model download
- ✅ Multiple models available
- ⚠️ Large model downloads (~100-500MB)
- ⚠️ Slower generation

**Usage:**
```python
audio_path = tts_synthesize(
    text="Hello world",
    engine="coqui"
)
```

---

## Troubleshooting

### Issue: "No TTS engine available"
**Solution:**
```bash
pip install gtts  # Install at least one engine
```

### Issue: "gTTS not working" or network errors
**Solution:**
1. Check internet connection
2. Try edge-tts or pyttsx3 as alternative
```bash
pip install pyttsx3  # Offline fallback
```

### Issue: Edge-TTS import errors
**Solution:**
```bash
pip install --upgrade attrs aiohttp certifi
```

### Issue: pyttsx3 no audio output
**Solution:**
- Windows: Check audio drivers are up to date
- Linux: Install espeak: `sudo apt-get install espeak`
- Mac: Should work out of the box

### Issue: Virtual environment corrupted
**Solution:**
```bash
# Delete and recreate venv
rm -rf .venv  # or rmdir /s .venv on Windows
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Performance Tips

### For Long Documents:
1. **Use gTTS or Edge-TTS** (fastest for long text)
2. **Split text into chunks** if > 5000 characters
3. **Use async processing** for multiple files

### For Best Quality:
1. **Use Edge-TTS** (best free option)
2. **Or use Coqui TTS** (if offline needed)
3. **Adjust voice parameters** for Edge-TTS

### For Offline Usage:
1. **Use pyttsx3** (fastest offline)
2. **Or download Coqui models** in advance
3. **Cache processed audio** to avoid re-generation

---

## API Reference

### `tts_synthesize()`
```python
def tts_synthesize(
    text: str,
    engine: str = "gtts",
    language: str = "en",
    rate: Optional[int] = None,
    voice_id: Optional[str] = None,
    basename: str = "speech",
) -> Path:
    """
    Synthesize speech and return path to audio file.
    
    Args:
        text: Text to synthesize
        engine: TTS engine ("gtts", "edge-tts", "pyttsx3", "coqui")
        language: Language code (for gtts)
        rate: Speech rate (for pyttsx3)
        voice_id: Voice ID (for edge-tts, pyttsx3)
        basename: Base name for output file
        
    Returns:
        Path to generated audio file
    """
```

### `list_available_engines()`
```python
def list_available_engines() -> dict:
    """
    Returns dict of all TTS engines with their availability status.
    """
```

### `get_recommended_engine()`
```python
def get_recommended_engine() -> str:
    """
    Returns name of best available TTS engine.
    Priority: gtts > edge-tts > pyttsx3
    """
```

---

## Complete Pipeline Example

```python
from extractor import extract_text
from llm_enrich import enrich_text
from tts import tts_synthesize, get_recommended_engine

# 1. Extract text from document
text = extract_text("document.pdf")

# 2. Enrich with AI (optional)
enriched_text = enrich_text(text)

# 3. Generate audio with best available engine
engine = get_recommended_engine()
audio_path = tts_synthesize(
    text=enriched_text,
    engine=engine,
    basename="my_audiobook"
)

print(f"Audio generated: {audio_path}")
```

---

## Integration with Streamlit App

The TTS module is automatically integrated with the Streamlit UI in `app.py`:

```bash
streamlit run app.py
```

Features:
- Upload document (PDF, image, DOCX)
- Toggle AI enrichment
- Select TTS engine
- Download generated audio

---

## Testing

### Run all TTS tests:
```bash
python tts_comparison.py
```

### Test specific engine:
```bash
python -c "from tts import tts_synthesize; print(tts_synthesize('Test', engine='gtts'))"
```

---

## Next Steps

1. ✅ Install recommended engines (gtts + edge-tts)
2. ✅ Run test script to verify setup
3. ✅ Try pipeline.py with a sample document
4. ✅ Use Streamlit app for interactive testing
5. 🔄 Choose production engine based on requirements

---

## Support & Resources

- **Documentation**: See [TTS_RESEARCH.md](TTS_RESEARCH.md)
- **Code**: See [tts.py](tts.py) and [tts_enhanced.py](tts_enhanced.py)
- **Pipeline**: See [pipeline.py](pipeline.py)
- **Issues**: Check troubleshooting section above

---

**Last Updated**: October 29, 2025
