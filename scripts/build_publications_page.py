#!/usr/bin/env python3
"""
WE3 Lab — Build publications.html from publications.json
Usage:
    python3 build_publications_page.py                        # uses publications.json
    python3 build_publications_page.py --data other.json      # custom data file
    python3 build_publications_page.py --min-citations 5      # filter low-cited pubs
    python3 build_publications_page.py --years 2022-2026      # year range filter
    python3 build_publications_page.py --min-year 2020        # since a year
"""

import argparse
import json
import sys
from pathlib import Path
from html import escape

ROOT    = Path(__file__).parent
INPUT   = ROOT / "publications.json"
OUTPUT  = ROOT.parent / "publications.html"

GROUP_COLORS = {
    "Energy Flexibility":          ("⚡", "#0f3443", "#134f5c"),
    "Water Systems Planning":      ("🏙️", "#0b3d2e", "#1a4a35"),
    "Separations Technologies":    ("🔬", "#2d1b54", "#3d2570"),
    "Other":                       ("📄", "#2a2a3a", "#3a3a4a"),
}

ROLE_ORDER = ["pi", "postdoc", "phd", "ms", "undergrad", "staff", "alumni"]
ROLE_LABELS = {
    "pi":       "Principal Investigator",
    "postdoc":  "Postdoctoral Researcher",
    "phd":      "PhD Student",
    "ms":       "MS Student",
    "undergrad":"Undergraduate",
    "staff":    "Research Staff",
    "alumni":   "Alumni",
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def esc(s) -> str:
    return escape(str(s or ""))


def author_links(authors_str: str, scholar_lookup: dict) -> str:
    """Wrap lab-member names in Scholar links where available."""
    parts = [a.strip() for a in authors_str.split(" and ") if a.strip()]
    linked = []
    for part in parts:
        match = next(
            (sid for name, sid in scholar_lookup.items() if name.lower() in part.lower()),
            None,
        )
        if match:
            url = f"https://scholar.google.com/citations?user={match}"
            linked.append(f'<a href="{url}" target="_blank" rel="noopener" class="author-link">{esc(part)}</a>')
        else:
            linked.append(esc(part))
    return ", ".join(linked)


def format_pub_card(pub: dict, scholar_lookup: dict) -> str:
    title     = esc(pub.get("title", "Untitled"))
    authors   = author_links(pub.get("authors", ""), scholar_lookup)
    venue     = esc(pub.get("venue", ""))
    year      = esc(pub.get("year", ""))
    citations = pub.get("citations") or 0
    url       = pub.get("url", "")
    abstract  = esc(pub.get("abstract", ""))
    lab_auths = pub.get("lab_authors", [])

    lab_tags = " ".join(
        f'<span class="pub-lab-tag">{esc(a)}</span>'
        for a in lab_auths
    )

    cite_badge = (
        f'<span class="pub-citations" title="Cited by {citations}">'
        f'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .757-2 2v11c0 1 .5 2 2 2h2c1.25 0 2-.757 2-2v-1M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .757-2 2v11c0 1 .5 2 2 2h2c1.25 0 2-.757 2-2v-1"/></svg>'
        f' {citations} citations</span>'
    ) if citations else ""

    link_btn = (
        f'<a href="{esc(url)}" target="_blank" rel="noopener" class="pub-link">View &rarr;</a>'
    ) if url else ""

    abstract_block = (
        f'<details class="pub-abstract"><summary>Abstract</summary><p>{abstract}</p></details>'
    ) if abstract else ""

    return f"""
      <div class="pub-card" data-year="{esc(str(pub.get('year','')))}" data-citations="{citations}">
        <div class="pub-meta">
          <span class="pub-year">{esc(year)}</span>
          {cite_badge}
        </div>
        <h4 class="pub-title">{title}</h4>
        <p class="pub-authors">{authors}</p>
        {f'<p class="pub-venue"><em>{venue}</em></p>' if venue else ""}
        <div class="pub-footer">
          <div class="pub-lab-authors">{lab_tags}</div>
          {link_btn}
        </div>
        {abstract_block}
      </div>"""


def build_html(data: dict, filters: dict) -> str:
    all_pubs      = data.get("all", [])
    by_group      = data.get("by_group", {})
    by_year       = data.get("by_year", {})
    members_meta  = data.get("members", [])
    generated_at  = data.get("generated_at", "")[:10]

    # Scholar ID lookup for author hyperlinking
    scholar_lookup = {
        m["name"]: m["scholar_id"]
        for m in members_meta
        if m.get("scholar_id")
    }

    # Apply filters
    min_cite = filters.get("min_citations", 0)
    min_year = filters.get("min_year", 0)
    max_year = filters.get("max_year", 9999)

    def keep(pub):
        try:
            year = int(pub.get("year") or 0)
        except ValueError:
            year = 0
        if min_cite and (pub.get("citations") or 0) < min_cite:
            return False
        if min_year and year and year < min_year:
            return False
        if max_year < 9999 and year and year > max_year:
            return False
        return True

    visible_pubs = [p for p in all_pubs if keep(p)]

    # Year options for filter dropdown
    years = sorted(
        {str(p.get("year", "")) for p in visible_pubs if p.get("year")},
        reverse=True,
    )

    # Groups present in visible pubs
    visible_groups = {}
    for pub in visible_pubs:
        g = pub.get("_source_group") or ""
        from scrape_scholar import GROUP_LABELS
        label = GROUP_LABELS.get(g, "Other")
        visible_groups.setdefault(label, []).append(pub)

    # ── Stats ─────────────────────────────────────────────────────────────────
    total_cites  = sum(p.get("citations", 0) or 0 for p in visible_pubs)
    max_h        = max((m.get("h_index") or 0 for m in members_meta), default=0)

    # ── Members table rows ─────────────────────────────────────────────────────
    sorted_members = sorted(
        members_meta,
        key=lambda m: ROLE_ORDER.index(m.get("role", "phd")) if m.get("role") in ROLE_ORDER else 99,
    )
    member_rows = ""
    for m in sorted_members:
        sid = m.get("scholar_id", "")
        scholar_link = (
            f'<a href="https://scholar.google.com/citations?user={esc(sid)}" '
            f'target="_blank" rel="noopener">Profile</a>'
        ) if sid else "—"
        member_rows += f"""
          <tr>
            <td>{esc(m['name'])}</td>
            <td>{esc(ROLE_LABELS.get(m.get('role',''),''))}</td>
            <td>{esc(m.get('group','').replace('-',' ').title())}</td>
            <td style="text-align:right">{esc(str(m.get('pub_count','')))}</td>
            <td style="text-align:right">{esc(str(m.get('h_index','') or '—'))}</td>
            <td style="text-align:right">{esc(str(m.get('citations','') or '—'))}</td>
            <td>{scholar_link}</td>
          </tr>"""

    # ── By-group sections ──────────────────────────────────────────────────────
    group_sections = ""
    for group_label, pubs in by_group.items():
        filtered = [p for p in pubs if keep(p)]
        if not filtered:
            continue
        emoji, col1, col2 = GROUP_COLORS.get(group_label, ("📄", "#333", "#555"))
        group_id = group_label.lower().replace(" ", "-").replace("&", "")
        cards    = "".join(format_pub_card(p, scholar_lookup) for p in filtered)
        group_sections += f"""
        <div class="group-section" data-group="{esc(group_label)}">
          <div class="group-header" style="background:linear-gradient(135deg,{col1},{col2})">
            <span>{emoji}</span>
            <div>
              <h3>{esc(group_label)}</h3>
              <span class="group-count">{len(filtered)} publication{'s' if len(filtered)!=1 else ''}</span>
            </div>
          </div>
          <div class="pub-list" id="group-{group_id}">
            {cards}
          </div>
        </div>"""

    # ── HTML ──────────────────────────────────────────────────────────────────
    year_options = "\n".join(
        f'<option value="{esc(y)}">{esc(y)}</option>' for y in years
    )
    group_options = "\n".join(
        f'<option value="{esc(g)}">{esc(g)}</option>'
        for g in by_group.keys()
        if any(keep(p) for p in by_group[g])
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Publications — WE3 Lab</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="assets/css/style.css" />
  <style>
    /* ── Publication-specific styles ── */
    .filter-bar {{
      background: var(--white); border-bottom: 1px solid var(--gray-200);
      position: sticky; top: var(--nav-h); z-index: 50;
      padding: .85rem 0;
    }}
    .filter-inner {{
      display: flex; flex-wrap: wrap; gap: .6rem; align-items: center;
    }}
    .filter-inner select, .filter-inner input {{
      padding: .45rem .8rem; border: 1.5px solid var(--gray-200);
      border-radius: var(--radius); font-size: .85rem;
      font-family: var(--font); background: var(--white);
      outline: none; cursor: pointer;
    }}
    .filter-inner select:focus, .filter-inner input:focus {{
      border-color: var(--teal);
    }}
    .filter-label {{
      font-size: .8rem; font-weight: 600; color: var(--gray-500);
    }}
    .filter-sep {{ flex: 1; }}
    #pub-count-badge {{
      background: var(--teal); color: var(--white);
      font-size: .78rem; font-weight: 700;
      padding: .3rem .7rem; border-radius: 100px;
    }}

    .group-section {{ margin-bottom: 2.5rem; }}
    .group-header {{
      display: flex; align-items: center; gap: 1rem;
      color: white; padding: 1.25rem 1.5rem;
      border-radius: var(--radius-lg) var(--radius-lg) 0 0;
      font-size: 1.5rem;
    }}
    .group-header h3 {{ color: white; font-size: 1.1rem; margin-bottom: .15rem; }}
    .group-count {{ font-size: .8rem; opacity: .8; }}
    .pub-list {{ display: grid; gap: 1px; background: var(--gray-200); }}
    .pub-card {{
      background: var(--white); padding: 1.25rem 1.5rem;
      transition: background .15s;
    }}
    .pub-card:hover {{ background: var(--gray-50); }}
    .pub-card.hidden {{ display: none; }}

    .pub-meta {{ display: flex; gap: .75rem; align-items: center; margin-bottom: .4rem; flex-wrap: wrap; }}
    .pub-year {{ background: var(--navy); color: white; font-size: .72rem; font-weight: 700; padding: .2rem .55rem; border-radius: 4px; }}
    .pub-citations {{ font-size: .78rem; color: var(--gray-500); display: flex; align-items: center; gap: .3rem; }}
    .pub-title {{ font-size: .975rem; font-weight: 600; color: var(--navy); margin-bottom: .3rem; line-height: 1.4; }}
    .pub-authors {{ font-size: .85rem; color: var(--gray-700); margin-bottom: .25rem; }}
    .author-link {{ color: var(--teal); font-weight: 500; }}
    .pub-venue {{ font-size: .82rem; color: var(--gray-500); margin-bottom: .5rem; }}
    .pub-footer {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: .5rem; }}
    .pub-lab-authors {{ display: flex; flex-wrap: wrap; gap: .3rem; }}
    .pub-lab-tag {{ background: var(--gray-100); color: var(--navy); font-size: .72rem; font-weight: 600; padding: .2rem .55rem; border-radius: 100px; border: 1px solid var(--gray-200); }}
    .pub-link {{ font-size: .82rem; font-weight: 600; color: var(--teal); white-space: nowrap; }}
    .pub-abstract {{ margin-top: .75rem; font-size: .85rem; }}
    .pub-abstract summary {{ cursor: pointer; color: var(--teal); font-weight: 500; font-size: .82rem; }}
    .pub-abstract p {{ margin-top: .5rem; color: var(--gray-700); line-height: 1.6; }}

    /* Members table */
    .members-table {{ width: 100%; border-collapse: collapse; font-size: .875rem; margin-top: 1rem; }}
    .members-table th {{ background: var(--navy); color: white; padding: .6rem .85rem; text-align: left; font-size: .78rem; font-weight: 600; }}
    .members-table td {{ padding: .6rem .85rem; border-bottom: 1px solid var(--gray-200); }}
    .members-table tr:hover td {{ background: var(--gray-50); }}
    .members-table a {{ color: var(--teal); font-weight: 500; }}

    /* No-results */
    #no-results {{ display: none; text-align: center; padding: 3rem; color: var(--gray-500); }}
  </style>
