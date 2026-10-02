# Diffusion ReRoll project page

Static, GitHub Pages-ready website for **Diffusion ReRoll: Revisable Denoising for
Robotic Sequential Prediction**, accepted at **CoRL 2026 (Spotlight)**.

## Current page flow

1. Title, acceptance notice, authors, and resources
2. Project-overview video
3. Full-sequence, causal, and ReRoll denoising overview
4. Robotics scope: OGBench, policy learning, UWM, and real-world navigation
5. Failure cases, method, and bidirectional denoising
6. Four result comparisons and the updated ReRoll-event ablation
7. Real-world navigation: 15× example and annotated clockwise/counterclockwise comparisons
8. Conclusion and BibTeX

## Preview and validate

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000>. The navigation comparisons offer grouped play, pause,
and restart, alongside each video's native controls. Finished clips hold their last
frame while longer clips continue. Videos do not autoplay.

```bash
python3 scripts/check_site.py
node --check static/js/index.js
```

## Media and result provenance

The September 2026 update uses `data/Diffusion_ReRoll_AfterRebuttal.pdf` and
`static/media/Compressed_Overview_ForLooking.mp4` as reference material. The Paper
button retains `data/DiffusionReRoll.pdf` until the final paper is ready.

The overview player uses `static/images/video/ReRoll_NewVid_web.mp4`, a 1080p web
copy of the October 2026 upload `static/images/video/ReRoll_NewVid.mp4`. The original
upload stays local. The web copy preserves its full duration and audio, with H.264
video (CRF 22) and faststart for browser playback.

The four summary charts match the updated overview and paper (full-sequence,
Forcing, ReRoll, respectively):

| Setting | Success (%) | Paper source |
| --- | --- | --- |
| OGBench guidance average | 38.4 / 72.8 / 88.1 | Table 1 |
| LIBERO-10 official average | 40.1 / 49.1 / 62.7 | Table 2 |
| UWM OOD joint policy | 58.1 / 60.7 / 69.7 | Table 4 |
| Navigation CW/CCW average | 0.0 / 22.2 / 72.2 | Figure 13 |

The navigation summary averages Figure 13's circuit means equally across clockwise
and counterclockwise directions. The separate navigation-results plot is not shown
on the page. The event ablation uses the supplied
`static/media/UpdatedResult_ReRollEvents.png`; failure illustrations use
`static/images/Full2.png` and `static/images/forcing2.png`.

The seven navigation originals are preserved in `static/media/NavigationVid/`.
Web copies are in `static/media/navigation/`, with posters in
`static/images/navigation/`. To regenerate them (requires FFmpeg and FFprobe):

```bash
python3 scripts/prepare_navigation_media.py
```

The six fixed-camera clips crop to the course and retain their baked-in 5× speed.
Full-sequence and Forcing clips include timed circles highlighting failures, matching
the reference overview. The clockwise full-sequence clip omits its last 0.8 seconds
to stop before the reversal after failure. Other clips retain their original duration;
the moving-camera 15× example also retains its full frame. The manifest records
source paths, crops, edits, dimensions, durations, and frame counts. All web videos
use silent H.264 MP4 with faststart.

## Publishing

The page is ready for GitHub Pages from the repository root. Add a public Code URL
when available. Update the Paper target when the final paper is ready. Source
edits alone do not publish the site.

The layout follows the academic project-page structure popularized by
[Nerfies](https://nerfies.github.io/), with original HTML and CSS.
