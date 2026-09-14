---
name: pub-directory-sync
description: Synchronize shared headers, footers, navigation links, canonical tags, and brand styling across all 118 Dublin pub subpages (pubs/*/index.html) and 15 route subpages (routes/*/index.html). Use whenever updating navigation menus, directory headers, canonical domain settings, or global UI components across the static directory.
---

# Pub & Route Directory Sync Skill

This skill ensures all **118 pub pages** (`pubs/*/index.html`), the **main pub directory** (`pubs/index.html`), and all **15 route pages** (`routes/*/index.html`) stay 100% synchronized with the global design system and canonical URLs.

## When to Use
- Updating header titles or navigation bar links across all pub/route pages.
- Applying global styling updates (e.g., Guinness Storehouse dark palette `#0a0406` and `#d9ac5e` gold highlights).
- Enforcing non-www canonical URLs (`https://dublinpubcrawl.app/`) across all 136 pages.
- Synchronizing changes between `scratch/github_repo/` and `dist/`.

## Helper Script Usage

Run the automated directory synchronization script:

```bash
python3 /usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo/_agents/skills/pub-directory-sync/scripts/sync_pages.py
```

### Supported Flags
- `--repo-dir <path>`: Path to `scratch/github_repo` (defaults to the workspace repo).
- `--dist-dir <path>`: Path to `dist/` directory to mirror updates.
- `--dry-run`: Preview changes without writing files.

## Checklist
1. Verify that `Dublin Pub Crawl <span style="color: #d9ac5e;">Directory</span>` is present on `pubs/index.html` and all pub subpage headers.
2. Confirm every page has a valid `<link rel="canonical" href="https://dublinpubcrawl.app/.../">` with a trailing slash.
3. Run `seo-sitemap-validator` after any batch update.
