"""
Chronicle AI - TTS Test Script
Verify that the TTS engine is working correctly by generating a sample audio snippet.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from chronicle_ai.tts_engine import tts_engine

def test_narration():
    print("🎬 Chronicle AI - TTS Verification")
    print("=" * 40)
    
    sample_text = (
        "The sun dipped below the horizon, casting long, dramatic shadows across the valley. "
        "It was a day of unexpected turns and quiet triumphs. As I closed my journal, "
        "I realized that every small moment was a thread in a much larger tapestry."
    )
    
    print(f"📝 Sample Text: {sample_text[:60]}...")
    
    voices = ["storyteller", "dramatic", "calm"]
    
    for voice in voices:
        print(f"\n🎙️ Testing voice: {voice}...")
        try:
            filename = f"test_verify_{voice}.wav"
            # We use a temp path for verification
            output_path = tts_engine.generate(sample_text, filename, voice_key=voice)
            
            if output_path and os.path.exists(output_path):
                print(f"✅ Success! Generated: {output_path}")
            else:
                print(f"❌ Failed to generate audio for {voice}.")
                print("Note: This script requires 'pip install TTS' to be run first.")
        except Exception as e:
            print(f"❌ Error during generation for {voice}: {e}")

if __name__ == "__main__":
    test_narration()
