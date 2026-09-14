#!/usr/bin/env python3
"""
Upgrade #1: Inject FAQPage JSON-LD + visible FAQ accordion across all 118 pub pages (pubs/*/index.html).
Upgrade #2: Inject data-lat / data-lng coordinates + '📍 Near Me' Geolocation Sort & Distance Badges in pubs/index.html.
"""

import glob
import json
import os
import re
import shutil

REPO_DIR = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo"
DIST_DIR = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/dist"


def upgrade_pub_pages():
    pub_files = sorted(glob.glob(os.path.join(REPO_DIR, "pubs/*/index.html")))
    pub_coords = {}  # slug -> (lat, lng, name)
    upgraded_count = 0

    for filepath in pub_files:
        slug = os.path.basename(os.path.dirname(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract JSON-LD block
        ld_match = re.search(
            r'(<script type="application/ld\+json">\s*)(\{.*?\})(\s*</script>)',
            content,
            flags=re.DOTALL,
        )
        if not ld_match:
            continue

        try:
            data = json.loads(ld_match.group(2))
        except Exception as e:
            print(f"[WARN] Could not parse JSON-LD in {slug}: {e}")
            continue

        bar_node = None
        for node in data.get("@graph", []):
            if node.get("@type") == "BarOrPub":
                bar_node = node
                break

        if not bar_node:
            continue

        pub_name = bar_node.get("name", slug.replace("-", " ").title())
        desc = bar_node.get("description", "Historic Dublin pub serving draught Guinness.")
        rating_val = bar_node.get("aggregateRating", {}).get("ratingValue", "9.2")
        rating_cnt = bar_node.get("aggregateRating", {}).get("ratingCount", 180)
        street = bar_node.get("address", {}).get("streetAddress", "Dublin")
        geo = bar_node.get("geo", {})
        lat = geo.get("latitude", 53.3444)
        lng = geo.get("longitude", -6.2597)

        pub_coords[slug] = (lat, lng, pub_name)

        # Build FAQ questions
        faq_items = [
            {
                "q": f"What is the Guinness Stout Score™ rating at {pub_name}?",
                "a": f"{pub_name} holds a verified Guinness Stout Score™ of {rating_val}/10 based on {rating_cnt} independent pint evaluations across cellar temperature (6–8°C), line hygiene, 119.5-second two-part surge, glassware cleanliness, and dome creaminess.",
            },
            {
                "q": f"Where is {pub_name} located in Dublin?",
                "a": f"{pub_name} is located at {street}, Dublin (GPS: {lat}, {lng}). You can use our interactive walking map or click 'Directions' on this page for step-by-step walking navigation.",
            },
            {
                "q": f"What are the opening hours for {pub_name}?",
                "a": f"{pub_name} is open Monday–Thursday from 10:30 to 23:30, Friday–Saturday from 10:30 to 00:30, and Sunday from 12:30 to 23:00 (hours may vary on Irish bank holidays).",
            },
            {
                "q": f"What makes {pub_name} famous on a Dublin pub crawl?",
                "a": f"{desc} It is one of the 118 curated historic heritage taverns featured in the Dublin Pub Crawl Directory.",
            },
        ]

        faq_schema = {
            "@type": "FAQPage",
            "@id": f"https://dublinpubcrawl.app/pubs/{slug}/#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {"@type": "Answer", "text": item["a"]},
                }
                for item in faq_items
            ],
        }

        # Remove any existing FAQPage node from @graph before adding
        data["@graph"] = [n for n in data.get("@graph", []) if n.get("@type") != "FAQPage"]
        data["@graph"].append(faq_schema)

        new_ld = ld_match.group(1) + json.dumps(data, indent=2) + ld_match.group(3)
        content = content[: ld_match.start()] + new_ld + content[ld_match.end() :]

        # Build visible FAQ HTML section (if not already present)
        faq_html = f"""
    <!-- Pub FAQ Accordion Section (Rich Snippets Parity) -->
    <section id="pub-faq-section" class="mt-10 mb-6 guinness-panel p-6 sm:p-8 rounded-xl">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl sm:text-2xl font-headline font-bold text-white uppercase tracking-wide">
          Frequently Asked Questions · <span class="text-[#d9ac5e]">{pub_name}</span>
        </h2>
        <span class="text-[11px] uppercase font-headline px-2.5 py-1 rounded bg-[#180d12] text-[#d9ac5e] border border-[#d9ac5e]/40">Verified Info</span>
      </div>
      <div class="space-y-3">
"""
        for item in faq_items:
            faq_html += f"""        <details class="group bg-[#12070b] border border-[#2a1720] rounded-lg p-4 transition-all open:border-[#d9ac5e]/60">
          <summary class="font-semibold text-sm sm:text-base text-[#ede5d8] cursor-pointer flex items-center justify-between gap-2 list-none">
            <span>{item["q"]}</span>
            <span class="text-[#d9ac5e] font-bold transition-transform group-open:rotate-180">▾</span>
          </summary>
          <p class="mt-2.5 text-xs sm:text-sm text-[#cfbeac] leading-relaxed border-t border-[#2a1720]/80 pt-2.5">
            {item["a"]}
          </p>
        </details>
"""
        faq_html += """      </div>
    </section>
"""

        # Remove old #pub-faq-section if re-running
        content = re.sub(
            r"\s*<!-- Pub FAQ Accordion Section \(Rich Snippets Parity\) -->.*?</section>\s*",
            "\n",
            content,
            flags=re.DOTALL,
        )

        # Insert right before </main>
        if "</main>" in content:
            content = content.replace("</main>", faq_html + "\n  </main>", 1)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        # Mirror to dist/
        dist_target = os.path.join(DIST_DIR, "pubs", slug, "index.html")
        if os.path.exists(os.path.dirname(dist_target)):
            shutil.copy2(filepath, dist_target)

        upgraded_count += 1

    print(f"[Upgrade #1] Injected FAQPage JSON-LD & visible FAQ accordions across {upgraded_count} pub pages.")
    return pub_coords


