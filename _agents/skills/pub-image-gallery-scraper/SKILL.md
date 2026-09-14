---
name: pub-image-gallery-scraper
description: Scrapes and curates Wikimedia Commons and Google Business Profile photo links for all 118 Dublin pubs, and injects interactive 3-photo galleries into the map pin popup menu (index.html), the Pub Directory cards (pubs/index.html), and individual pub subpages (pubs/*/index.html).
---

# Pub Image Gallery Scraper & Curator Skill (`pub-image-gallery-scraper`)

This skill builds and embeds interactive **3-Photo Galleries** (`Exterior Facade`, `Historic Snug & Interior`, and `Signature Guinness Stout`) with direct **Google Business Profile Photo Feeds** across all 118 Dublin pubs.

## Where Galleries Are Embedded
1. **Pub Pin Menu (`index.html`)**:
   - Inside `renderPubDetailPopup(pub)` when a user taps any map pin.
   - Includes interactive thumbnail switching, left/right controls, a full-screen `.modal-mobile-safe` Lightbox, and a direct **"📸 Google Business Profile Photos ↗"** link.
2. **Pub Directory (`pubs/index.html`)**:
   - Embedded at the top of all 118 `.pub-card` elements with interactive 3-photo switcher pills and a Google Business Profile photo link.
3. **Pub Subpages (`pubs/*/index.html`)**:
   - Adds a dedicated **Photo Gallery & Google Business Profile** section above the FAQ accordion on all 118 pub pages.

## Usage

Run the automated gallery builder and injector:

```bash
python3 /usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo/_agents/skills/pub-image-gallery-scraper/scripts/fetch_and_inject_pub_galleries.py
```
