# Dublin Pub Crawl Toolkit (`dublin-pub-crawl-toolkit`)

Official Jetski plugin for **Dublin Pub Crawl** (`https://dublinpubcrawl.app/`).

## Bundled Customizations

### Rules (`rules/AGENTS.md`)
- Guinness Storehouse dark palette (`#0a0406` background, `#d9ac5e` gold, `#f5ead8` cream).
- Mobile modal safety (`.modal-mobile-safe` + `items-start sm:items-center`).
- Non-www canonical domain (`https://dublinpubcrawl.app/`).
- Mandatory `<5` iteration `Critic-PreDeploy` inspection loop before any deployment.

### Skills (`skills/`)
1. **`pub-directory-sync`**: Synchronize shared headers, gold "Directory" spans, and canonical URLs across all 136 pages.
2. **`seo-sitemap-validator`**: Audit `CNAME`, `sitemap.xml` (136 pages), canonical tags, and HTML DOM tag balance.
3. **`github-one-click-deploy`**: Automated validation, `<5` iteration Critic loop check, `dist/` sync, Git commit/push, and live HTTP 200 verification.

### Subagents (`agents/`)
1. **`SEO-Auditor`**: Technical SEO & Schema.org structured data auditor.
2. **`Dublin-Pub-Curator`**: Historian & Guinness Stout Score™ curator.
3. **`Mobile-UI-Inspector`**: Mobile viewport & touch-target inspector.
4. **`Critic-PreDeploy`**: Adversarial pre-deployment quality gate (`<5` iteration loop).
