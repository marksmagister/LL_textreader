#!/usr/bin/env bash
# Optional. Fetch Literata (OFL) for the reader — it has real Cyrillic, which
# system serif stacks do not. Not vendored; see NOTICE. Without it the CSS
# falls back to Georgia and nothing breaks.
set -euo pipefail

dest="frontend/public/fonts"
mkdir -p "$dest"
url="https://github.com/google/fonts/raw/main/ofl/literata/Literata%5Bopsz%2Cwght%5D.ttf"

echo "Fetching Literata…"
curl -L --retry 5 --retry-all-errors --progress-bar -o "$dest/literata.ttf" "$url"
echo "Saved to $dest/literata.ttf"
