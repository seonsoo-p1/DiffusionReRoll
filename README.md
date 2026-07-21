# Diffusion ReRoll project page

Static, GitHub Pages-ready website for:

> **Diffusion ReRoll: Revisable Denoising for Robotic Sequential Prediction**

The layout follows the familiar academic project-page structure popularized by
[Nerfies](https://nerfies.github.io/), with original HTML and CSS tailored to
Diffusion ReRoll.

## Current page flow

1. Title, authors, affiliation, and resource controls
2. Playable project-overview video
3. Overview with the supplied full-sequence, causal, and ReRoll denoising visuals
4. Robotics scope: OGBench planning, LIBERO-10/RoboCasa policy learning, and UWM video–action generation
5. Characteristic failure cases and ReRoll correction
6. Deployment and training schedules, benchmark results, conclusion, and BibTeX

The method figures and animated denoising visuals are the original supplied assets. Supporting
robotics and failure-case stills in `static/images/video/` were derived from the supplied project
video. The page embeds the complete project video and a shorter bidirectional-mode excerpt.

## Preview locally

From this directory:

```bash
python3 -m http.server 8000
```

Then open <http://localhost:8000>.

Run the dependency-free structural check with:

```bash
python3 scripts/check_site.py
node --check static/js/index.js
```

## Content to finalize before publishing

Before publishing:

- replace the disabled Paper and Code controls with public URLs;
- optionally replace the local MP4 with a YouTube embed;
- update the BibTeX entry if a public publication venue becomes available;

The page intentionally does **not** include the confidential manuscript PDF.

## Publish with GitHub Pages

1. Create a repository such as `diffusion-reroll`.
2. Push this directory to its `main` branch.
3. In **Settings → Pages**, select **Deploy from a branch**.
4. Choose `main` and `/ (root)`, then save.

The resulting project URL follows this pattern:

```text
https://USERNAME.github.io/diffusion-reroll/
```