</head>
<body>

<!-- ── Navigation ───────────────────────────────────────── -->
<nav class="nav">
  <div class="container">
    <a class="nav-logo" href="index.html">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <circle cx="14" cy="14" r="13" stroke="#3a9aaa" stroke-width="2"/>
        <path d="M7 10l3.5 8L14 12l3.5 6L21 10" stroke="#3a9aaa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      WE3<span>Lab</span>
    </a>
    <button class="nav-hamburger" aria-label="Toggle navigation" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
    <ul class="nav-links">
      <li><a href="index.html">Overview</a></li>
      <li><a href="research.html">Research</a></li>
      <li><a href="people.html">People</a></li>
      <li><a href="publications.html" class="active">Publications</a></li>
      <li><a href="contact.html">Contact</a></li>
    </ul>
  </div>
</nav>

<!-- ── Page Header ──────────────────────────────────────── -->
<div class="page-header">
  <div class="container">
    <h1>Publications</h1>
    <p>Scraped from Google Scholar and organized by research group. Updated {esc(generated_at)}.</p>
  </div>
</div>

<!-- ── Stats strip ──────────────────────────────────────── -->
<div class="stats-strip">
  <div class="container">
    <div class="stats-grid">
      <div><div class="stat-number">{len(visible_pubs)}</div><div class="stat-label">Total Publications</div></div>
      <div><div class="stat-number">{total_cites:,}</div><div class="stat-label">Total Citations</div></div>
      <div><div class="stat-number">{len(years)}</div><div class="stat-label">Years Covered</div></div>
      <div><div class="stat-number">{len(members_meta)}</div><div class="stat-label">Lab Members</div></div>
    </div>
  </div>