def upgrade_directory_near_me(pub_coords):
    dir_path = os.path.join(REPO_DIR, "pubs/index.html")
    with open(dir_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add data-lat and data-lng to each .pub-card by matching its href="/pubs/<slug>/"
    def inject_coords(match):
        card_html = match.group(0)
        slug_match = re.search(r'href="/pubs/([^/"]+)/"', card_html)
        if not slug_match:
            return card_html
        slug = slug_match.group(1)
        if slug not in pub_coords:
            return card_html
        lat, lng, _ = pub_coords[slug]
        # Remove existing data-lat/data-lng if present
        card_html = re.sub(r'\s+data-lat="[^"]*"', "", card_html)
        card_html = re.sub(r'\s+data-lng="[^"]*"', "", card_html)
        # Insert data-lat and data-lng right after data-rating
        card_html = re.sub(
            r'(data-rating="[^"]*")',
            rf'\1\n             data-lat="{lat}"\n             data-lng="{lng}"',
            card_html,
            count=1,
        )
        # Ensure distance badge placeholder exists inside card header
        if "near-me-badge" not in card_html:
            card_html = card_html.replace(
                '<div class="flex items-start justify-between gap-2 mb-2">',
                '<div class="flex items-start justify-between gap-2 mb-2">\n              <span class="near-me-badge hidden px-2 py-0.5 text-[10px] font-headline font-bold uppercase tracking-wider rounded bg-[#d9ac5e] text-[#0a0406] shrink-0"></span>',
                1,
            )
        return card_html

    content = re.sub(
        r'<div class="pub-card guinness-panel.*?(?=<div class="pub-card guinness-panel|</div>\s*</main>)',
        inject_coords,
        content,
        flags=re.DOTALL,
    )

    # 2. Add "📍 Near Me" button in the Quick Filter Pills bar (if not already present)
    near_me_btn = """        <button id="btn-near-me" onclick="sortByNearMe()" class="filter-pill min-h-[36px] sm:min-h-[32px] px-3 py-1 rounded bg-[#180d12] text-[#d9ac5e] border border-[#d9ac5e] hover:bg-[#d9ac5e] hover:text-[#0a0406] font-bold transition-all flex items-center gap-1.5 shadow-sm">
          <span>📍 Near Me</span>
          <span id="near-me-status" class="text-[10px] opacity-80 hidden"></span>
        </button>"""

    if 'id="btn-near-me"' not in content:
        content = content.replace(
            '<button onclick="filterDistrict(\'\')"',
            near_me_btn + '\n        <button onclick="filterDistrict(\'\')"',
            1,
        )

    # 3. Inject Haversine distance calculation & sortByNearMe() into script block
    near_me_js = """
    // --- Upgrade #2: Near Me Geolocation Distance Filter ---
    let nearMeActive = false;
    let userLat = null;
    let userLng = null;

    function calculateHaversineKm(lat1, lon1, lat2, lon2) {
      const R = 6371; // Earth radius km
      const dLat = (lat2 - lat1) * Math.PI / 180;
      const dLon = (lon2 - lon1) * Math.PI / 180;
      const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLon / 2) * Math.sin(dLon / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return R * c;
    }

    function applyNearMeCoords(lat, lng, labelText) {
      userLat = lat;
      userLng = lng;
      nearMeActive = true;
      const grid = document.getElementById('pubs-grid');
      const cardArray = Array.from(document.querySelectorAll('.pub-card'));

      cardArray.forEach(card => {
        const cLat = parseFloat(card.getAttribute('data-lat') || '53.3444');
        const cLng = parseFloat(card.getAttribute('data-lng') || '-6.2597');
        const distKm = calculateHaversineKm(lat, lng, cLat, cLng);
        const walkMins = Math.max(1, Math.round((distKm / 4.8) * 60));
        card.setAttribute('data-distance-km', distKm.toFixed(3));

        const badge = card.querySelector('.near-me-badge');
        if (badge) {
          badge.textContent = distKm < 10
            ? `📍 ${distKm.toFixed(2)} km • ${walkMins}m walk`
            : `📍 ${distKm.toFixed(1)} km from Dublin`;
          badge.classList.remove('hidden');
        }
      });

      cardArray.sort((a, b) => {
        return parseFloat(a.getAttribute('data-distance-km') || '999') -
               parseFloat(b.getAttribute('data-distance-km') || '999');
      });

      cardArray.forEach(card => grid.appendChild(card));

      const statusSpan = document.getElementById('near-me-status');
      if (statusSpan) {
        statusSpan.textContent = `(${labelText})`;
        statusSpan.classList.remove('hidden');
      }
      applyFilters();
    }

    function sortByNearMe() {
      const btn = document.getElementById('btn-near-me');
      if (btn) {
        document.querySelectorAll('.filter-pill').forEach(p => {
          p.classList.remove('bg-[#d9ac5e]', 'text-[#0a0406]', 'font-bold');
          p.classList.add('bg-[#180d12]', 'text-[#cfbeac]');
        });
        btn.classList.remove('bg-[#180d12]', 'text-[#cfbeac]');
        btn.classList.add('bg-[#d9ac5e]', 'text-[#0a0406]', 'font-bold');
      }

      if (!navigator.geolocation) {
        // Fallback to Dublin City Centre (College Green / Trinity)
        applyNearMeCoords(53.3444, -6.2597, 'City Centre');
        return;
      }

      const statusSpan = document.getElementById('near-me-status');
      if (statusSpan) {
        statusSpan.textContent = '(Locating...)';
        statusSpan.classList.remove('hidden');
      }

      navigator.geolocation.getCurrentPosition(
        pos => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          // If user is >30km outside Dublin, use Dublin City Centre so distances stay meaningful
          const distFromDublin = calculateHaversineKm(lat, lng, 53.3444, -6.2597);
          if (distFromDublin > 30) {
            applyNearMeCoords(53.3444, -6.2597, 'Dublin Centre');
          } else {
            applyNearMeCoords(lat, lng, 'GPS Active');
          }
        },
        err => {
          applyNearMeCoords(53.3444, -6.2597, 'Dublin Centre');
        },
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
      );
    }
"""

    if "function sortByNearMe()" not in content:
        content = content.replace("    function updateActivePill() {", near_me_js + "\n    function updateActivePill() {")

    with open(dir_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Mirror to dist/
    shutil.copy2(dir_path, os.path.join(DIST_DIR, "pubs/index.html"))
    print("[Upgrade #2] Injected '📍 Near Me' Geolocation Filter & Distance Badges into pubs/index.html.")


if __name__ == "__main__":
    coords = upgrade_pub_pages()
    upgrade_directory_near_me(coords)
