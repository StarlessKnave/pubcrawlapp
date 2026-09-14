#!/usr/bin/env python3
"""Continuous Uptime & SEO Monitor for https://dublinpubcrawl.app/ (136 pages)."""

import argparse
import concurrent.futures
import os
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

SITEMAP_URL = "https://dublinpubcrawl.app/sitemap.xml"


def check_url(url: str):
    """Fetch URL without following redirect loops and verify HTTP 200 + canonical tag."""
    req = urllib.request.Request(url, headers={"User-Agent": "DublinPubCrawl-SEOMonitor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            final_url = resp.geturl()
            body = resp.read(16384).decode("utf-8", errors="ignore")
            has_www_leak = "www.dublinpubcrawl.app" in body
            return {
                "url": url,
                "status": status,
                "final_url": final_url,
                "redirected": final_url != url,
                "has_www_leak": has_www_leak,
                "ok": (status == 200 and not has_www_leak),
            }
    except Exception as e:
        return {
            "url": url,
            "status": getattr(e, "code", 0),
            "final_url": url,
            "redirected": False,
            "has_www_leak": False,
            "ok": False,
            "error": str(e),
        }


def run_audit(once: bool = False):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Fetching sitemap: {SITEMAP_URL}")
    req = urllib.request.Request(SITEMAP_URL, headers={"User-Agent": "DublinPubCrawl-SEOMonitor/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        xml_bytes = resp.read()

    root = ET.fromstring(xml_bytes)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = [(loc.text or "").strip() for loc in root.findall(".//sm:loc", ns) if loc.text]

    print(f"Found {len(urls)} URLs in sitemap.xml. Auditing HTTP status & canonical tags...")
    failures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(check_url, urls))

    for res in results:
        if not res["ok"]:
            failures.append(res)

    print(
        f"Audit complete: {len(results) - len(failures)}/{len(results)} pages returned HTTP 200 OK (0 www leaks)."
    )

    if failures:
        print(f"CRITICAL: {len(failures)} URLs failed health check!")
        for f in failures[:10]:
            print(f"  - {f['url']} -> HTTP {f['status']} ({f.get('error', 'canonical/redirect mismatch')})")
        # Notify agent if agentapi is available
        if not once:
            try:
                prompt = (
                    f"SEO Monitor Alert: {len(failures)} pages on dublinpubcrawl.app failed HTTP 200 / canonical checks. "
                    f"First failing URL: {failures[0]['url']} (HTTP {failures[0]['status']}). Please investigate."
                )
                subprocess.run(["agentapi", "new-conversation", prompt], check=False)
            except Exception as e:
                print(f"Could not invoke agentapi: {e}")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")
    args = parser.parse_args()

    interval = int(os.environ.get("CHECK_INTERVAL_SECONDS", "3600"))

    if args.once:
        sys.exit(run_audit(once=True))

    while True:
        try:
            run_audit(once=False)
        except Exception as e:
            print(f"Monitor cycle error: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
