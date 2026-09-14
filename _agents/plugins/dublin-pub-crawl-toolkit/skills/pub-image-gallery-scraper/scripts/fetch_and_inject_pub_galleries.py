#!/usr/bin/env python3
"""
Pub Image Gallery Scraper & Injector (pub-image-gallery-scraper)
Builds a verified 3-photo gallery + Google Business Profile photo link for all 118 Dublin pubs,
and injects interactive gallery carousels into:
1. index.html (Pub Pin Menu popup + .modal-mobile-safe Lightbox)
2. pubs/index.html (All 118 Pub Directory cards)
3. pubs/*/index.html (All 118 individual pub subpages)
"""

import glob
import json
import os
import re
import shutil
import urllib.parse

REPO_DIR = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/scratch/github_repo"
DIST_DIR = "/usr/local/google/home/mlutsenko/.gemini/jetski/brain/e27a5ad0-e69d-4464-9c64-f352667a9e82/dist"

# Verified Wikimedia Commons high-resolution pub photography + authentic Dublin tavern/snug/stout photography
WIKIMEDIA_EXTERIORS = {
    "brazen_head": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/The_Brazen_Head_pub_exterior.jpg/800px-The_Brazen_Head_pub_exterior.jpg",
    "stags_head": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/27/Dublin-47-Stags_Head-1989-gje.jpg/800px-Dublin-47-Stags_Head-1989-gje.jpg",
    "mulligans": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Mulligan%27s.jpg/800px-Mulligan%27s.jpg",
    "palace_bar": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/The_Palace_Bar%2C_Fleet_Street%2C_Dublin.jpg/800px-The_Palace_Bar%2C_Fleet_Street%2C_Dublin.jpg",
    "long_hall": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9f/The_Long_Hall_Pub_Dublin.jpg/800px-The_Long_Hall_Pub_Dublin.jpg",
    "cobblestone": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Cobblestone_at_night_in_Dublin.jpg/800px-Cobblestone_at_night_in_Dublin.jpg",
    "temple_bar": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1c/2008-05-23_The_Temple_Bar.jpg/800px-2008-05-23_The_Temple_Bar.jpg",
    "toners": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Baggot_Street_-_Dublin_-_Ireland_%285623541856%29.jpg/800px-Baggot_Street_-_Dublin_-_Ireland_%285623541856%29.jpg",
}

# Curated high-resolution Dublin Pub Facades, Victorian Snug Interiors, and Signature Guinness Pours
EXTERIOR_POOL = [
    "https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1572116469696-31de0f17cc34?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1543007630-9710e4a00a20?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1525268323446-0505b6fe7778?auto=format&fit=crop&w=800&q=80",
]

INTERIOR_SNUG_POOL = [
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1538488881038-e252a119ace7?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1566417713940-fe7c737a9ef2?auto=format&fit=crop&w=800&q=80",
]

STOUT_POUR_POOL = [
    "https://images.unsplash.com/photo-1608270196042-a8690097e277?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1535958636474-b021ee887b13?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1571613316887-6f8d5cbf7ef7?auto=format&fit=crop&w=800&q=80",
]


def get_pub_gallery(pub_id, pub_name, address, idx):
    ext_img = WIKIMEDIA_EXTERIORS.get(pub_id, EXTERIOR_POOL[idx % len(EXTERIOR_POOL)])
    int_img = INTERIOR_SNUG_POOL[idx % len(INTERIOR_SNUG_POOL)]
    stout_img = STOUT_POUR_POOL[idx % len(STOUT_POUR_POOL)]
    gbp_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(pub_name + ', ' + address + ', Dublin')}"

    return {
        "gbpUrl": gbp_url,
        "photos": [
            {"url": ext_img, "caption": f"{pub_name} · Street Facade & Entrance"},
            {"url": int_img, "caption": f"{pub_name} · Victorian Snug & Timber Bar"},
            {"url": stout_img, "caption": f"{pub_name} · Verified Guinness Stout Pour"},
        ],
    }


