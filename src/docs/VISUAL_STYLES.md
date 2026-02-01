# 🎨 Visual Style Presets

Chronicle AI supports 5 distinct visual looks for your episode cover art. You can switch between these styles using the CLI.

## How to Configure
To set your preferred style, use the following command:
```bash
chronicle config --style <style_name>
```

Available styles: `cinematic`, `anime`, `noir`, `watercolor`, `minimalist`.

---

## 🎬 CINEMATIC (Default)
**Description:** Film grain, dramatic lighting, realistic photography style.
- **Positive Prompt:** Cinematic film, 35mm, film grain, dramatic lighting, realistic photography...
- **Sampler:** DPM++ 2M Karras
- **Steps:** 30

![Cinematic Example](./styles/cinematic.png)

---

## 🌸 ANIME
**Description:** Studio Ghibli inspired, soft colors, illustrated style.
- **Positive Prompt:** Studio Ghibli style, anime art, soft colors, illustrated, cel shading...
- **Sampler:** Euler a
- **Steps:** 25

![Anime Example](./styles/anime.png)

---

## 🕵️ NOIR
**Description:** Black and white, high contrast, dramatic shadows.
- **Positive Prompt:** Black and white, high contrast, dramatic shadows, film noir, gritty...
- **Sampler:** DPM++ SDE Karras
- **Steps:** 35

![Noir Example](./styles/noir.png)

---

## 🎨 WATERCOLOR
**Description:** Soft, artistic, dreamy, painterly.
- **Positive Prompt:** Watercolor painting, soft artistic edges, dreamy, painterly style...
- **Sampler:** Euler a
- **Steps:** 20

![Watercolor Example](./styles/watercolor.png)

---

## 📐 MINIMALIST
**Description:** Simple shapes, limited palette, clean design.
- **Positive Prompt:** Minimalist design, simple shapes, limited palette, clean lines, flat design...
- **Sampler:** DPM++ 2M Karras
- **Steps:** 25

![Minimalist Example](./styles/minimalist.png)
---

## 🏛️ Visual Identity & Consistency

Chronicle AI employs a `VisualIdentity` system to ensure your episode covers feel like part of a unified series. This includes fixed style tokens, season-specific color palettes, and recurring signature motifs.

### Season Palettes
Each season has a distinct color grade to visually distinguish different "chapters" of your life:
- **Season 1:** Cool blues, deep indigo, silver accents.
- **Season 2:** Warm tones, amber, golden hour glow.
- **Season 3:** Emerald greens, earthy browns, forest mist.
- **Season 4:** Regal purples, crimson, gold filigree.
- **Season 5:** Monochrome neutrals, slate grays, sterile grading.

### Signature Motifs
A subtle visual element is woven into every cover based on the episode's ID:
- Faint glowing geometric crests.
- Crystalline floating particles.
- Anamorphic lens flares.
- Delicate golden threads.

### How to Customize
You can customize the visual identity by editing the `VisualIdentity` class in `src/chronicle_ai/visual_prompts.py`. 

- **To change a season's look:** Update the `SEASON_PALETTES` dictionary.
- **To add new recurring elements:** Modify the `SIGNATURE_MOTIFS` list.
- **To adjust core consistency:** Edit the `CONSISTENCY_TOKENS` string.

### Consistent Seeds
Related episodes within a season use a shared seed prefix. This ensures that the AI's "interpretative lens" remains consistent, preventing wild shifts in how characters or environments are rendered across a season.