</div>

<!-- ── Filter bar ────────────────────────────────────────── -->
<div class="filter-bar">
  <div class="container">
    <div class="filter-inner">
      <span class="filter-label">Filter by:</span>

      <select id="filter-year" onchange="applyFilters()">
        <option value="">All Years</option>
        {year_options}
      </select>

      <select id="filter-group" onchange="applyFilters()">
        <option value="">All Groups</option>
        {group_options}
      </select>

      <input type="number" id="filter-min-cite" placeholder="Min citations"
             style="width:130px" onchange="applyFilters()" min="0" />

      <input type="search" id="filter-search" placeholder="Search title / author…"
             style="width:220px;flex:1;min-width:140px" oninput="applyFilters()" />

      <span class="filter-sep"></span>
      <span id="pub-count-badge">{len(visible_pubs)} shown</span>
      <button onclick="resetFilters()" class="btn" style="padding:.4rem .8rem;font-size:.82rem;background:var(--gray-100);color:var(--gray-700);border:1px solid var(--gray-200)">Reset</button>
    </div>
  </div>
</div>

<!-- ── Main content ──────────────────────────────────────── -->
<section class="section">
  <div class="container">

    <!-- Group-organized publications -->
    <div id="publications-container">
      {group_sections}
    </div>
    <div id="no-results">No publications match your filters.</div>

    <!-- Member stats table -->
    <details style="margin-top:3rem">
      <summary style="cursor:pointer;font-weight:700;color:var(--navy);font-size:1.1rem;padding:.75rem 0;border-top:2px solid var(--gray-200)">
        Lab Member Scholar Stats
      </summary>
      <div style="overflow-x:auto;margin-top:1rem">
        <table class="members-table">
          <thead>
            <tr>
              <th>Name</th><th>Role</th><th>Group</th>
              <th style="text-align:right">Pubs (scraped)</th>
              <th style="text-align:right">h-index</th>
              <th style="text-align:right">Total Citations</th>
              <th>Scholar</th>
            </tr>
          </thead>
          <tbody>{member_rows}</tbody>
        </table>
      </div>
    </details>

  </div>
