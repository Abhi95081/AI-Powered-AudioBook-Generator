"""
Complete Document-to-Audio Pipeline

Processes documents through the full pipeline:
1. Extract text from PDF/image/DOCX
2. Enrich text with Gemini AI (optional)
3. Generate high-quality audio with TTS

Usage:
    python pipeline.py input.pdf --enrich --engine gtts
    python pipeline.py image.png --engine edge-tts
"""
import argparse
import sys
from pathlib import Path

# Import pipeline modules
from extractor import extract_text
from llm_enrich import enrich_text
from tts import tts_synthesize, list_available_engines, get_recommended_engine
from utils import write_text_file


def run_pipeline(
    input_file: str,
    enrich: bool = False,
    tts_engine: str = "gtts",
    output_dir: str = "outputs",
) -> dict:
    """
    Run complete document-to-audio pipeline.
    
    Returns:
        dict with paths to extracted text, enriched text (if applicable), and audio
    """
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    print("=" * 70)
    print("AI AUDIOBOOK GENERATOR - COMPLETE PIPELINE")
    print("=" * 70)
    print(f"Input: {input_path.name}")
    print(f"Enrichment: {'Yes' if enrich else 'No'}")
    print(f"TTS Engine: {tts_engine}")
    print("=" * 70)
    
    results = {}
    
    # Step 1: Extract text
    print("\n[1/3] Extracting text...")
    try:
        extracted_text = extract_text(str(input_path))
        if not extracted_text.strip():
            raise ValueError("No text extracted from document")
        
        # Save extracted text
        text_filename = f"{input_path.stem}_extracted.txt"
        text_path = write_text_file(extracted_text, text_filename)
        results["extracted_text"] = text_path
        
        word_count = len(extracted_text.split())
        print(f"✓ Extracted {word_count} words")
        print(f"  Saved to: {text_path}")
        
    except Exception as e:
        print(f"✗ Text extraction failed: {e}")
        return results
    
    # Step 2: Enrich text (optional)
    final_text = extracted_text
    if enrich:
        print("\n[2/3] Enriching text with AI...")
        try:
            enriched_text = enrich_text(extracted_text)
            if enriched_text and enriched_text != extracted_text:
                final_text = enriched_text
                
                # Save enriched text
                enriched_filename = f"{input_path.stem}_enriched.txt"
                enriched_path = write_text_file(enriched_text, enriched_filename)
                results["enriched_text"] = enriched_path
                
                word_count = len(enriched_text.split())
                print(f"✓ Enriched to {word_count} words")
                print(f"  Saved to: {enriched_path}")
            else:
                print("⚠ Enrichment returned no changes, using original text")
                
        except Exception as e:
            print(f"⚠ Enrichment failed: {e}")
            print("  Continuing with extracted text...")
    else:
        print("\n[2/3] Skipping enrichment (disabled)")
    
    # Step 3: Generate audio
    print("\n[3/3] Generating audio...")
    try:
        # Limit text length for TTS (some engines have limits)
        max_chars = 5000
        if len(final_text) > max_chars:
            print(f"⚠ Text is long ({len(final_text)} chars), using first {max_chars} chars")
            final_text = final_text[:max_chars] + "..."
        
        audio_path = tts_synthesize(
            text=final_text,
            engine=tts_engine,
            basename=input_path.stem,
        )
        results["audio"] = audio_path
        
        audio_size = audio_path.stat().st_size / 1024  # KB
        print(f"✓ Audio generated ({audio_size:.1f} KB)")
        print(f"  Saved to: {audio_path}")
        
    except Exception as e:
        print(f"✗ Audio generation failed: {e}")
        return results
    
    # Summary
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE!")
    print("=" * 70)
    print(f"Text:  {results.get('extracted_text', 'N/A')}")
    if "enriched_text" in results:
        print(f"Enriched: {results['enriched_text']}")
    print(f"Audio: {results.get('audio', 'N/A')}")
    print("=" * 70)
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="AI Audiobook Generator - Document to Audio Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic: PDF to audio
  python pipeline.py document.pdf
  
  # With AI enrichment
  python pipeline.py document.pdf --enrich
  
  # Choose TTS engine
  python pipeline.py image.png --engine edge-tts
  
  # Full pipeline with enrichment
  python pipeline.py book.pdf --enrich --engine gtts

Supported formats: PDF, PNG, JPG, JPEG, DOCX, TXT
        """
    )
    
    parser.add_argument(
        "input_file",
        help="Path to input document (PDF, image, DOCX, or TXT)",
    )
    
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Enable AI text enrichment with Gemini (requires API key)",
    )
    
    # List available engines
    engines = list_available_engines()
    available_engine_names = [name for name, info in engines.items() if info["available"]]
    
    parser.add_argument(
        "--engine",
        choices=available_engine_names if available_engine_names else ["gtts"],
        default=get_recommended_engine() if available_engine_names else "gtts",
        help=f"TTS engine to use (available: {', '.join(available_engine_names) if available_engine_names else 'gtts'})",
    )
    
    parser.add_argument(
        "--list-engines",
        action="store_true",
        help="List all TTS engines and their status",
    )
    
    args = parser.parse_args()
    
    # List engines if requested
    if args.list_engines:
        print("\n" + "=" * 70)
        print("AVAILABLE TTS ENGINES")
        print("=" * 70)
        engines = list_available_engines()
        for name, info in engines.items():
            status = "✓ Available" if info["available"] else "✗ Not installed"
            print(f"\n{name}")
            print(f"  Status: {status}")
            print(f"  Quality: {info['quality']}")
            print(f"  Speed: {info['speed']}")
            print(f"  Type: {info['type']}")
            print(f"  Notes: {info['notes']}")
        print("=" * 70)
        return 0
    
    # Check if any TTS engine is available
    if not available_engine_names:
        print("ERROR: No TTS engines available!")
        print("\nInstall at least one:")
        print("  pip install gtts          # Simple, reliable (recommended)")
        print("  pip install edge-tts       # High quality, natural voices")
        print("  pip install pyttsx3        # Offline, lower quality")
        return 1
    
    # Run pipeline
    try:
        results = run_pipeline(
            input_file=args.input_file,
            enrich=args.enrich,
            tts_engine=args.engine,
        )
        
        if "audio" in results:
            return 0
        else:
            print("\n⚠ Pipeline incomplete - check errors above")
            return 1
            
    except Exception as e:
        print(f"\n✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
