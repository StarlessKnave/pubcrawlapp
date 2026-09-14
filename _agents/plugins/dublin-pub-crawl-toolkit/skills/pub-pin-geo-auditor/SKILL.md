---
name: pub-pin-geo-auditor
description: Audits and fixes Dublin pub GPS coordinates and map pin locations across index.html (DUBLIN_PUBS), pubs/index.html (data-lat/data-lng), and all 118 pub subpages (pubs/*/index.html JSON-LD GeoCoordinates and walking directions). Use whenever a pub map pin is out of place, has low precision, or when adding/verifying pub locations.
---

# Pub Map Pin & Geolocation Auditor Skill (`pub-pin-geo-auditor`)

This skill audits all **118 Dublin pubs** across the interactive map (`index.html`), the Pub Directory (`pubs/index.html`), and individual pub pages (`pubs/*/index.html`) against OpenStreetMap Nominatim and verified ground-truth Eircode/building coordinates.

## What It Fixes
1. **Displaced or Approximate Pins**: Detects any pub whose stored `lat`/`lng` has low precision ($\le 4$ decimal places) or deviates from its verified Dublin street address / Eircode.
2. **Cross-File Coordinate Desynchronization**: Ensures that a pub's coordinates in:
   - `index.html` (`let DUBLIN_PUBS = [...]`)
   - `pubs/index.html` (`data-lat` and `data-lng` attributes on `.pub-card` elements)
   - `pubs/<slug>/index.html` (`@graph` $\rightarrow$ `BarOrPub` $\rightarrow$ `geo: { latitude, longitude }`, `hasMap` walking link, and FAQ text)
   - `dist/` build artifacts
   are **100% synchronized** to 6 decimal places ($\approx 11\text{cm}$ precision).

## Usage

Run the automated pin auditor and ground-truth synchronization script:

```bash
python3 /usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo/_agents/skills/pub-pin-geo-auditor/scripts/audit_and_fix_pins.py --apply
```

### Flags
- `--audit-only`: Inspect and report displaced pins without writing changes.
- `--apply`: Update all displaced pins across `index.html`, `pubs/index.html`, `pubs/*/index.html`, and `dist/`.
- `--live-nominatim`: Query OpenStreetMap Nominatim API (`nominatim.openstreetmap.org`) for any new or unverified pub addresses.
