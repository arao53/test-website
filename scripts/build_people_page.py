#!/usr/bin/env python3
"""Reads members.json and writes the people section into people.html."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
MEMBERS_JSON = ROOT / "scripts" / "members.json"
PEOPLE_HTML  = ROOT / "people.html"

ROLE_ORDER = ["PI", "postdoc", "phd student", "ms student", "undergrad", "staff", "alumni"]
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


def build_links(m):
    parts = []
    scholar_url = m.get("scholar_url") or (
        f"https://scholar.google.com/citations?user={m['scholar_id']}"
        if m.get("scholar_id") else ""
    )
    if scholar_url:
        parts.append(f'<a href="{scholar_url}" target="_blank" rel="noopener">Scholar</a>')
    if m.get("linkedin"):
        parts.append(f'<a href="{m["linkedin"]}" target="_blank" rel="noopener">LinkedIn</a>')
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
        <div class="person-avatar {av}" style="width:90px;height:90px;font-size:1.5rem;flex-shrink:0">{initials(m["name"])}</div>
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
    html += f'        <div class="person-avatar {av}">{initials(m["name"])}</div>\n'
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
    area   = m.get("research_area") or (
        ", ".join(g.capitalize() for g in groups) if groups else ""
    )
    links = build_links(m)
    html  = f'      <div class="person-card">\n'
    html += f'        <div class="person-avatar {av}">{initials(m["name"])}</div>\n'
    html += f'        <h4>{m["name"]}</h4>\n'
    html += f'        <div class="role">{role_text}</div>\n'
    if area:
        html += f'        <p class="research-area">{area}</p>\n'
    if links:
        html += f'        <div class="links">{links}</div>\n'
    html += "      </div>"
    return html


def render_section(role, members, av_idx):
    if not members:
        return "", av_idx
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
