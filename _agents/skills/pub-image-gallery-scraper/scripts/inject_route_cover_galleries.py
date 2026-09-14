#!/usr/bin/env python3
"""Injects 5-photo cover galleries into routes/index.html and all 15 route subpages (routes/*/index.html)."""

import glob
import json
import os
import re
import shutil

REPO_DIR = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo"
DIST_DIR = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/dist"
DATA_PATH = os.path.join(
    REPO_DIR,
    "_agents/skills/pub-image-gallery-scraper/data/google_business_profile_photos.json",
)


def load_gbp_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_pubs_map():
    index_path = os.path.join(REPO_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    m = re.search(
        r"(let DUBLIN_PUBS = )(\[.*?\])(;\s*(?:const|let|var|function|//))",
        content,
        re.DOTALL,
    )
    pubs = json.loads(m.group(2))
    name_to_pub = {}
    for p in pubs:
        name_to_pub[p["name"].lower().strip()] = p
        name_to_pub[re.sub(r"[^a-z0-9]", "", p["name"].lower())] = p
    return pubs, name_to_pub


def find_pub_for_stop(pub_name, pubs, name_to_pub):
    norm = re.sub(r"[^a-z0-9]", "", pub_name.lower())
    if pub_name.lower().strip() in name_to_pub:
        return name_to_pub[pub_name.lower().strip()]
    if norm in name_to_pub:
        return name_to_pub[norm]
    for p in pubs:
        pnorm = re.sub(r"[^a-z0-9]", "", p["name"].lower())
        if norm in pnorm or pnorm in norm:
            return p
    return None


def get_pub_photos(pub_id, gbp_data, pub_name="Dublin Pub"):
    entry = gbp_data.get(pub_id, {})
    raw_list = []
    if isinstance(entry, dict):
        raw_list = entry.get("photos", [])
    elif isinstance(entry, list):
        raw_list = entry
    normalized = []
    for i, item in enumerate(raw_list, start=1):
        if isinstance(item, dict):
            normalized.append(
                {
                    "url": item.get("url", ""),
                    "caption": item.get("caption", f"{pub_name} Photo {i}"),
                }
            )
        elif isinstance(item, str):
            normalized.append(
                {
                    "url": item,
                    "caption": f"{pub_name} Photo {i}",
                }
            )
    return normalized


def pick_best_photo(pub_id, gbp_data, pub_name="Dublin Pub", prefer_interior=True):
    photos = get_pub_photos(pub_id, gbp_data, pub_name)
    if not photos:
        return {"url": "", "caption": ""}
    if prefer_interior:
        for p in photos:
            if "streetviewpixels" not in p["url"]:
                return p
    return photos[0]


def get_route_stops(route_filepath, pubs, name_to_pub, gbp_data):
    with open(route_filepath, "r", encoding="utf-8") as f:
        html = f.read()
    ld_m = re.search(
        r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL
    )
    ld = json.loads(ld_m.group(1))
    stops = []
    for g in ld.get("@graph", []):
        if g.get("@type") == "ItemList":
            for idx, item in enumerate(g.get("itemListElement", []), start=1):
                pub_name = item["item"]["name"]
                pub = find_pub_for_stop(pub_name, pubs, name_to_pub)
                if pub:
                    pid = pub["id"]
                    photos = get_pub_photos(pid, gbp_data, pub["name"])
                    stops.append(
                        {
                            "stop_num": idx,
                            "name": pub["name"],
                            "id": pid,
                            "photos": photos,
                        }
                    )
    return stops


def build_five_route_cover_photos(stops, gbp_data):
    """Returns exactly 5 cover photo dicts [{'url': ..., 'caption': 'Stop 1: The Brazen Head'}, ...]."""
    selected = []
    for s in stops:
        best = pick_best_photo(s["id"], gbp_data, prefer_interior=True)
        selected.append(
            {
                "url": best["url"],
                "caption": f"Stop {s['stop_num']}: {s['name']}",
            }
        )
        if len(selected) == 5:
            break
    # If fewer than 5 stops (e.g. 4 stops), add a second distinct photo from stop 1
    while len(selected) < 5 and stops:
        s0 = stops[0]
        photos = s0["photos"]
        extra_idx = min(len(selected) - len(stops) + 1, len(photos) - 1)
        p = photos[extra_idx]
        selected.append(
            {
                "url": p["url"],
                "caption": f"Stop {s0['stop_num']}: {s0['name']} (Interior)",
            }
        )
    return selected[:5]


def inject_into_routes_directory(route_covers_by_slug):
    routes_index_path = os.path.join(REPO_DIR, "routes/index.html")
    with open(routes_index_path, "r", encoding="utf-8") as f:
        content = f.read()

    def update_route_article(match):
        article_html = match.group(0)
        slug_m = re.search(r'href="/routes/([^/"]+)/"', article_html)
        if not slug_m:
            return article_html
        slug = slug_m.group(1)
        cover_photos = route_covers_by_slug.get(slug)
        if not cover_photos:
            return article_html

        photos_json = json.dumps(cover_photos, ensure_ascii=False).replace("'", "&#39;")
        p0 = cover_photos[0]["url"]
        c0 = cover_photos[0]["caption"]

        gallery_strip = f"""          <!-- Route Card 5-Photo Cover Gallery -->
          <div id="route-card-gallery-{slug}" data-idx="0" data-photos='{photos_json}' class="route-card-gallery mb-3.5 rounded-lg overflow-hidden border border-[#2a1720] bg-[#0a0406] relative group/routegal">
            <img id="route-gal-img-{slug}" src="{p0}" alt="{slug} cover photo" class="w-full h-40 sm:h-44 object-cover transition-all duration-300" loading="lazy" />
            <div class="absolute inset-0 bg-gradient-to-t from-black/85 via-transparent to-black/20 pointer-events-none"></div>
            <button type="button" onclick="stepRouteCardPhoto('{slug}', -1)" aria-label="Previous route photo"
                    class="absolute left-1.5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-[#0a0406]/85 hover:bg-[#d9ac5e] text-[#f5ead8] hover:text-[#0a0406] border border-[#d9ac5e]/50 flex items-center justify-center font-bold text-base transition-all shadow-md z-10">
              &#8249;
            </button>
            <button type="button" onclick="stepRouteCardPhoto('{slug}', 1)" aria-label="Next route photo"
                    class="absolute right-1.5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-[#0a0406]/85 hover:bg-[#d9ac5e] text-[#f5ead8] hover:text-[#0a0406] border border-[#d9ac5e]/50 flex items-center justify-center font-bold text-base transition-all shadow-md z-10">
              &#8250;
            </button>
            <div class="absolute bottom-2 left-2.5 right-2.5 flex items-center justify-between gap-2">
              <span id="route-gal-caption-{slug}" class="text-[11px] text-[#ede5d8] font-medium truncate">{c0}</span>
              <span id="route-gal-counter-{slug}" class="px-2 py-0.5 rounded bg-black/80 border border-[#d9ac5e]/40 text-[10px] font-mono text-[#d9ac5e] font-bold shrink-0">1 / 5</span>
            </div>
          </div>"""

        # Remove any existing Route Card 5-Photo Cover Gallery first
        article_html = re.sub(
            r"\s*<!-- Route Card 5-Photo Cover Gallery -->.*?(?=\s*<div class=\"flex items-center justify-between gap-2 mb-2\">)",
            "",
            article_html,
            flags=re.DOTALL,
        )

        # Insert right inside the top `<div>` before `<div class="flex items-center justify-between gap-2 mb-2">`
        article_html = re.sub(
            r'(<article[^>]*>\s*<div>\s*)(<div class="flex items-center justify-between gap-2 mb-2">)',
            lambda m: m.group(1) + gallery_strip + "\n            " + m.group(2),
            article_html,
            count=1,
            flags=re.DOTALL,
        )
        return article_html

    content = re.sub(
        r'<article class="p-5 rounded-\[4px\] guinness-panel.*?</article>',
        update_route_article,
        content,
        flags=re.DOTALL,
    )

    # Add stepRouteCardPhoto JS function before </body> if not present
    js_snippet = """  <script>
    function stepRouteCardPhoto(slug, delta) {
      const galEl = document.getElementById('route-card-gallery-' + slug);
      if (!galEl) return;
      let photos = [];
      try {
        photos = JSON.parse(galEl.getAttribute('data-photos') || '[]');
      } catch (e) {
        return;
      }
      if (!photos.length) return;
      let idx = parseInt(galEl.getAttribute('data-idx') || '0', 10);
      idx = (idx + delta + photos.length) % photos.length;
      galEl.setAttribute('data-idx', String(idx));
      const img = document.getElementById('route-gal-img-' + slug);
      if (img) img.src = photos[idx].url;
      const cap = document.getElementById('route-gal-caption-' + slug);
      if (cap) cap.textContent = photos[idx].caption;
      const counter = document.getElementById('route-gal-counter-' + slug);
      if (counter) counter.textContent = (idx + 1) + ' / ' + photos.length;
    }
  </script>
</body>"""

    content = re.sub(
        r"\s*<script>\s*function stepRouteCardPhoto.*?</script>\s*</body>",
        "\n</body>",
        content,
        flags=re.DOTALL,
    )
    content = content.replace("</body>", js_snippet)

    with open(routes_index_path, "w", encoding="utf-8") as f:
        f.write(content)
    shutil.copy2(routes_index_path, os.path.join(DIST_DIR, "routes/index.html"))
    print(
        f"[1/2] Injected 5-photo cover galleries into all {len(route_covers_by_slug)} route cards in routes/index.html."
    )


def inject_into_route_subpages(route_stops_by_slug, route_covers_by_slug):
    for slug, stops in route_stops_by_slug.items():
        filepath = os.path.join(REPO_DIR, f"routes/{slug}/index.html")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        cover_photos = route_covers_by_slug[slug]
        photos_json = json.dumps(cover_photos, ensure_ascii=False).replace("'", "&#39;")
        p0 = cover_photos[0]["url"]
        c0 = cover_photos[0]["caption"]

        hero_banner = f"""      <!-- Route Hero 5-Photo Cover Banner -->
      <div id="route-hero-gallery" data-idx="0" data-photos='{photos_json}' class="mb-5 rounded-lg overflow-hidden border border-[#d9ac5e]/40 bg-[#0a0406] relative group/routehero">
        <img id="route-hero-img" src="{p0}" alt="{slug} featured pub stop photo" class="w-full h-52 sm:h-64 object-cover transition-all duration-300" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/85 via-transparent to-black/20 pointer-events-none"></div>
        <button type="button" onclick="stepRouteHeroPhoto(-1)" aria-label="Previous route stop photo"
                class="absolute left-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-[#0a0406]/85 hover:bg-[#d9ac5e] text-[#f5ead8] hover:text-[#0a0406] border border-[#d9ac5e]/50 flex items-center justify-center font-bold text-lg transition-all shadow-md z-10">
          &#8249;
        </button>
        <button type="button" onclick="stepRouteHeroPhoto(1)" aria-label="Next route stop photo"
                class="absolute right-2 top-1/2 -translate-y-1/2 w-9 h-9 rounded-full bg-[#0a0406]/85 hover:bg-[#d9ac5e] text-[#f5ead8] hover:text-[#0a0406] border border-[#d9ac5e]/50 flex items-center justify-center font-bold text-lg transition-all shadow-md z-10">
          &#8250;
        </button>
        <div class="absolute bottom-2.5 left-3 right-3 flex items-center justify-between gap-2">
          <span id="route-hero-caption" class="text-xs sm:text-sm text-[#ede5d8] font-medium truncate">{c0}</span>
          <span id="route-hero-counter" class="px-2.5 py-0.5 rounded bg-black/80 border border-[#d9ac5e]/40 text-xs font-mono text-[#d9ac5e] font-bold shrink-0">1 / 5</span>
        </div>
      </div>"""

        # Remove existing Route Hero 5-Photo Cover Banner if present
        content = re.sub(
            r"\s*<!-- Route Hero 5-Photo Cover Banner -->.*?(?=\s*<div class=\"flex flex-wrap items-center gap-2 mb-2\">)",
            "",
            content,
            flags=re.DOTALL,
        )

        # Inject hero_banner inside <!-- Hero Header --> right before <div class="flex flex-wrap items-center gap-2 mb-2">
        content = re.sub(
            r'(<!-- Hero Header -->\s*<div class="guinness-panel[^"]*">\s*)(<div class="flex flex-wrap items-center gap-2 mb-2">)',
            lambda m: m.group(1) + hero_banner + "\n      " + m.group(2),
            content,
            count=1,
            flags=re.DOTALL,
        )

        # Also inject Stop 5-Photo Gallery Strip into each stop card along the itinerary timeline
        for stop in stops:
            s_num = stop["stop_num"]
            s_photos = stop["photos"]
            if not s_photos:
                continue
            s_json = json.dumps(s_photos, ensure_ascii=False).replace("'", "&#39;")
            sp0 = s_photos[0]["url"]
            sc0 = s_photos[0]["caption"]
            stop_strip = f"""            <!-- Stop {s_num} 5-Photo Gallery Strip -->
            <div id="route-stop-gallery-{s_num}" data-idx="0" data-photos='{s_json}' class="mb-3.5 rounded-lg overflow-hidden border border-[#2a1720] bg-[#0a0406] relative group/stopgal">
              <img id="route-stop-img-{s_num}" src="{sp0}" alt="{stop['name']} photo" class="w-full h-44 sm:h-52 object-cover transition-all duration-300" loading="lazy" />
              <div class="absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-black/15 pointer-events-none"></div>
              <button type="button" onclick="stepRouteStopPhoto({s_num}, -1)" aria-label="Previous stop photo"
                      class="absolute left-1.5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-[#0a0406]/85 hover:bg-[#d9ac5e] text-[#f5ead8] hover:text-[#0a0406] border border-[#d9ac5e]/50 flex items-center justify-center font-bold text-base transition-all shadow-md z-10">
                &#8249;
              </button>
              <button type="button" onclick="stepRouteStopPhoto({s_num}, 1)" aria-label="Next stop photo"
                      class="absolute right-1.5 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-[#0a0406]/85 hover:bg-[#d9ac5e] text-[#f5ead8] hover:text-[#0a0406] border border-[#d9ac5e]/50 flex items-center justify-center font-bold text-base transition-all shadow-md z-10">
                &#8250;
              </button>
              <div class="absolute bottom-2 right-2.5 flex items-center justify-end">
                <span id="route-stop-counter-{s_num}" class="px-2 py-0.5 rounded bg-black/80 border border-[#d9ac5e]/40 text-[10px] font-mono text-[#d9ac5e] font-bold shrink-0">1 / {len(s_photos)}</span>
              </div>
            </div>"""

            # Remove any existing stop strip first
            content = re.sub(
                rf"\s*<!-- Stop {s_num} 5-Photo Gallery Strip -->.*?(?=\s*<div class=\"flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2\">)",
                "",
                content,
                flags=re.DOTALL,
            )

            # Inject stop_strip inside the stop card right after `<div class="p-4 sm:p-5 rounded-[4px] bg-[#12070b] ...">`
            pattern = (
                rf'(<div class="absolute -left-\[17px\] top-0[^"]*">\s*{s_num}\s*</div>\s*'
                rf'<div class="p-4 sm:p-5 rounded-\[4px\] bg-\[#12070b\][^"]*">\s*)'
                rf'(<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">)'
            )
            content = re.sub(
                pattern,
                lambda m, strip=stop_strip: m.group(1) + strip + "\n            " + m.group(2),
                content,
                count=1,
                flags=re.DOTALL,
            )

        subpage_js = """  <script>
    function stepRouteHeroPhoto(delta) {
      const galEl = document.getElementById('route-hero-gallery');
      if (!galEl) return;
      let photos = [];
      try {
        photos = JSON.parse(galEl.getAttribute('data-photos') || '[]');
      } catch (e) {
        return;
      }
      if (!photos.length) return;
      let idx = parseInt(galEl.getAttribute('data-idx') || '0', 10);
      idx = (idx + delta + photos.length) % photos.length;
      galEl.setAttribute('data-idx', String(idx));
      const img = document.getElementById('route-hero-img');
      if (img) img.src = photos[idx].url;
      const cap = document.getElementById('route-hero-caption');
      if (cap) cap.textContent = photos[idx].caption;
      const counter = document.getElementById('route-hero-counter');
      if (counter) counter.textContent = (idx + 1) + ' / ' + photos.length;
    }

    function stepRouteStopPhoto(stopNum, delta) {
      const galEl = document.getElementById('route-stop-gallery-' + stopNum);
      if (!galEl) return;
      let photos = [];
      try {
        photos = JSON.parse(galEl.getAttribute('data-photos') || '[]');
      } catch (e) {
        return;
      }
      if (!photos.length) return;
      let idx = parseInt(galEl.getAttribute('data-idx') || '0', 10);
      idx = (idx + delta + photos.length) % photos.length;
      galEl.setAttribute('data-idx', String(idx));
      const img = document.getElementById('route-stop-img-' + stopNum);
      if (img) img.src = photos[idx].url;
      const cap = document.getElementById('route-stop-caption-' + stopNum);
      if (cap) cap.textContent = photos[idx].caption;
      const counter = document.getElementById('route-stop-counter-' + stopNum);
      if (counter) counter.textContent = (idx + 1) + ' / ' + photos.length;
    }
  </script>
</body>"""

        content = re.sub(
            r"\s*<script>\s*function stepRouteHeroPhoto.*?</script>\s*</body>",
            "\n</body>",
            content,
            flags=re.DOTALL,
        )
        content = content.replace("</body>", subpage_js)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        dist_sub = os.path.join(DIST_DIR, f"routes/{slug}/index.html")
        os.makedirs(os.path.dirname(dist_sub), exist_ok=True)
        shutil.copy2(filepath, dist_sub)

    print(
        f"[2/2] Injected hero cover banners & stop photo galleries into all {len(route_stops_by_slug)} route subpages."
    )


def main():
    gbp_data = load_gbp_data()
    pubs, name_to_pub = load_pubs_map()

    route_files = sorted(glob.glob(os.path.join(REPO_DIR, "routes/*/index.html")))
    route_stops_by_slug = {}
    route_covers_by_slug = {}

    for rf in route_files:
        slug = os.path.basename(os.path.dirname(rf))
        stops = get_route_stops(rf, pubs, name_to_pub, gbp_data)
        route_stops_by_slug[slug] = stops
        route_covers_by_slug[slug] = build_five_route_cover_photos(stops, gbp_data)

    inject_into_routes_directory(route_covers_by_slug)
    inject_into_route_subpages(route_stops_by_slug, route_covers_by_slug)


if __name__ == "__main__":
    main()
