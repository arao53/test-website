#!/usr/bin/env python3
"""
Reads members/members.json and updates the Group Members section
in each research subgroup HTML file.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent

GROUP_TO_FILE = {
    "energy flexibility":  ROOT / "research" / "energyflexibility.html",
    "infrastructure planning": ROOT / "research" / "infrastructureplanning.html",
    "separations":    ROOT / "research" / "separations.html",
    "water technology":    ROOT / "research" / "watertechnology.html",
}

ROLE_LABEL = {
    "pi":                     "Principal Investigator",
    "postdoc":                "Postdoctoral Researcher",
    "phd student":            "PhD Student",
    "ms student":             "MS Student",
    "undergraduate":          "Undergraduate Researcher",
    "undergraduate researcher":"Undergraduate Researcher",
    "staff":                  "Research Staff",
}

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
    members_path = ROOT / "members" / "members.json"
    with open(members_path) as f:
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
        if not html_path.exists():
            print(f"  SKIP  {html_path.name} (file not found)")
            continue

        group_members = by_group[group]
        html = html_path.read_text()

        if not SECTION_RE.search(html):
            print(f"  SKIP  {html_path.name} (no Group Members section found)")
            continue

        if not group_members:
            cards = ['      <p style="color:var(--gray-500);font-size:.875rem">No members currently assigned to this group.</p>']
        else:
            cards = [make_card(m) for m in group_members]

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
