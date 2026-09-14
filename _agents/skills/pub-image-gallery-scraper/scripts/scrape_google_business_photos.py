#!/usr/bin/env python3
"""
Scrape real Google Business Profile photos (lh3.googleusercontent.com/gps-cs-s/... and streetviewpixels-pa.googleapis.com)
directly from Google Maps for all 118 Dublin pubs.
"""

import concurrent.futures
import json
import os
import re
import time
import urllib.parse
import urllib.request

REPO_DIR = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo"
DATA_DIR = os.path.join(REPO_DIR, "_agents/skills/pub-image-gallery-scraper/data")
OUT_JSON = os.path.join(DATA_DIR, "google_business_profile_photos.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Cookie": "SOCS=CAISHAgBEhJnd3NfMjAyMzA4MTUtMF9SQzIaAmVuIAEaBgiA_LyaBg",
}


def scrape_pub_gbp_photos(pub):
    pid = pub["id"]
    name = pub["name"]
    addr = pub.get("address", "Dublin")
    query = f"{name}, {addr}, Dublin"
    search_url = "https://www.google.com/maps/search/" + urllib.parse.quote(query)

    photos = []
    try:
        req = urllib.request.Request(search_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        m = re.search(r'href="(/search\?tbm=map[^"]+)"', html)
        if m:
            map_api_url = "https://www.google.com" + m.group(1).replace("&amp;", "&")
            req2 = urllib.request.Request(map_api_url, headers=HEADERS)
            with urllib.request.urlopen(req2, timeout=15) as resp2:
                raw = resp2.read().decode("utf-8", errors="ignore")
                clean = raw.replace("\\/", "/").replace("\\u003d", "=").replace("\\u0026", "&")

                # 1. Extract Google Business Profile gps-cs-s and /p/ photos
                gbp_matches = re.findall(
                    r"https://lh[35]\.googleusercontent\.com/(?:gps-cs-s|p)/[A-Za-z0-9_/-]+",
                    clean,
                )
                for u in gbp_matches:
                    base = re.sub(r"=w\d+.*", "", u)
                    full_url = base + "=w800-h600-k-no"
                    if full_url not in photos:
                        photos.append(full_url)

                # 2. Extract Google Street View panorama thumbnail if available
                sv_matches = re.findall(
                    r"https://streetviewpixels-pa\.googleapis\.com/v1/thumbnail\?[^\s\"'\\)\]]+",
                    clean,
                )
                for sv in sv_matches:
                    sv_high = re.sub(r"&w=\d+&h=\d+", "&w=800&h=600", sv)
                    if sv_high not in photos:
                        photos.append(sv_high)
    except Exception as e:
        print(f"  [WARN] Error scraping {name}: {e}")

    return pid, name, photos


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    index_path = os.path.join(REPO_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        text = f.read()

    m = re.search(r"let DUBLIN_PUBS = (\[.*?\]);\s*(?:const|let|var|function|//)", text, re.DOTALL)
    pubs = json.loads(m.group(1))
    print(f"Scraping real Google Business Profile photos from Google Maps for {len(pubs)} Dublin pubs...")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(scrape_pub_gbp_photos, p): p for p in pubs}
        for i, fut in enumerate(concurrent.futures.as_completed(futures), 1):
            pid, name, photos = fut.result()
            results[pid] = photos
            if i % 15 == 0 or i == len(pubs):
                print(f"  Progress: {i}/{len(pubs)} pubs scraped (latest: {name} -> {len(photos)} photos)")

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    non_empty = sum(1 for v in results.values() if len(v) > 0)
    print(f"Saved {OUT_JSON} — {non_empty}/{len(pubs)} pubs returned direct Google Maps photos!")


if __name__ == "__main__":
    main()
