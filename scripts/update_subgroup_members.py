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
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" crossorigin="anonymous" />
</head>
<body>

<!-- ── Site Header (Sticky) ────────────────────────────── -->
<div class="site-header">
  <div class="identity-bar">
    <div class="container">
      <a href="https://www.stanford.edu">Stanford University</a>
    </div>
  </div>
  <nav class="nav">
    <div class="container">
      <a class="nav-logo" href="../index.html">
        <img src="../assets/logos/WE3_Lab_Logo_black.png" alt="WE3 Lab" height="48">
      </a>
      <button class="nav-hamburger" aria-label="Toggle navigation" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
      <ul class="nav-links">
        <li><a href="../index.html">Home</a></li>
        <li><a href="../people.html">Who We Are</a></li>
        <li class="dropdown">
          <a href="../research.html" class="active">What We Do</a>
          <ul class="dropdown-content">
            <li><a href="../research/energyflexibility.html">Energy Flexibility</a></li>
            <li><a href="../research/infrastructureplanning.html">Infrastructure Planning</a></li>
            <li><a href="../research/separations.html">Separations Technology</a></li>
          </ul>
        </li>
        <li><a href="../why-we-do-it.html">Why We Do It</a></li>
        <li><a href="../contact.html">Contact Us</a></li>
      </ul>
    </div>
  </nav>
</div>

<!-- ── Page Banner ─────────────────────────────────────── -->
<div class="page-banner">
  <div class="container">
    <div class="breadcrumb"><a href="../research.html">What We Do</a> &rsaquo; {label}</div>
    <h1>{label}</h1>
    <p>This page is under development.</p>
  </div>
</div>

<section class="section">
  <div class="container">
    <!-- Team -->
    <h2 class="text-deep-space" style="margin-top:3rem;margin-bottom:1.5rem">Group Members</h2>
    <div style="display:flex;flex-wrap:wrap;gap:1rem">
      <p style="color:var(--gray-500);font-size:.875rem">No members currently assigned to this group.</p>
    </div>
  </div>
</section>

<!-- ── WE3 Lab Footer ───────────────────────────────────── -->
<footer class="footer-we3">
  <div class="container">
    <div class="footer-inner">
      <div>
        <img src="../assets/logos/WE3_Lab_Logo_black.png" alt="WE3 Lab" height="40">
        <p class="footer-dept">Department of Civil &amp; Environmental Engineering<br>Stanford, CA</p>
      </div>
      <div class="footer-social">
        <a href="https://www.linkedin.com/company/we3-lab" target="_blank" rel="noopener" title="LinkedIn">
          <i class="fa-brands fa-linkedin"></i>
        </a>
        <a href="https://scholar.google.com/citations?user=04f-_PIAAAAJ&hl=en&oi=ao" target="_blank" rel="noopener" title="Google Scholar">
          <i class="fa-brands fa-google-scholar"></i>
        </a>
        <a href="https://github.com/we3lab" target="_blank" rel="noopener" title="GitHub">
          <i class="fa-brands fa-github"></i>
        </a>
        <a href="mailto:mauter@stanford.edu" title="Email">
          <i class="fa-solid fa-envelope"></i>
        </a>
      </div>
    </div>
  </div>
</footer>

<!-- ── Stanford Global Footer ──────────────────────────── -->
<footer class="footer-stanford">
  <div class="container">
    <div class="footer-stanford-inner">
      <div class="footer-stanford-logo">
        <a href="https://www.stanford.edu">Stanford<br>University</a>
      </div>
      <ul class="footer-stanford-links">
        <li><a href="https://www.stanford.edu">Stanford Home</a></li>
        <li><a href="https://visit.stanford.edu/plan/">Maps &amp; Directions</a></li>
        <li><a href="https://www.stanford.edu/search/">Search Stanford</a></li>
        <li><a href="https://emergency.stanford.edu">Emergency Info</a></li>
        <li><a href="https://www.stanford.edu/site/terms/">Terms of Use</a></li>
        <li><a href="https://www.stanford.edu/site/privacy/">Privacy</a></li>
        <li><a href="https://uit.stanford.edu/security/copyright-infringement">Copyright</a></li>
        <li><a href="https://adminguide.stanford.edu/chapter-1/subchapter-5/policy-1-5-4">Trademarks</a></li>
        <li><a href="https://studentservices.stanford.edu/more-resources/student-policies/non-academic/non-discrimination">Non-Discrimination</a></li>
        <li><a href="https://www.stanford.edu/site/accessibility">Accessibility</a></li>
      </ul>
      <p class="footer-stanford-copy">&copy; Stanford University.&nbsp; Stanford, California 94305.</p>
    </div>
  </div>
</footer>

<script>
  const btn = document.querySelector('.nav-hamburger');
  const links = document.querySelector('.nav-links');
  if (btn && links) {{
    btn.addEventListener('click', () => {{
      links.classList.toggle('open');
      btn.setAttribute('aria-expanded', links.classList.contains('open'));
    }});
  }}
</script>

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
        f'      <div style="background:var(--bright-snow);border:1px solid var(--gray-200);'
        f'border-radius:var(--radius);padding:.75rem 1.25rem;font-size:.875rem">\n'
        f'        <strong style="color:var(--deep-space)">{name}</strong>'
        f' <span style="color:var(--cerulean)">· {label}</span>\n'
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
        if m.get("role", "").strip().lower() == "alumni":
            continue
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