</section>

<!-- ── Footer ───────────────────────────────────────────── -->
<footer>
  <div class="container">
    <div class="footer-inner">
      <div>
        <div class="footer-logo">WE3<span>Lab</span></div>
        <p style="margin-top:.4rem;font-size:.8rem">Department of Civil &amp; Environmental Engineering<br>University • City, State</p>
      </div>
      <nav class="footer-links">
        <a href="index.html">Overview</a>
        <a href="research.html">Research</a>
        <a href="people.html">People</a>
        <a href="publications.html">Publications</a>
        <a href="contact.html">Contact</a>
      </nav>
      <p style="font-size:.8rem">&copy; 2026 WE3 Lab. All rights reserved.</p>
    </div>
  </div>
</footer>

<script src="assets/js/main.js"></script>
<script>
  // ── Client-side filtering ──────────────────────────────────────────────────
  function applyFilters() {{
    const year    = document.getElementById('filter-year').value;
    const group   = document.getElementById('filter-group').value;
    const minCite = parseInt(document.getElementById('filter-min-cite').value) || 0;
    const search  = document.getElementById('filter-search').value.toLowerCase().trim();

    let visible = 0;

    document.querySelectorAll('.group-section').forEach(section => {{
      const sectionGroup = section.dataset.group;
      let sectionHasVisible = false;

      section.querySelectorAll('.pub-card').forEach(card => {{
        const cardYear    = card.dataset.year;
        const cardCite    = parseInt(card.dataset.citations) || 0;
        const cardText    = card.textContent.toLowerCase();

        const yearOk   = !year    || cardYear === year;
        const groupOk  = !group   || sectionGroup === group;
        const citeOk   = !minCite || cardCite >= minCite;
        const searchOk = !search  || cardText.includes(search);

        if (yearOk && groupOk && citeOk && searchOk) {{
          card.classList.remove('hidden');
          sectionHasVisible = true;
          visible++;
        }} else {{
          card.classList.add('hidden');
        }}
      }});

      section.style.display = sectionHasVisible ? '' : 'none';
    }});

    document.getElementById('pub-count-badge').textContent = visible + ' shown';
    document.getElementById('no-results').style.display = visible === 0 ? 'block' : 'none';
  }}

  function resetFilters() {{
    document.getElementById('filter-year').value     = '';
    document.getElementById('filter-group').value    = '';
    document.getElementById('filter-min-cite').value = '';
    document.getElementById('filter-search').value   = '';
    applyFilters();
  }}
