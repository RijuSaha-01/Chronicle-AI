
import os
import sys
from pathlib import Path

# Add src to sys.path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from chronicle_ai.audio_generator import audio_generator
from chronicle_ai.repository import get_repository
from chronicle_ai.models import Entry

def generate_samples():
    repo = get_repository()
    
    samples = [
        {
            "title": "Adventurous Exploration",
            "mood": "adventurous",
            "text": "### Introduction\nThe sun rose over the jagged peaks of the Forbidden Mountains. I knew this day would be unlike any other. My boots crunched against the frost-covered gravel as I reached the edge of the chasm.\n\n### Act 1: The Descent\n--- \nScaling down the vertical cliff face was a test of pure nerves. Every grip felt precarious, every breath a prayer to the gods of gravity. But as I reached the hidden cave entrance, the sparkle of ancient crystals made it all worth it."
        },
        {
            "title": "Midnight Shadows",
            "mood": "mysterious",
            "text": "### Cold Open\nFog rolled through the alleyways of Old Town, thick as wool. A single lamp flickered, casting long, dancing shadows against the brickwork. I heard the footsteps before I saw the figure.\n\n### Act 1: The Encounter\n--- \nThey stood there, holding a parcel wrapped in oilskin. No words were spoken. The exchange was swift, almost spectral. By the time I turned around to ask for a name, the fog had swallowed them whole."
        },
        {
            "title": "Morning Reflection",
            "mood": "reflective",
            "text": "### Opening\nThe steam from my coffee mingled with the morning mist. Silence is a rare gift in this city, and I intended to savor every second of it. \n\n### Act 1: Inner Peace\n--- \nLooking back at the last decade, the triumphs feel smaller, the failures less sharp. It is the quiet moments like these that define the architecture of a life. I am content, for now, to just exist."
        }
    ]
    
    print("🚀 Generating sample audio for 3 episodes...")
    
    for i, sample in enumerate(samples):
        # Create a temporary entry
        entry = Entry(
            id=1000 + i,
            title=sample["title"],
            mood=sample["mood"],
            narrative_text=sample["text"],
            date="2026-03-16"
        )
        repo.create_entry(entry)
        
        print(f"🎙️ Processing '{sample['title']}' (Mood: {sample['mood']})...")
        try:
            path = audio_generator.generate_audio(entry.id)
            if path:
                print(f"✅ Success: {path}")
            else:
                print(f"❌ Failed to generate audio for {sample['title']}")
        except Exception as e:
            print(f"❌ Error generating {sample['title']}: {e}")

if __name__ == "__main__":
    generate_samples()
