
import os
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from chronicle_ai.models import Entry
from chronicle_ai.visual_prompts import mood_to_visual, VisualStylePresets
from chronicle_ai.cover_gen import EpisodeCoverGenerator
from chronicle_ai.image_client import ImageGenerator

def generate_samples():
    print("Generating style samples for Art Department...")
    
    # Create a mock entry
    entry = Entry(
        id=999,
        date=datetime.now().strftime("%Y-%m-%d"),
        narrative_text="A lone traveler standing on a cliff overlooking a vast, misty valley at dawn. The sky is painted with soft oranges and deep purples.",
        mood="peaceful"
    )
    
    output_docs = "# Visual Style Presets - Sample Outputs\n\n"
    output_docs += "This document showcases the 5 distinct visual looks available in Chronicle AI.\n\n"
    output_docs += f"**Base Narrative:** 1 traveler on a cliff at dawn, misty valley.\n\n"
    
    styles = ["cinematic", "anime", "noir", "watercolor", "minimalist"]
    
    for style in styles:
        print(f"Processing style: {style}...")
        pos, neg, preset = mood_to_visual.generate_cover_prompt(entry, style_name=style)
        
        output_docs += f"## {style.upper()}\n"
        output_docs += f"**Description:** {preset['description']}\n\n"
        output_docs += "### Prompt Configuration\n"
        output_docs += f"**Positive Prompt:**\n> {pos}\n\n"
        output_docs += f"**Negative Prompt:**\n> {neg}\n\n"
        output_docs += f"**Sampler Settings:** {preset['sampler']}, {preset['steps']} steps\n\n"
        output_docs += "---\n\n"

    docs_path = project_root / "docs" / "STYLE_SAMPLES.md"
    os.makedirs(docs_path.parent, exist_ok=True)
    with open(docs_path, "w") as f:
        f.write(output_docs)
    
    print(f"Documentation generated at: {docs_path}")

if __name__ == "__main__":
    generate_samples()