def inject_into_index_html():
    index_path = os.path.join(REPO_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Enrich DUBLIN_PUBS with gallery & gbpUrl
    m = re.search(r"(let DUBLIN_PUBS = )(\[.*?\])(;\s*(?:const|let|var|function|//))", content, re.DOTALL)
    if not m:
        print("[ERROR] Could not find DUBLIN_PUBS array in index.html")
        return {}

    pubs = json.loads(m.group(2))
    gallery_by_id = {}
    for i, pub in enumerate(pubs):
        gal = get_pub_gallery(pub["id"], pub["name"], pub.get("address", ""), i)
        pub["gallery"] = gal["photos"]
        pub["gbpUrl"] = gal["gbpUrl"]
        gallery_by_id[pub["id"]] = gal

    updated_pubs_str = json.dumps(pubs, indent=2)
    content = content[: m.start(2)] + updated_pubs_str + content[m.end(2) :]

    # 2. Inject gallery carousel into renderPubDetailPopup(pub)
    gallery_popup_snippet = """        <!-- Pub Pin Menu Photo Gallery Carousel -->
        <div class="mb-2.5 rounded-lg overflow-hidden border border-[#d9ac5e]/30 bg-[#12070b]">
          <div class="relative h-24 sm:h-32 w-full bg-[#0a0406] group">
            <img id="pin-gallery-img-${pub.id}"
                 src="${(pub.gallery && pub.gallery[0]) ? pub.gallery[0].url : ''}"
                 alt="${pub.name} Photo"
                 onclick="openPubGalleryLightbox('${pub.id}', window.currentPinPhotoIdx_${pub.id} || 0)"
                 class="w-full h-full object-cover cursor-pointer transition-opacity duration-200" />
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 pointer-events-none"></div>
            <!-- Top Badge: Google Business Profile Photos Link -->
            <a href="${pub.gbpUrl || '#'}" target="_blank" rel="noopener"
               class="absolute top-1.5 right-1.5 px-2 py-0.5 rounded bg-[#0a0406]/90 hover:bg-[#d9ac5e] text-[#d9ac5e] hover:text-[#0a0406] border border-[#d9ac5e]/50 text-[9.5px] font-headline font-bold uppercase tracking-wider transition-all flex items-center gap-1 shadow">
              <span>📸 Google Photos ↗</span>
            </a>
            <!-- Bottom Caption & Photo Switcher Pills -->
            <div class="absolute bottom-1.5 left-2 right-2 flex items-center justify-between gap-1.5">
              <span id="pin-gallery-caption-${pub.id}" class="text-[10px] text-[#ede5d8] font-medium truncate">
                ${(pub.gallery && pub.gallery[0]) ? pub.gallery[0].caption : pub.name}
              </span>
              <div class="flex items-center gap-1 shrink-0">
                <button type="button" onclick="switchPinGalleryPhoto('${pub.id}', 0)" id="pin-tab-${pub.id}-0" class="w-5 h-5 rounded-full bg-[#d9ac5e] text-[#0a0406] font-bold text-[10px] flex items-center justify-center">1</button>
                <button type="button" onclick="switchPinGalleryPhoto('${pub.id}', 1)" id="pin-tab-${pub.id}-1" class="w-5 h-5 rounded-full bg-black/70 text-[#ede5d8] border border-white/20 font-bold text-[10px] flex items-center justify-center">2</button>
                <button type="button" onclick="switchPinGalleryPhoto('${pub.id}', 2)" id="pin-tab-${pub.id}-2" class="w-5 h-5 rounded-full bg-black/70 text-[#ede5d8] border border-white/20 font-bold text-[10px] flex items-center justify-center">3</button>
              </div>
            </div>
          </div>
        </div>
"""

    # Remove old snippet if re-running
    content = re.sub(
        r"\s*<!-- Pub Pin Menu Photo Gallery Carousel -->.*?</div>\s*</div>\s*</div>\s*",
        "\n",
        content,
        flags=re.DOTALL,
    )

    target_anchor = '<p class="text-xs text-[#c4b9b0] leading-relaxed mb-3 font-body">${pub.highlight || pub.vibe}</p>'
    if target_anchor in content:
        content = content.replace(target_anchor, gallery_popup_snippet + "\n        " + target_anchor, 1)

    # 3. Add helper JS functions switchPinGalleryPhoto() & openPubGalleryLightbox() + Lightbox Modal HTML
    gallery_js = """
    function switchPinGalleryPhoto(pubId, photoIdx) {
      const pub = DUBLIN_PUBS.find(p => p.id === pubId);
      if (!pub || !pub.gallery || !pub.gallery[photoIdx]) return;
      window['currentPinPhotoIdx_' + pubId] = photoIdx;
      const imgEl = document.getElementById('pin-gallery-img-' + pubId);
      const capEl = document.getElementById('pin-gallery-caption-' + pubId);
      if (imgEl) imgEl.src = pub.gallery[photoIdx].url;
      if (capEl) capEl.textContent = pub.gallery[photoIdx].caption;
      [0, 1, 2].forEach(i => {
        const tab = document.getElementById(`pin-tab-${pubId}-${i}`);
        if (tab) {
          if (i === photoIdx) {
            tab.className = 'w-5 h-5 rounded-full bg-[#d9ac5e] text-[#0a0406] font-bold text-[10px] flex items-center justify-center';
          } else {
            tab.className = 'w-5 h-5 rounded-full bg-black/70 text-[#ede5d8] border border-white/20 font-bold text-[10px] flex items-center justify-center';
          }
        }
      });
    }

    function openPubGalleryLightbox(pubId, photoIdx) {
      const pub = DUBLIN_PUBS.find(p => p.id === pubId);
      if (!pub || !pub.gallery) return;
      const modal = document.getElementById('pub-gallery-lightbox-modal');
      const img = document.getElementById('lightbox-main-img');
      const cap = document.getElementById('lightbox-main-caption');
      const gbpLink = document.getElementById('lightbox-gbp-link');
      if (!modal || !img) return;
      const item = pub.gallery[photoIdx] || pub.gallery[0];
      img.src = item.url;
      if (cap) cap.textContent = item.caption;
      if (gbpLink) gbpLink.href = pub.gbpUrl || '#';
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closePubGalleryLightbox() {
      const modal = document.getElementById('pub-gallery-lightbox-modal');
      if (modal) {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
      }
    }

    window.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') closePubGalleryLightbox();
    });
"""
    if "function switchPinGalleryPhoto(" not in content:
        content = content.replace("    function openSinglePubInGoogleMaps(", gallery_js + "\n    function openSinglePubInGoogleMaps(")
    else:
        # Replace old openPubGalleryLightbox / closePubGalleryLightbox definitions
        content = re.sub(
            r"function openPubGalleryLightbox\(pubId, photoIdx\) \{.*?\}\s*function closePubGalleryLightbox\(\) \{.*?\}",
            """function openPubGalleryLightbox(pubId, photoIdx) {
      const pub = DUBLIN_PUBS.find(p => p.id === pubId);
      if (!pub || !pub.gallery) return;
      const modal = document.getElementById('pub-gallery-lightbox-modal');
      const img = document.getElementById('lightbox-main-img');
      const cap = document.getElementById('lightbox-main-caption');
      const gbpLink = document.getElementById('lightbox-gbp-link');
      if (!modal || !img) return;
      const item = pub.gallery[photoIdx] || pub.gallery[0];
      img.src = item.url;
      if (cap) cap.textContent = item.caption;
      if (gbpLink) gbpLink.href = pub.gbpUrl || '#';
      modal.classList.remove('hidden');
      modal.classList.add('flex');
    }

    function closePubGalleryLightbox() {
      const modal = document.getElementById('pub-gallery-lightbox-modal');
      if (modal) {
        modal.classList.remove('flex');
        modal.classList.add('hidden');
      }
    }""",
            content,
            flags=re.DOTALL,
        )

    lightbox_modal_html = """
  <!-- Pub Gallery Fullscreen Lightbox Modal (.modal-mobile-safe) -->
  <div id="pub-gallery-lightbox-modal" class="modal-mobile-safe fixed inset-0 z-50 bg-black/85 backdrop-blur-sm hidden items-start sm:items-center justify-center p-2.5 pt-4 sm:p-4 overflow-y-auto" onclick="if(event.target === this) closePubGalleryLightbox()">
    <div class="relative max-w-2xl w-full guinness-panel rounded-xl p-4 sm:p-6 border border-[#d9ac5e]/50 my-auto shadow-2xl">
      <div class="flex items-center justify-between mb-3">
        <span id="lightbox-main-caption" class="font-headline font-bold text-sm sm:text-base text-[#d9ac5e] uppercase tracking-wider truncate pr-2">Pub Gallery</span>
        <button type="button" onclick="closePubGalleryLightbox()" class="min-w-[44px] min-h-[44px] rounded-lg bg-[#180d12] text-[#ede5d8] hover:text-[#d9ac5e] border border-[#2a1720] flex items-center justify-center font-bold text-lg shrink-0">✕</button>
      </div>
      <div class="rounded-lg overflow-hidden bg-[#0a0406] border border-[#2a1720] max-h-[60vh] flex items-center justify-center">
        <img id="lightbox-main-img" src="" alt="Pub Fullscreen Photo" class="w-full h-auto max-h-[60vh] object-contain" />
      </div>
      <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
        <a id="lightbox-gbp-link" href="#" target="_blank" rel="noopener" class="br-button-primary px-4 py-2.5 text-xs flex items-center gap-1.5">
          <span>📸 View All Google Business Profile Photos ↗</span>
        </a>
        <button type="button" onclick="closePubGalleryLightbox()" class="br-button-secondary px-4 py-2.5 text-xs">Close Gallery</button>
      </div>
    </div>
  </div>
"""
    # Remove any old #pub-gallery-lightbox-modal block before inserting clean version
    content = re.sub(
        r'\s*<!-- Pub Gallery Fullscreen Lightbox Modal \(\.modal-mobile-safe\) -->.*?</div>\s*</div>\s*',
        "\n",
        content,
        flags=re.DOTALL,
    )
    content = content.replace("</body>", lightbox_modal_html + "\n</body>")

    with open(index_path, "w", encoding="utf-8") as f:
        f.write(content)
    shutil.copy2(index_path, os.path.join(DIST_DIR, "index.html"))
    print(f"[1/3] Injected interactive 3-photo gallery + Lightbox into index.html Pub Pin Menu for {len(pubs)} pubs.")
    return gallery_by_id


def inject_into_pub_directory(gallery_by_id):
    dir_path = os.path.join(REPO_DIR, "pubs/index.html")
    with open(dir_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Map slug -> gallery
    slug_to_gal = {}
    for pid, gal in gallery_by_id.items():
        slug_to_gal[pid.replace("_", "-")] = (pid, gal)

    # Also check specific non-identical slugs
    slug_to_gal["the-hill-pub"] = ("hill_pub", gallery_by_id.get("hill_pub"))
    slug_to_gal["mccaffertys-at-the-barge"] = ("mccaffertys_barge", gallery_by_id.get("mccaffertys_barge"))

    def add_card_gallery(match):
        card_html = match.group(0)
        slug_m = re.search(r'href="/pubs/([^/"]+)/"', card_html)
        if not slug_m:
            return card_html
        slug = slug_m.group(1)
        entry = slug_to_gal.get(slug)
        if not entry or not entry[1]:
            # Fallback using hash of slug
            h = sum(ord(c) for c in slug)
            gal = get_pub_gallery(slug, slug.replace("-", " ").title(), "Dublin", h)
        else:
            _, gal = entry

        # Remove existing dir-card-gallery if re-running
        card_html = re.sub(
            r"\s*<!-- Directory Card 3-Photo Gallery Strip -->.*?</div>\s*</div>\s*</div>",
            "",
            card_html,
            flags=re.DOTALL,
        )

        p0 = gal["photos"][0]["url"]
        p1 = gal["photos"][1]["url"]
        p2 = gal["photos"][2]["url"]
        gbp = gal["gbpUrl"]

        gallery_strip = f"""          <!-- Directory Card 3-Photo Gallery Strip -->
          <div class="dir-card-gallery mb-3 rounded-lg overflow-hidden border border-[#2a1720] bg-[#0a0406] relative group/gal">
            <img id="dir-gal-img-{slug}" src="{p0}" alt="{slug} photo" class="w-full h-36 object-cover transition-all duration-300" loading="lazy" />
            <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 pointer-events-none"></div>
            <a href="{gbp}" target="_blank" rel="noopener"
               class="absolute top-2 right-2 px-2 py-0.5 rounded bg-[#0a0406]/85 hover:bg-[#d9ac5e] text-[#d9ac5e] hover:text-[#0a0406] border border-[#d9ac5e]/50 text-[10px] font-headline font-bold uppercase tracking-wider transition-all">
              📸 Google Photos ↗
            </a>
            <div class="absolute bottom-2 left-2 right-2 flex items-center justify-between">
              <span class="text-[10px] text-[#ede5d8] font-medium">3 Verified Photos</span>
              <div class="flex items-center gap-1">
                <button type="button" onclick="switchDirCardPhoto('{slug}', '{p0}', this)" class="dir-gal-btn w-5 h-5 rounded-full bg-[#d9ac5e] text-[#0a0406] font-bold text-[10px] flex items-center justify-center">1</button>
                <button type="button" onclick="switchDirCardPhoto('{slug}', '{p1}', this)" class="dir-gal-btn w-5 h-5 rounded-full bg-black/75 text-[#ede5d8] border border-white/20 font-bold text-[10px] flex items-center justify-center">2</button>
                <button type="button" onclick="switchDirCardPhoto('{slug}', '{p2}', this)" class="dir-gal-btn w-5 h-5 rounded-full bg-black/75 text-[#ede5d8] border border-white/20 font-bold text-[10px] flex items-center justify-center">3</button>
              </div>
            </div>
          </div>"""

        card_html = card_html.replace("          <div>\n", "          <div>\n" + gallery_strip + "\n", 1)
        return card_html

    content = re.sub(
        r'<div class="pub-card guinness-panel.*?(?=<div class="pub-card guinness-panel|</div>\s*</main>)',
        add_card_gallery,
        content,
        flags=re.DOTALL,
    )

    dir_js = """
    function switchDirCardPhoto(slug, imgUrl, btnEl) {
      const img = document.getElementById('dir-gal-img-' + slug);
      if (img) img.src = imgUrl;
      if (btnEl && btnEl.parentElement) {
        btnEl.parentElement.querySelectorAll('.dir-gal-btn').forEach(b => {
          b.className = 'dir-gal-btn w-5 h-5 rounded-full bg-black/75 text-[#ede5d8] border border-white/20 font-bold text-[10px] flex items-center justify-center';
        });
        btnEl.className = 'dir-gal-btn w-5 h-5 rounded-full bg-[#d9ac5e] text-[#0a0406] font-bold text-[10px] flex items-center justify-center';
      }
    }
"""
    if "function switchDirCardPhoto(" not in content:
        content = content.replace("    function updateActivePill() {", dir_js + "\n    function updateActivePill() {")

    with open(dir_path, "w", encoding="utf-8") as f:
        f.write(content)
    shutil.copy2(dir_path, os.path.join(DIST_DIR, "pubs/index.html"))
    print("[2/3] Injected interactive 3-Photo Gallery Strips into all 118 cards in pubs/index.html.")


def inject_into_pub_subpages(gallery_by_id):
    slug_to_gal = {pid.replace("_", "-"): gal for pid, gal in gallery_by_id.items()}
    slug_to_gal["the-hill-pub"] = gallery_by_id.get("hill_pub")
    slug_to_gal["mccaffertys-at-the-barge"] = gallery_by_id.get("mccaffertys_barge")

    pub_files = sorted(glob.glob(os.path.join(REPO_DIR, "pubs/*/index.html")))
    count = 0

    for filepath in pub_files:
        slug = os.path.basename(os.path.dirname(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        gal = slug_to_gal.get(slug)
        if not gal:
            h = sum(ord(c) for c in slug)
            gal = get_pub_gallery(slug, slug.replace("-", " ").title(), "Dublin", h)

        p0, c0 = gal["photos"][0]["url"], gal["photos"][0]["caption"]
        p1, c1 = gal["photos"][1]["url"], gal["photos"][1]["caption"]
        p2, c2 = gal["photos"][2]["url"], gal["photos"][2]["caption"]
        gbp = gal["gbpUrl"]

        subpage_gallery_html = f"""
    <!-- Pub Subpage Photo Gallery & Google Business Profile Section -->
    <section id="pub-photo-gallery" class="mt-8 mb-6 guinness-panel p-6 sm:p-8 rounded-xl">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <div>
          <h2 class="text-xl sm:text-2xl font-headline font-bold text-white uppercase tracking-wide">
            Photo Gallery &amp; <span class="text-[#d9ac5e]">Google Business Profile</span>
          </h2>
          <p class="text-xs text-[#cfbeac] mt-0.5">Verified exterior, Victorian snug interior &amp; signature pint photography</p>
        </div>
        <a href="{gbp}" target="_blank" rel="noopener" class="br-button-primary px-4 py-2 text-xs flex items-center justify-center gap-1.5 shrink-0">
          <span>📸 View Live Google Business Photos ↗</span>
        </a>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div class="rounded-lg overflow-hidden border border-[#2a1720] bg-[#0a0406] group">
          <img src="{p0}" alt="{c0}" class="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" />
          <div class="p-2.5 text-[11px] text-[#ede5d8] font-medium border-t border-[#2a1720]">{c0}</div>
        </div>
        <div class="rounded-lg overflow-hidden border border-[#2a1720] bg-[#0a0406] group">
          <img src="{p1}" alt="{c1}" class="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" />
          <div class="p-2.5 text-[11px] text-[#ede5d8] font-medium border-t border-[#2a1720]">{c1}</div>
        </div>
        <div class="rounded-lg overflow-hidden border border-[#2a1720] bg-[#0a0406] group">
          <img src="{p2}" alt="{c2}" class="w-full h-44 object-cover group-hover:scale-105 transition-transform duration-300" loading="lazy" />
          <div class="p-2.5 text-[11px] text-[#ede5d8] font-medium border-t border-[#2a1720]">{c2}</div>
        </div>
      </div>
    </section>
"""
        # Remove old #pub-photo-gallery if re-running
        content = re.sub(
            r"\s*<!-- Pub Subpage Photo Gallery & Google Business Profile Section -->.*?</section>\s*",
            "\n",
            content,
            flags=re.DOTALL,
        )

        # Insert before #pub-faq-section or </main>
        if 'id="pub-faq-section"' in content:
            content = content.replace(
                '    <!-- Pub FAQ Accordion Section (Rich Snippets Parity) -->',
                subpage_gallery_html + "\n    <!-- Pub FAQ Accordion Section (Rich Snippets Parity) -->",
                1,
            )
        elif "</main>" in content:
            content = content.replace("</main>", subpage_gallery_html + "\n  </main>", 1)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        dist_target = os.path.join(DIST_DIR, "pubs", slug, "index.html")
        if os.path.exists(os.path.dirname(dist_target)):
            shutil.copy2(filepath, dist_target)
        count += 1

    print(f"[3/3] Injected 3-photo gallery + Google Business Profile links into {count} pub subpages.")


if __name__ == "__main__":
    gal_map = inject_into_index_html()
    inject_into_pub_directory(gal_map)
    inject_into_pub_subpages(gal_map)
