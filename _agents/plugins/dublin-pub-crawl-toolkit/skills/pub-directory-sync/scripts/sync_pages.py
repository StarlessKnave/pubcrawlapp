#!/usr/bin/env python3
"""Synchronize shared headers, canonical URLs, and brand spans across all 136 pages."""

import argparse
import glob
import os
import re
import shutil

DEFAULT_REPO = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo"
DEFAULT_DIST = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/dist"


def sync_file(filepath: str, dry_run: bool = False) -> bool:
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    updated = original
    # 1. Enforce non-www canonical URLs
    updated = updated.replace("https://www.dublinpubcrawl.app", "https://dublinpubcrawl.app")

    # 2. Enforce Dublin Pub Crawl <span style="color: #d9ac5e;">Directory</span> in headers
    updated = re.sub(
        r"Dublin Pub Crawl Directory(?!</span>)",
        'Dublin Pub Crawl <span style="color: #d9ac5e;">Directory</span>',
        updated,
    )

    if updated != original:
        if not dry_run:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(updated)
        return True
    return False


def main():
    parser = argparse.ArgumentParser(description="Synchronize Dublin Pub Crawl directory pages.")
    parser.add_argument("--repo-dir", default=DEFAULT_REPO, help="Path to git repository root")
    parser.add_argument("--dist-dir", default=DEFAULT_DIST, help="Path to dist directory")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    args = parser.parse_args()

    html_files = glob.glob(os.path.join(args.repo_dir, "**/*.html"), recursive=True)
    changed_count = 0

    for html_file in sorted(html_files):
        if sync_file(html_file, dry_run=args.dry_run):
            changed_count += 1
            rel_path = os.path.relpath(html_file, args.repo_dir)
            dist_target = os.path.join(args.dist_dir, rel_path)
            if not args.dry_run and os.path.exists(os.path.dirname(dist_target)):
                shutil.copy2(html_file, dist_target)

    print(f"[pub-directory-sync] Scanned {len(html_files)} HTML pages. Updated {changed_count} files.")


if __name__ == "__main__":
    main()
