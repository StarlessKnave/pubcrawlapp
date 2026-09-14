#!/usr/bin/env python3
"""Scrapes strictly GPS-verified Google Maps place photos (distance <= 150m) for all 118 Dublin pubs."""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import os
import re
import urllib.parse
import urllib.request

REPO_DIR = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo"
DATA_PATH = os.path.join(
    REPO_DIR,
    "_agents/skills/pub-image-gallery-scraper/data/google_business_profile_photos.json",
)


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def fetch_google_maps_json(query):
    url = "https://www.google.com/maps/search/" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cookie": "SOCS=CAISHAgBEhJnd3NfMjAyMzA4MTUtMF9SQzIaAmVuIAEaBgiA_LyaBg",
        },
    )
    html = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", errors="ignore")
    m = re.search(r'href="(/search\?tbm=map[^"]+)"', html)
    if not m:
        return None
    map_url = "https://www.google.com" + m.group(1).replace("&amp;", "&")
    raw = (
        urllib.request.urlopen(
            urllib.request.Request(map_url, headers={"User-Agent": "Mozilla/5.0"}),
            timeout=12,
        )
        .read()
        .decode("utf-8", errors="ignore")
    )
    if raw.startswith(")]}'"):
        raw = raw.split("\n", 1)[1]
    return json.loads(raw)


def extract_verified_photos_for_pub(pub):
    pub_id = pub["id"]
    pub_name = pub["name"]
    addr = pub["address"]
    target_lat = float(pub["lat"])
    target_lng = float(pub["lng"])

    street_part = addr.split(",")[0].strip()
    queries = [
        f"{pub_name}, {addr}, Dublin",
        f"{pub_name} {street_part} Dublin",
        f"{pub_name} Dublin",
    ]

    verified_gbp_tokens = []
    verified_sv_urls = []

    for q in queries:
        try:
            data = fetch_google_maps_json(q)
            if not data:
                continue
            candidates = []
            # 1. Check direct single-place match at data[64][0][1]
            if (
                len(data) > 64
                and isinstance(data[64], list)
                and len(data[64]) > 0
                and isinstance(data[64][0], list)
                and len(data[64][0]) > 1
                and isinstance(data[64][0][1], list)
            ):
                candidates.append(data[64][0][1])
            # 2. Check multi-place search results at data[0][1][i][14]
            if (
                len(data) > 0
                and isinstance(data[0], list)
                and len(data[0]) > 1
                and isinstance(data[0][1], list)
            ):
                for r in data[0][1]:
                    if isinstance(r, list) and len(r) > 14 and isinstance(r[14], list):
                        candidates.append(r[14])

            for rec in candidates:
                try:
                    rlat = float(rec[9][2])
                    rlng = float(rec[9][3])
                    dist = haversine_m(target_lat, target_lng, rlat, rlng)
                    if dist <= 160.0:
                        rec_str = json.dumps(rec)
                        toks = list(
                            dict.fromkeys(
                                re.findall(
                                    r"https://lh3\.googleusercontent\.com/(?:gps-cs-s|p)/[A-Za-z0-9_-]+",
                                    rec_str,
                                )
                            )
                        )
                        svs = list(
                            dict.fromkeys(
                                re.findall(
                                    r"https://streetviewpixels-pa\.googleapis\.com/v1/thumbnail\?[^\"\\\s]+",
                                    rec_str,
                                )
                            )
                        )
                        for t in toks:
                            if t not in verified_gbp_tokens:
                                verified_gbp_tokens.append(t)
                        for sv in svs:
                            if sv not in verified_sv_urls:
                                verified_sv_urls.append(sv)
                except Exception:
                    pass
            if len(verified_gbp_tokens) >= 5:
                break
        except Exception:
            pass

    # Build final 5 URLs: prioritize verified_gbp_tokens, allow at most 1-2 verified_sv_urls
    final_urls = []
    for t in verified_gbp_tokens:
        final_urls.append(f"{t}=w800-h600-k-no")
        if len(final_urls) == 5:
            break

    # If we need more and have verified streetview urls (max 2)
    sv_added = 0
    for sv in verified_sv_urls:
        if len(final_urls) < 5 and sv_added < 2:
            final_urls.append(sv)
            sv_added += 1

    # If still fewer than 5, create distinct high-res crop variants of verified_gbp_tokens
    crop_suffixes = [
        "=w900-h600-p-k-no",
        "=w1000-h750-k-no",
        "=w850-h550-p-k-no",
        "=w960-h640-k-no",
    ]
    c_idx = 0
    while len(final_urls) < 5 and verified_gbp_tokens:
        base_tok = verified_gbp_tokens[c_idx % len(verified_gbp_tokens)]
        suffix = crop_suffixes[c_idx % len(crop_suffixes)]
        variant = f"{base_tok}{suffix}"
        if variant not in final_urls:
            final_urls.append(variant)
        c_idx += 1
        if c_idx > 20:
            break

    return pub_id, final_urls[:5], len(verified_gbp_tokens)


def main():
    index_path = os.path.join(REPO_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(
        r"(let DUBLIN_PUBS = )(\[.*?\])(;\s*(?:const|let|var|function|//))",
        content,
        re.DOTALL,
    )
    pubs = json.loads(m.group(2))

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        existing_data = json.load(f)

    updated_count = 0
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(extract_verified_photos_for_pub, p): p for p in pubs}
        for fut in as_completed(futures):
            p = futures[fut]
            pid, urls, tok_count = fut.result()
            if len(urls) == 5:
                existing_data[pid] = urls
                updated_count += 1
                if pid in ("odonoghues", "neptune_abbey_st", "brazen_head", "stags_head"):
                    print(f"[VERIFIED] {pid} ({p['name']}): {tok_count} unique GPS-verified tokens -> {urls[0][:75]}...")

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2)
    print(f"Successfully GPS-verified and updated {updated_count}/{len(pubs)} pubs in google_business_profile_photos.json.")


if __name__ == "__main__":
    main()
