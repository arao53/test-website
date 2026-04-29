# WE3Lab Website — Editing Guide

All routine content updates are made by editing JSON files and pushing to `main`. GitHub Actions rebuilds the affected HTML automatically (weekly on Sunday nights, or triggered manually).

---

## Triggering a rebuild manually

Go to **Actions → Update Site → Run workflow** in GitHub to rebuild immediately rather than waiting for the Sunday schedule.

---

## Adding or updating a lab member

Edit [`members/members.json`](members/members.json) and add or update an entry in the `members` array:

```json
{
  "name": "Jane Smith",
  "role": "phd student",
  "groups": ["energy flexibility", "infrastructure planning"],
  "scholar_id": "XXXXXXXXX",
  "scholar_url": "https://scholar.google.com/citations?user=XXXXXXXXX",
  "linkedin": "https://www.linkedin.com/in/janesmith/",
  "website": "",
  "cv": ""
}
```

**Valid roles:** `postdoc`, `phd student`, `ms student`, `undergrad`, `staff`, `alumni`

**Valid groups** (must match exactly): `energy flexibility`, `infrastructure planning`, `separations`, `water technology`

For **alumni**, add:
```json
"degree_year": "PhD 2024",
"placement": "Google DeepMind"
```

Push to `main`. The next GitHub Actions run regenerates `people.html` and all research subgroup pages.

---

## Adding a member photo

Photos are displayed automatically if a file named `{first}{last}.png` (lowercase, no spaces) exists in [`members/images/`](members/images/).

1. Crop the photo to a square (any resolution; 400×400px is fine).
2. Save it as e.g. `janesmith.png`.
3. Commit and push to `members/images/janesmith.png`.

No rebuild is needed — the build script picks up the image the next time it runs.

---

## Adding a news item to the front page

Edit [`assets/news.json`](assets/news.json) and prepend a new entry:

```json
{
  "date": "May 2026",
  "headline": "Paper accepted at Nature Water",
  "link": "https://example.com/paper"
}
```

Push to `main`. The front page loads `news.json` at runtime (no build step required), so the item appears immediately after the push.

---

## Adding a new research subgroup

This requires two small edits:

1. **Create the subgroup page** by copying an existing one (e.g. `research/separations.html`) and editing the title and description.

2. **Register the group in [`subgroups.json`](research/subgroups.json):**
   ```json
   { "key": "new group name", "label": "New Group Name", "file": "research/newgroup.html" }
   ```
   The build scripts read this file automatically — no Python edits needed. If the HTML file listed in `research/subgroups.json` does not exist, the scripts will exit with a 404 error identifying the missing page.

3. **Add members to the group** using the `groups` field in `members/members.json` (see above).

Push to `main` and trigger a manual workflow run.

---

## How the automation works

| File edited | What rebuilds | How |
|---|---|---|
| `members/members.json` | `people.html`, all `research/*.html` member lists | GitHub Actions runs `build_people_page.py` + `update_subgroup_members.py` |
| `members/images/*.png` | Nothing — images are served directly | Static file, no build needed |
| `assets/news.json` | Nothing — loaded client-side at runtime | Push and it's live |
| `research/*.html` (content) | Nothing | Edit directly |

The workflow runs **every Sunday at 6 pm PT** and can be triggered manually from the Actions tab.
