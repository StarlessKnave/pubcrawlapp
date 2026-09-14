# AGENTS.md — Dublin Pub Crawl Architecture & Deployment Rules

This repository powers **Dublin Pub Crawl** (`https://dublinpubcrawl.app/`), an interactive Dublin pub guide, crawl builder, and 118-pub directory with curated routes and the Guinness Stout Score™ evaluation engine.

---

## 1. Visual Identity & Design System ("Guinness Storehouse Aesthetic")

All UI components, pub pages, route pages, and modals MUST strictly follow the Guinness Storehouse dark-mode palette and typography:

- **Primary Background**: `#0a0406` (`bg-[#0a0406]`) — Deep stout black.
- **Elevated Surface / Card**: `#140d0f` (`bg-[#140d0f]`) — Warm roasted malt surface.
- **Primary Gold Accent**: `#d9ac5e` (`text-[#d9ac5e]`, `border-[#d9ac5e]`) — Signature harp gold.
- **Cream Foam Text**: `#f5ead8` (`text-[#f5ead8]`) — Crisp nitro head cream.
- **Muted / Secondary Text**: `#cbbca2` (`text-[#cbbca2]`).
- **Display Typography**: `--font-knockout` (Oswald / uppercase condensed tracking) for headers and titles.
- **Body Typography**: `--font-gotham` (Montserrat / Plus Jakarta Sans) for readable descriptions and metadata.
- **Pub Directory Title Styling**: The main Pub Directory header MUST always render as **"Dublin Pub Crawl <span style="color: #d9ac5e;">Directory</span>"** with "Directory" highlighted in `#d9ac5e` gold.

---

## 2. Mobile UI & Modal Safety Rules

To prevent top cutoff and viewport clipping on iOS Safari and Android Chrome:

1. **Modal Outer Wrapper**: Every modal overlay (`fixed inset-0`) MUST include:
   - `.modal-mobile-safe` class
   - `items-start sm:items-center` (aligns to top with safe-area padding on mobile, vertically centers on `sm:` and larger screens)
   - `overflow-y-auto`
2. **Safe-Area Top Clearance**: `.modal-mobile-safe` uses `padding-top: max(1rem, env(safe-area-inset-top, 0px))` and `max-height: 100dvh` so close buttons and headers are never clipped under mobile status bars or notches.
3. **Touch Targets**: All interactive buttons, filter pills, and close buttons (`×`) must maintain a minimum touch area of `44px × 44px`.

---

## 3. Strict Canonical URL & SEO Architecture

1. **Root Domain (`non-www`)**: The canonical domain is strictly **`https://dublinpubcrawl.app/`** (never `www.dublinpubcrawl.app`).
   - `CNAME` file in the repository root and `dist/CNAME` MUST always contain exactly `dublinpubcrawl.app`.
2. **Trailing Slashes**: All directory and subpage URLs MUST end with a trailing slash `/` (e.g., `https://dublinpubcrawl.app/pubs/the-stags-head/`).
3. **Canonical Tags & Sitemap Synchronization**:
   - Every page's `<link rel="canonical" href="...">` and `<meta property="og:url" content="...">` must match its exact `https://dublinpubcrawl.app/.../` URL in `sitemap.xml`.
   - Total indexed pages in `sitemap.xml`: **136 pages** (Home, `/routes/`, `/pubs/`, 15 route subpages, and 118 individual pub subpages).

---

## 4. Mandatory `<5` Iteration Pre-Deployment Critic Loop

Before executing **ANY** deployment (`git push`, running `_agents/skills/github-one-click-deploy/scripts/deploy.sh`, or syncing to production):

1. **Invoke `Critic-PreDeploy`**: You MUST run the **`Critic-PreDeploy`** subagent (or run the automated pre-deploy validation suite) to audit all staged/pending changes.
2. **Iterative Quality Gate (`< 5` Iterations)**:
   - Each iteration inspects:
     1. **HTML & DOM Integrity**: Balanced tags (`<div>`, `<header>`, `<section>`, `<script>`), no orphaned closing tags.
     2. **Canonical & CNAME Compliance**: Zero `www.dublinpubcrawl.app` leaks; `CNAME` is strictly `dublinpubcrawl.app`; all 136 URLs in `sitemap.xml` are valid.
     3. **Mobile Modal Safety**: All modal overlays retain `.modal-mobile-safe` and `items-start sm:items-center`.
     4. **Brand & Typography Consistency**: Guinness Storehouse palette (`#0a0406`, `#d9ac5e`) and gold "Directory" span in pub headers.
   - If `Critic-PreDeploy` reports any **CRITICAL** or **HIGH** findings, fix them immediately and re-run `Critic-PreDeploy`.
   - Maximum loop bound: **`< 5` iterations** (max 4 fix cycles).
   - **Deployment is strictly blocked** until `Critic-PreDeploy` outputs:
     `STATUS: APPROVED (0 critical findings)`.
