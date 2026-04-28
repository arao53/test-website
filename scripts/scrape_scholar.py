#!/usr/bin/env python3
"""
WE3 Lab — Google Scholar scraper
Usage:
    python3 scrape_scholar.py                    # scrape all members
    python3 scrape_scholar.py --member "Emma Liu" # single member
    python3 scrape_scholar.py --force            # ignore cache
    python3 scrape_scholar.py --proxy            # use free proxy pool (slower, fewer blocks)
    python3 scrape_scholar.py --max-pubs 50      # cap publications per author
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from tqdm import tqdm

try:
    from scholarly import scholarly, ProxyGenerator
except ImportError:
    sys.exit("scholarly not installed. Run: pip3 install -r requirements.txt")

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent
MEMBERS    = ROOT / "members.json"
CACHE_DIR  = ROOT / "cache"
OUTPUT     = ROOT / "publications.json"
LOG_FILE   = ROOT / "scrape.log"

CACHE_DIR.mkdir(exist_ok=True)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE),
    ],
)
log = logging.getLogger("we3-scraper")

# ── Retry wrapper ─────────────────────────────────────────────────────────────
@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(log, logging.WARNING),
)
def _fill_author(author_stub):
    return scholarly.fill(author_stub, sections=["basics", "publications", "indices"])


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=4, max=60),
    retry=retry_if_exception_type(Exception),
    before_sleep=before_sleep_log(log, logging.WARNING),
)
def _fill_pub(pub_stub):
    return scholarly.fill(pub_stub)


# ── Cache helpers ─────────────────────────────────────────────────────────────
def _cache_path(scholar_id: str) -> Path:
    return CACHE_DIR / f"{scholar_id}.json"


def _load_cache(scholar_id: str):
    p = _cache_path(scholar_id)
    if p.exists():
        with p.open() as f:
            return json.load(f)
    return None


def _save_cache(scholar_id: str, data: dict):
    with _cache_path(scholar_id).open("w") as f:
        json.dump(data, f, indent=2, default=str)


# ── Scholar fetch ─────────────────────────────────────────────────────────────
def fetch_author(member: dict, force: bool, max_pubs: int) -> dict | None:
    name        = member["name"]
    scholar_id  = member.get("scholar_id", "").strip()

    # Derive ID from URL if not given directly
    if not scholar_id and member.get("scholar_url"):
        url = member["scholar_url"]
        if "user=" in url:
            scholar_id = url.split("user=")[1].split("&")[0]

    if not scholar_id:
        # Name-based search fallback — less reliable
        log.warning(f"{name}: no Scholar ID, attempting name search (may be inaccurate)")
        try:
            search_results = list(scholarly.search_author(name))
            if not search_results:
                log.warning(f"{name}: no Scholar profile found, skipping")
                return None
            # Take the first hit — labelled as a guess
            author_stub = search_results[0]
            scholar_id  = author_stub.get("scholar_id", name.replace(" ", "_"))
        except Exception as e:
            log.error(f"{name}: search failed — {e}")
            return None
    else:
        author_stub = scholarly.search_author_id(scholar_id)

    # Use cached result unless --force
    if not force:
        cached = _load_cache(scholar_id)
        if cached:
            log.info(f"{name}: loaded from cache ({len(cached.get('publications', []))} pubs)")
            return cached

    log.info(f"{name}: fetching from Google Scholar …")
    try:
        author = _fill_author(author_stub)
    except Exception as e:
        log.error(f"{name}: failed to fetch author — {e}")
        return None

    pubs_raw = author.get("publications", [])
    if max_pubs:
        pubs_raw = pubs_raw[:max_pubs]

    publications = []
    for pub_stub in tqdm(pubs_raw, desc=f"  {name} pubs", leave=False):
        try:
            pub = _fill_pub(pub_stub)
            bib = pub.get("bib", {})
            publications.append({
                "title":       bib.get("title", ""),
                "authors":     bib.get("author", ""),
                "venue":       bib.get("journal") or bib.get("booktitle") or bib.get("venue") or "",
                "year":        bib.get("pub_year") or bib.get("year") or "",
                "abstract":    bib.get("abstract", ""),
                "url":         pub.get("pub_url") or pub.get("eprint_url") or "",
                "citations":   pub.get("num_citations", 0),
                "scholar_url": pub.get("author_pub_id", ""),
            })
            # Polite delay between individual pub fetches
            time.sleep(1.5)
        except Exception as e:
            log.warning(f"  Could not fill pub — {e}")

    result = {
        "name":          name,
        "role":          member.get("role", ""),
        "group":         member.get("group", ""),
        "scholar_id":    scholar_id,
        "scholar_url":   f"https://scholar.google.com/citations?user={scholar_id}",
        "affiliation":   author.get("affiliation", ""),
        "h_index":       author.get("hindex", ""),
        "citations":     author.get("citedby", ""),
        "interests":     author.get("interests", []),
        "publications":  publications,
        "scraped_at":    datetime.utcnow().isoformat(),
    }

    _save_cache(scholar_id, result)
    log.info(f"{name}: saved {len(publications)} publications")

    # Polite delay between authors
    time.sleep(4)
    return result


# ── Deduplication ─────────────────────────────────────────────────────────────
def _normalize_title(t: str) -> str:
    return "".join(c.lower() for c in t if c.isalnum())


def deduplicate(all_pubs: list[dict]) -> list[dict]:
    seen     = {}  # norm_title → index in result
    result   = []

    for pub in all_pubs:
        key = _normalize_title(pub.get("title", ""))
        if not key:
            result.append(pub)
            continue
        if key in seen:
            # Merge: keep higher citation count, accumulate authors
            existing = result[seen[key]]
            if pub.get("citations", 0) > existing.get("citations", 0):
                existing["citations"] = pub["citations"]
            # Merge contributor list (which lab member authored this)
            existing.setdefault("lab_authors", [])
            for a in pub.get("lab_authors", []):
                if a not in existing["lab_authors"]:
                    existing["lab_authors"].append(a)
        else:
            pub.setdefault("lab_authors", [])
            seen[key] = len(result)
            result.append(pub)

    return result


# ── Aggregation ───────────────────────────────────────────────────────────────
GROUP_LABELS = {
    "energy-flexibility": "Energy Flexibility",
    "water-systems":      "Water Systems Planning",
    "separations":        "Separations Technologies",
    None:                 "Other",
    "":                   "Other",
}


def aggregate(member_records: list[dict]) -> dict:
    all_pubs = []

    for record in member_records:
        for pub in record.get("publications", []):
            pub_copy = dict(pub)
            pub_copy["lab_authors"] = [record["name"]]
            pub_copy["_source_group"] = record.get("group") or ""
            all_pubs.append(pub_copy)

    all_pubs = deduplicate(all_pubs)

    # Sort by year desc, then citations desc
    def sort_key(p):
        try:
            y = int(p.get("year") or 0)
        except ValueError:
            y = 0
        return (-y, -(p.get("citations") or 0))

    all_pubs.sort(key=sort_key)

    # Build per-group and per-year indices
    by_group = {}
    by_year  = {}

    for pub in all_pubs:
        group = pub.get("_source_group") or ""
        label = GROUP_LABELS.get(group, "Other")
        by_group.setdefault(label, []).append(pub)

        year = str(pub.get("year") or "Unknown")
        by_year.setdefault(year, []).append(pub)

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total":        len(all_pubs),
        "all":          all_pubs,
        "by_group":     by_group,
        "by_year":      by_year,
    }


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Scrape Google Scholar for WE3 Lab publications")
    parser.add_argument("--member",   help="Scrape only this member (by name)")
    parser.add_argument("--force",    action="store_true", help="Ignore cached results")
    parser.add_argument("--proxy",    action="store_true", help="Use free proxy pool (slower, avoids rate limits)")
    parser.add_argument("--max-pubs", type=int, default=100, help="Max publications per author (default 100)")
    parser.add_argument("--no-fill",  action="store_true", help="Skip filling individual pub details (faster, less data)")
    args = parser.parse_args()

    if args.proxy:
        log.info("Setting up free proxy pool …")
        pg = ProxyGenerator()
        pg.FreeProxies()
        scholarly.use_proxy(pg)

    with MEMBERS.open() as f:
        config = json.load(f)

    members = config["members"]
    if args.member:
        members = [m for m in members if m["name"].lower() == args.member.lower()]
        if not members:
            sys.exit(f"Member '{args.member}' not found in members.json")

    records = []
    for member in members:
        record = fetch_author(member, force=args.force, max_pubs=args.max_pubs)
        if record:
            records.append(record)

    if not records:
        log.error("No records retrieved. Check Scholar IDs in members.json.")
        sys.exit(1)

    output = aggregate(records)
    output["members"] = [
        {
            "name":        r["name"],
            "role":        r["role"],
            "group":       r["group"],
            "scholar_id":  r["scholar_id"],
            "h_index":     r.get("h_index", ""),
            "citations":   r.get("citations", ""),
            "pub_count":   len(r.get("publications", [])),
        }
        for r in records
    ]

    with OUTPUT.open("w") as f:
        json.dump(output, f, indent=2, default=str)

    log.info(
        f"\nDone. {output['total']} unique publications from {len(records)} authors "
        f"→ {OUTPUT}"
    )
    log.info("Run  python3 build_publications_page.py  to generate the HTML page.")


if __name__ == "__main__":
    main()
