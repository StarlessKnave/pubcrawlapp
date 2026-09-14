---
name: github-one-click-deploy
description: Automated pre-deployment validation, <5 iteration Critic-PreDeploy inspection gate, dist/ sync, Git commit, GitHub Pages push, and live HTTP 200 verification for dublinpubcrawl.app. Use whenever deploying changes to GitHub Pages.
---

# GitHub One-Click Deploy Skill (with `<5` Critic Inspection Loop)

This skill orchestrates safe, verified deployments of `dublinpubcrawl.app` to GitHub Pages (`main` branch).

## Mandatory Pre-Deployment Protocol (`<5` Iteration Critic Loop)

Before executing `scripts/deploy.sh` or `git push origin main`:
1. **Run `Critic-PreDeploy`**: The agent MUST invoke the `Critic-PreDeploy` subagent to inspect all pending changes (up to `<5` iterations).
2. **Gate Check**: Deployment proceeds ONLY when `Critic-PreDeploy` outputs `STATUS: APPROVED (0 critical findings)`.

## Deployment Script

Run the deployment script with `BypassSandbox: true`:

```bash
bash /usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo/_agents/skills/github-one-click-deploy/scripts/deploy.sh "Commit message describing the update"
```

### What `deploy.sh` Executes
1. Runs `pub-directory-sync/scripts/sync_pages.py` to ensure all 136 pages and headers match.
2. Runs `seo-sitemap-validator/scripts/validate_seo.py` to verify zero canonical or DOM errors.
3. Mirrors updated files to `/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/dist/`.
4. Stages all changes (`git add -A`), commits with the provided message, and pushes to `origin main`.
5. Verifies live HTTP 200 OK status on `https://dublinpubcrawl.app/`, `https://dublinpubcrawl.app/routes/`, and `https://dublinpubcrawl.app/pubs/`.