</script>
</body>
</html>"""


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Build publications.html from publications.json")
    parser.add_argument("--data",          default=str(INPUT),  help="Input JSON file")
    parser.add_argument("--out",           default=str(OUTPUT), help="Output HTML file")
    parser.add_argument("--min-citations", type=int, default=0, help="Exclude pubs below this citation count")
    parser.add_argument("--min-year",      type=int, default=0, help="Earliest year to include")
    parser.add_argument("--max-year",      type=int, default=9999, help="Latest year to include")
    parser.add_argument("--years",         help="Shortcut: year range, e.g. 2020-2026")
    args = parser.parse_args()

    if args.years:
        try:
            y1, y2 = args.years.split("-")
            args.min_year = int(y1)
            args.max_year = int(y2)
        except ValueError:
            sys.exit("--years must be in format YYYY-YYYY, e.g. 2020-2026")

    data_path = Path(args.data)
    if not data_path.exists():
        sys.exit(f"Data file not found: {data_path}\nRun scrape_scholar.py first.")

    with data_path.open() as f:
        data = json.load(f)

    filters = {
        "min_citations": args.min_citations,
        "min_year":      args.min_year,
        "max_year":      args.max_year,
    }

    html = build_html(data, filters)

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(html)

    total = data.get("total", 0)
    print(f"Built {out_path}  ({total} publications)")


if __name__ == "__main__":
    main()
