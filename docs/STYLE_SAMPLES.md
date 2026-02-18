# Visual Style Presets - Art Department Documentation

This document showcases the 5 distinct visual looks available in Chronicle AI for episode cover art and posters.

## 1. CINEMATIC
**Description:** Film grain, dramatic lighting, realistic photography style.
- **Positive Prompt Addition:** `cinematic film, 35mm, film grain, dramatic lighting, realistic photography, masterful cinematography, high dynamic range`
- **Negative Prompt Addition:** `cartoon, anime, drawing, illustration, sketch, low contrast, flat lighting, CG, 3d render`
- **Recommended Sampler:** DPM++ 2M Karras (30 steps)

## 2. ANIME
**Description:** Studio Ghibli inspired, soft colors, illustrated style.
- **Positive Prompt Addition:** `studio ghibli style, anime art, soft colors, illustrated, high quality cel shading, whimsical atmosphere, hand-drawn look`
- **Negative Prompt Addition:** `photography, realistic, 3d render, low quality, messy, noisy, dark, gritty`
- **Recommended Sampler:** Euler a (25 steps)

## 3. NOIR
**Description:** Black and white, high contrast, dramatic shadows.
- **Positive Prompt Addition:** `black and white, high contrast, dramatic shadows, film noir, gritty urban setting, moody lighting, 1940s aesthetic, sharp focus`
- **Negative Prompt Addition:** `color, bright, sunny, cheerful, soft, low contrast, modern, futuristic`
- **Recommended Sampler:** DPM++ SDE Karras (35 steps)

## 4. WATERCOLOR
**Description:** Soft, artistic, dreamy, painterly.
- **Positive Prompt Addition:** `watercolor painting, soft artistic edges, dreamy, painterly style, paper texture, fluid brushstrokes, pastel palette, ethereal`
- **Negative Prompt Addition:** `realistic, photography, sharp, hard edges, digital art, neon, high contrast, dark`
- **Recommended Sampler:** Euler a (20 steps)

## 5. MINIMALIST
**Description:** Simple shapes, limited palette, clean design.
- **Positive Prompt Addition:** `minimalist design, simple shapes, limited palette, clean lines, flat design, modern aesthetic, spacious composition, sharp focus`
- **Negative Prompt Addition:** `cluttered, detailed, busy, realistic, complex textures, messy, dark, gritty`
- **Recommended Sampler:** DPM++ 2M Karras (25 steps)

---

### Implementation Details

The `MoodToVisualPrompt` system automatically maps detected moods to these styles, applying visual identity layers (season palettes, consistent motifs) to maintain cohesive aesthetics across the entire Chronicle.

**Test Coverage:**
- Comprehensive unit tests for prompt generation.
- Integration tests for full cover generation pipeline.
- Fallback system validation (gradient generation when SD is offline).
- Storage organization and thumbnail verification.
- Cover history and regeneration logic.
