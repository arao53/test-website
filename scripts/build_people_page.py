#!/usr/bin/env python3
"""Reads members.json and writes the people section into people.html."""

import json
import re
from pathlib import Path

MEMBERS_JSON   = Path("members/members.json")
SUBGROUPS_JSON = Path("research/subgroups.json")
PEOPLE_HTML    = Path("people.html")

ROLE_ORDER = ["PI", "postdoc", "phd student", "ms student", "undergrad", "staff", "alumni"]

def _create_placeholder(entry):
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
    <h2 class="text-navy">Group Members</h2>
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


def _load_subgroups():
    entries = json.loads(SUBGROUPS_JSON.read_text())["subgroups"]
    for e in entries:
        if not Path(e["file"]).exists():
            _create_placeholder(e)
    urls   = {e["key"]: e["file"]  for e in entries}
    labels = {e["key"]: e["label"] for e in entries}
    return urls, labels

GROUP_URLS, GROUP_LABELS = _load_subgroups()
SECTION_LABEL = {
    "PI":          "Principal Investigator",
    "postdoc":     "Postdoctoral Researchers",
    "phd student": "PhD Students",
    "ms student":  "MS Students",
    "undergrad":   "Undergraduate Researchers",
    "staff":       "Lab Staff",
    "alumni":      "Alumni",
}
ROLE_DISPLAY = {
    "PI":          "Principal Investigator",
    "postdoc":     "Postdoctoral Researcher",
    "phd student": "PhD Student",
    "ms student":  "MS Student",
    "undergrad":   "Undergraduate Researcher",
    "staff":       "Lab Staff",
}
AV_COUNT = 8


def initials(name):
    clean = re.sub(r"^Dr\.\s+", "", name, flags=re.IGNORECASE).strip()
    parts = clean.split()
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def avatar_html(m, av, extra_style=""):
    clean = re.sub(r"^Dr\.\s+", "", m["name"], flags=re.IGNORECASE).strip()
    slug = (re.sub(" ", "",clean)).lower() + ".png"
    img_path = Path("members/images") / slug
    style_attr = f' style="{extra_style}"' if extra_style else ""
    if img_path.exists():
        return f'<div class="person-avatar {av}"{style_attr}><img src="members/images/{slug}" alt="{m["name"]}"></div>'
    return f'<div class="person-avatar {av}"{style_attr}>{initials(m["name"])}</div>'


def build_links(m):
    parts = []
    scholar_url = m.get("scholar_url") or (
        f"https://scholar.google.com/citations?user={m['scholar_id']}"
        if m.get("scholar_id") else ""
    )
    if scholar_url:
        parts.append(f'<a href="{scholar_url}" target="_blank" rel="noopener" title="Google Scholar"><i class="fa-brands fa-google-scholar"></i></a>')
    if m.get("linkedin"):
        parts.append(f'<a href="{m["linkedin"]}" target="_blank" rel="noopener" title="LinkedIn"><i class="fa-brands fa-linkedin"></i></a>')
    if m.get("website"):
        parts.append(f'<a href="{m["website"]}" target="_blank" rel="noopener">Web</a>')
    if m.get("cv"):
        parts.append(f'<a href="{m["cv"]}" target="_blank" rel="noopener">CV</a>')
    if m.get("email"):
        parts.append(f'<a href="mailto:{m["email"]}">Email</a>')
    return " &middot; ".join(parts)


def card_pi(m, av):
    links = build_links(m)
    bio   = m.get("bio", "")
    html  = f'''      <div class="person-card" style="display:flex;gap:1.5rem;text-align:left;padding:1.75rem;align-items:flex-start">
        {avatar_html(m, av, "width:90px;height:90px;font-size:1.5rem;flex-shrink:0")}
        <div>
          <h4>{m["name"]}</h4>
          <div class="role">Principal Investigator</div>'''
    if bio:
        html += f'\n          <p class="research-area" style="margin-top:.35rem">{bio}</p>'
    if links:
        html += f'\n          <div class="links" style="justify-content:flex-start;margin-top:.75rem">{links}</div>'
    html += "\n        </div>\n      </div>"
    return html


def card_alumni(m, av):
    degree_year = m.get("degree_year", "")
    placement   = m.get("placement", "")
    html = f'      <div class="person-card alumni-card">\n'
    html += f'        {avatar_html(m, av)}\n'
    html += '        <div class="info">\n'
    html += f'          <h4>{m["name"]}</h4>\n'
    if degree_year:
        html += f'          <span class="role">{degree_year}</span>\n'
    if placement:
        html += f'          <span class="placement">&rarr; {placement}</span>\n'
    html += "        </div>\n      </div>"
    return html


def card_member(m, av):
    role_text = m.get("role_label") or ROLE_DISPLAY.get(m["role"], m["role"])
    groups = m.get("groups") or []
    links = build_links(m)
    html  = f'      <div class="person-card">\n'
    html += f'        {avatar_html(m, av)}\n'
    html += f'        <h4>{m["name"]}</h4>\n'
    html += f'        <div class="role">{role_text}</div>\n'
    if groups:
        tags = "".join(
            f'<a href="{GROUP_URLS.get(g.lower(), "#")}" class="group-tag">{GROUP_LABELS.get(g.lower(), g.title())}</a>'
            for g in groups
        )
        html += f'        <div class="group-tags">{tags}</div>\n'
    elif m.get("research_area"):
        html += f'        <p class="research-area">{m["research_area"]}</p>\n'
    if links:
        html += f'        <div class="links">{links}</div>\n'
    html += "      </div>"
    return html


def last_name(m):
    clean = re.sub(r"^Dr\.\s+", "", m["name"], flags=re.IGNORECASE).strip()
    return clean.split()[-1].lower()


def render_section(role, members, av_idx):
    if not members:
        return "", av_idx
    if role != "PI":
        members = sorted(members, key=last_name)
    label    = SECTION_LABEL.get(role, role)
    is_pi    = role == "PI"
    is_alumni = role == "alumni"
    grid_class = "people-grid alumni-grid" if is_alumni else "people-grid"
    grid_style = ' style="grid-template-columns:repeat(auto-fill,minmax(240px,1fr))"' if is_pi else ""

    lines = [f'    <h2 class="people-section-title">{label}</h2>',
             f'    <div class="{grid_class}"{grid_style}>']
    for m in members:
        av = f"av-{(av_idx % AV_COUNT) + 1}"
        av_idx += 1
        if is_pi:
            lines.append(card_pi(m, av))
        elif is_alumni:
            lines.append(card_alumni(m, av))
        else:
            lines.append(card_member(m, av))
    lines.append("    </div>")
    return "\n".join(lines), av_idx


def main():
    data    = json.loads(MEMBERS_JSON.read_text())
    members = data.get("members", [])

    groups = {r.lower(): [] for r in ROLE_ORDER}
    for m in members:
        key = m["role"].lower()
        if key not in groups:
            key = "staff"
        groups[key].append(m)

    sections, av_idx = [], 0
    for role in ROLE_ORDER:
        html, av_idx = render_section(role, groups[role.lower()], av_idx)
        if html:
            sections.append(html)

    generated = "\n".join(sections)

    original = PEOPLE_HTML.read_text()
    updated  = re.sub(
        r"(<!-- BEGIN:people-generated -->).*?(<!-- END:people-generated -->)",
        f"\\1\n{generated}\n    \\2",
        original,
        flags=re.DOTALL,
    )
    PEOPLE_HTML.write_text(updated)
    print(f"Updated {PEOPLE_HTML} with {len(members)} members.")


if __name__ == "__main__":
    main()
