#!/usr/bin/env bash
# WE3 Lab — full publications pipeline
# Usage:
#   ./run_pipeline.sh                   full run (uses cache)
#   ./run_pipeline.sh --force           ignore cache, re-scrape everything
#   ./run_pipeline.sh --proxy           use free proxy pool
#   ./run_pipeline.sh --min-year 2020   only show pubs from 2020+
#   ./run_pipeline.sh --min-citations 3 only show pubs with ≥3 citations

set -euo pipefail
cd "$(dirname "$0")"

SCRAPE_ARGS=()
BUILD_ARGS=()

# Pass through known flags to the right script
for arg in "$@"; do
  case "$arg" in
    --force|--proxy|--no-fill) SCRAPE_ARGS+=("$arg") ;;
    --min-year=*|--max-year=*|--years=*|--min-citations=*)
      BUILD_ARGS+=("$arg") ;;
    --min-year|--max-year|--years|--min-citations)
      # These come in pairs; handled below
      ;;
  esac
done

# Re-scan for paired args
args=("$@")
i=0
while [ $i -lt ${#args[@]} ]; do
  arg="${args[$i]}"
  case "$arg" in
    --min-year|--max-year|--years|--min-citations)
      BUILD_ARGS+=("$arg" "${args[$((i+1))]}")
      i=$((i+2))
      ;;
    *) i=$((i+1)) ;;
  esac
done

echo "═══════════════════════════════════════"
echo "  WE3 Lab Publications Pipeline"
echo "═══════════════════════════════════════"
echo ""

# 1. Install dependencies if not present
if ! python3 -c "import scholarly" 2>/dev/null; then
  echo "▶ Installing dependencies …"
  pip3 install -r requirements.txt -q
fi

# 2. Scrape
echo "▶ Scraping Google Scholar …"
python3 scrape_scholar.py "${SCRAPE_ARGS[@]+"${SCRAPE_ARGS[@]}"}"

# 3. Build HTML page
echo ""
echo "▶ Building publications.html …"
python3 build_publications_page.py "${BUILD_ARGS[@]+"${BUILD_ARGS[@]}"}"

echo ""
echo "✓ Done.  Open ../publications.html to view the result."
echo ""
echo "Tip: To update the nav, add a Publications link to the other pages:"
echo '     <li><a href="publications.html">Publications</a></li>'
