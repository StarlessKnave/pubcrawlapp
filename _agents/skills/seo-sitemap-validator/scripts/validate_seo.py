#!/usr/bin/env python3
"""Validate SEO canonicals, sitemap.xml (136 pages), CNAME, and HTML tag balance."""

import argparse
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET

DEFAULT_REPO = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo"


def validate_repo(repo_dir: str) -> int:
    errors = []
    warnings = []

    # 1. Check CNAME
    cname_path = os.path.join(repo_dir, "CNAME")
    if not os.path.exists(cname_path):
        errors.append("Missing CNAME file in repository root.")
    else:
        with open(cname_path, "r", encoding="utf-8") as f:
            cname = f.read().strip()
        if cname != "dublinpubcrawl.app":
            errors.append(f"CNAME must be 'dublinpubcrawl.app', found '{cname}'.")

    # 2. Parse sitemap.xml
    sitemap_path = os.path.join(repo_dir, "sitemap.xml")
    sitemap_urls = set()
    if not os.path.exists(sitemap_path):
        errors.append("Missing sitemap.xml in repository root.")
    else:
        try:
            tree = ET.parse(sitemap_path)
            root = tree.getroot()
            ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            for loc in root.findall(".//sm:loc", ns):
                url = (loc.text or "").strip()
                sitemap_urls.add(url)
                if "www.dublinpubcrawl.app" in url:
                    errors.append(f"sitemap.xml contains www URL: {url}")
        except Exception as e:
            errors.append(f"Failed to parse sitemap.xml: {e}")

    # 3. Inspect all HTML files
    html_files = sorted(glob.glob(os.path.join(repo_dir, "**/*.html"), recursive=True))
    for html_file in html_files:
        rel_path = os.path.relpath(html_file, repo_dir)
        # Skip files inside _agents/
        if rel_path.startswith("_agents/"):
            continue

        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for www. leaks
        if "www.dublinpubcrawl.app" in content:
            errors.append(f"[{rel_path}] Contains forbidden 'www.dublinpubcrawl.app' reference.")

        # Check canonical tag
        canon_match = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']', content)
        if not canon_match:
            warnings.append(f"[{rel_path}] Missing <link rel='canonical'> tag.")
        else:
            canon_url = canon_match.group(1)
            if not canon_url.startswith("https://dublinpubcrawl.app/"):
                errors.append(f"[{rel_path}] Invalid canonical URL: {canon_url}")

        # Validate all Schema.org JSON-LD blocks parse cleanly with json.loads()
        ld_blocks = re.findall(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            content,
            re.DOTALL | re.IGNORECASE,
        )
        for ld_idx, ld_body in enumerate(ld_blocks):
            try:
                import json as _json
                _json.loads(ld_body)
            except Exception as e:
                errors.append(f"[{rel_path}] Invalid Schema.org JSON-LD block #{ld_idx + 1}: {e}")

        # Check tag balance on index.html
        if rel_path == "index.html":
            for tag in ["div", "header", "section", "script"]:
                opens = len(re.findall(rf"<{tag}\b", content))
                closes = len(re.findall(rf"</{tag}>", content))
                if opens != closes:
                    errors.append(f"[{rel_path}] Unbalanced <{tag}> tags: {opens} opens vs {closes} closes.")
            if "modal-mobile-safe" not in content:
                errors.append(f"[{rel_path}] Missing '.modal-mobile-safe' mobile modal safety class.")
            # Ensure no modal-mobile-safe element has both 'hidden' and 'flex' simultaneously (which breaks .modal-mobile-safe.flex { display: flex !important })
            for m_tag in re.findall(r'<[^>]+class=["\'][^"\']*modal-mobile-safe[^"\']*["\'][^>]*>', content):
                cls_attr = re.search(r'class=["\']([^"\']+)["\']', m_tag)
                if cls_attr:
                    classes = cls_attr.group(1).split()
                    if "hidden" in classes and "flex" in classes:
                        errors.append(f"[{rel_path}] Modal has both 'hidden' and 'flex' in initial classes (blocks screen on load!): {m_tag[:90]}...")

    print(f"=== SEO & Sitemap Validation Summary ===")
    print(f"HTML files scanned : {len(html_files)}")
    print(f"Sitemap URLs count : {len(sitemap_urls)}")
    print(f"Warnings           : {len(warnings)}")
    print(f"Critical Errors    : {len(errors)}")

    for w in warnings[:5]:
        print(f"  [WARN] {w}")
    for e in errors:
        print(f"  [ERROR] {e}")

    if errors:
        print("STATUS: FAILED")
        return 1
    print("STATUS: PASSED (0 critical findings)")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir", default=DEFAULT_REPO)
    args = parser.parse_args()
    sys.exit(validate_repo(args.repo_dir))
