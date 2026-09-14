#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo"
DIST_DIR="/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/dist"
COMMIT_MSG="${1:-Update Dublin Pub Crawl site and agent customizations}"

echo "=== [1/5] Running Pub Directory Sync ==="
python3 "$REPO_DIR/_agents/skills/pub-directory-sync/scripts/sync_pages.py" --repo-dir "$REPO_DIR" --dist-dir "$DIST_DIR"

echo "=== [2/5] Running SEO & Sitemap Validator ==="
python3 "$REPO_DIR/_agents/skills/seo-sitemap-validator/scripts/validate_seo.py" --repo-dir "$REPO_DIR"

echo "=== [3/5] Syncing files to dist/ ==="
cp -f "$REPO_DIR/index.html" "$DIST_DIR/index.html"
cp -f "$REPO_DIR/CNAME" "$DIST_DIR/CNAME"
cp -f "$REPO_DIR/sitemap.xml" "$DIST_DIR/sitemap.xml"
cp -f "$REPO_DIR/AGENTS.md" "$DIST_DIR/AGENTS.md"

echo "=== [4/5] Staging, Committing, and Pushing to GitHub (origin/main) ==="
cd "$REPO_DIR"
git add -A
if git diff --cached --quiet; then
  echo "No new changes to commit."
else
  git commit -m "$COMMIT_MSG"
  git push origin main
fi

echo "=== [5/5] Verifying Live Endpoints (HTTP 200 OK) ==="
for url in "https://dublinpubcrawl.app/" "https://dublinpubcrawl.app/routes/" "https://dublinpubcrawl.app/pubs/"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  echo "  $url -> HTTP $code"
done
echo "=== Deployment Complete! ==="
