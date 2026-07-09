# Research UI Walkthrough (GIF/Video Script)

Use this script to capture a short GIF/video (~60s) demonstrating autonomous research mode:

1) Open `http://localhost:8000/chat`.
2) Toggle 🔬 Research, open ⚙️ settings, show coverage threshold, max queries, cost cap.
3) Send: “Latest Qdrant performance benchmarks”. Keep research enabled.
4) During response, highlight progress HUD stages and cancel button (let it finish).
5) Show gap analysis card (coverage/recency/coherence bars) and research summary card.
6) Hover researched source chips to show ✨ provenance tooltip and click to reveal timeline.
7) Open history panel: adjust window filter, export CSV, point to charts.
8) On mobile viewport (dev tools), show swipe gesture on history list and collapsed insights.
9) Demonstrate accessibility: focus ring on controls; mention reduced-motion/high-contrast toggles (OS settings).

Capture tips:
- Use 1280×720 for desktop, 390×844 for mobile clip.
- Keep cursor motions deliberate; zoom to settings and history panels briefly.
- Export GIF to `docs/media/research-ui-walkthrough.gif` (~8–12 MB) and MP4 to `docs/media/research-ui-walkthrough.mp4`.

Narration (optional):
- “Gap detected → research triggered; HUD shows stages.”
- “Sources marked with ✨ were researched now; hover for provenance, click for timeline.”
- “History/analytics show sessions, cost, and gap distribution; CSV export available.”
