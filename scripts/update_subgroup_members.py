#!/usr/bin/env python3
"""
Reads members/members.json and updates the Group Members section
in each research subgroup HTML file.
"""

import json
import re
from pathlib import Path

def _create_placeholder(entry: dict) -> None:
    path  = Path(entry["file"])
    label = entry["label"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{label} — WE3 Lab</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../assets/css/style.css" />
</head>
<body>

<nav class="nav">
  <div class="container">
    <a class="nav-logo" href="../index.html">
      <img src="../assets/logos/stanfordlogo.png" alt="Stanford logo" height="64">
    </a>
    <button class="nav-hamburger" aria-label="Toggle navigation" aria-expanded="false">
      <span></span><span></span><span></span>
    </button>
    <ul class="nav-links">
      <li><a href="../index.html">Overview</a></li>
      <li><a href="../research.html">Research</a></li>
      <li><a href="../people.html">People</a></li>
      <li><a href="../funding.html">Funding</a></li>
      <li><a href="../contact.html">Contact</a></li>
    </ul>
  </div>
</nav>

<div class="page-header">
  <div class="container">
    <div class="breadcrumb"><a href="../research.html">Research</a> &rsaquo; {label}</div>
    <h1>{label}</h1>
    <p>This page is under development.</p>
  </div>
</div>

<section class="section">
  <div class="container">
    <!-- Team -->
    <h2 class="text-navy">Group Members</h2>
    <div style="display:flex;flex-wrap:wrap;gap:1rem">
      <p style="color:var(--gray-500);font-size:.875rem">No members currently assigned to this group.</p>
    </div>
  </div>
</section>

<footer>
  <div class="container">
    <div class="footer-inner">
      <div>
        <div class="footer-logo">WE3<span>Lab</span></div>
        <p style="margin-top:.4rem;font-size:.8rem">Department of Civil &amp; Environmental Engineering<br>Stanford University</p>
      </div>
      <nav class="footer-links">
        <a href="../index.html">Overview</a>
        <a href="../research.html">Research</a>
        <a href="../people.html">People</a>
        <a href="../contact.html">Contact</a>
      </nav>
      <p style="font-size:.8rem">&copy; 2026 WE3 Lab. All rights reserved.</p>
    </div>
  </div>
</footer>

</body>
</html>
''')
    print(f"  CREATED  {entry['file']} (placeholder page for '{entry['key']}')")


def _load_group_to_file() -> dict[str, Path]:
    entries = json.loads(Path("research/subgroups.json").read_text())["subgroups"]
    for e in entries:
        if not Path(e["file"]).exists():
            _create_placeholder(e)
    return {e["key"]: Path(e["file"]) for e in entries}

GROUP_TO_FILE = _load_group_to_file()

ROLE_LABEL = {
    "pi":                     "Principal Investigator",
    "postdoc":                "Postdoctoral Researcher",
    "phd student":            "PhD Student",
    "ms student":             "MS Student",
    "undergraduate":          "Undergraduate Researcher",
    "undergraduate researcher":"Undergraduate Researcher",
    "staff":                  "Research Staff",
}

ROLE_ORDER = ["pi", "postdoc", "phd student", "ms student", "undergraduate", "undergraduate researcher", "staff"]


def role_sort_key(member: dict) -> tuple:
    raw = member.get("role", "").strip().lower()
    order = ROLE_ORDER.index(raw) if raw in ROLE_ORDER else len(ROLE_ORDER)
    last_name = member["name"].strip().split()[-1].lower()
    return (order, last_name)

SECTION_RE = re.compile(
    r'(<!-- Team -->\s*\n\s*<h2[^>]*>Group Members</h2>\s*\n\s*)'
    r'<div style="display:flex;flex-wrap:wrap;gap:1rem">'
    r'.*?'
    r'\n    </div>',   # matches outer container close (4-space indent, not 6-space inner cards)
    re.DOTALL,
)


def role_label(raw: str) -> str:
    return ROLE_LABEL.get(raw.strip().lower(), raw.strip().title())


def make_card(member: dict) -> str:
    name = member["name"]
    label = role_label(member.get("role", ""))
    return (
        f'      <div style="background:var(--gray-50);border:1px solid var(--gray-200);'
        f'border-radius:var(--radius);padding:.75rem 1.25rem;font-size:.875rem">\n'
        f'        <strong style="color:var(--navy)">{name}</strong>'
        f' <span style="color:var(--teal)">· {label}</span>\n'
        f'      </div>'
    )


def build_section(prefix: str, cards: list[str]) -> str:
    inner = "\n".join(cards)
    return (
        f'{prefix}'
        f'<div style="display:flex;flex-wrap:wrap;gap:1rem">\n'
        f'{inner}\n'
        f'    </div>'
    )


def main():
    with open(Path("members/members.json")) as f:
        data = json.load(f)

    members = data["members"]

    # Group members by their subgroup(s)
    by_group: dict[str, list[dict]] = {g: [] for g in GROUP_TO_FILE}
    for m in members:
        for g in m.get("groups", []):
            key = g.strip().lower()
            if key in by_group:
                by_group[key].append(m)

    for group, html_path in GROUP_TO_FILE.items():
        group_members = by_group[group]
        html = html_path.read_text()

        if not SECTION_RE.search(html):
            print(f"  SKIP  {html_path.name} (no Group Members section found)")
            continue

        if not group_members:
            cards = ['      <p style="color:var(--gray-500);font-size:.875rem">No members currently assigned to this group.</p>']
        else:
            cards = [make_card(m) for m in sorted(group_members, key=role_sort_key)]

        def replacer(m):
            return build_section(m.group(1), cards)

        new_html, n = SECTION_RE.subn(replacer, html)
        if n == 0:
            print(f"  SKIP  {html_path.name} (regex did not match)")
            continue

        html_path.write_text(new_html)
        print(f"  OK    {html_path.name} — {len(group_members)} member(s)")


if __name__ == "__main__":
    main()
