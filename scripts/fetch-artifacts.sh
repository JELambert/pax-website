#!/bin/bash
# fetch-artifacts.sh — Download latest registry artifacts from pax-market releases
#
# Downloads registry.json, constructs.json, full-catalog.json, pack archives,
# and PAX_CREATION_GUIDE.md / PAX_USAGE_GUIDE.md from the latest GitHub Release
# on JELambert/pax-market.
#
# Uses curl (no gh CLI auth required — pax-market is a public repo).
#
# Usage:
#   scripts/fetch-artifacts.sh

set -euo pipefail

REPO="JELambert/pax-market"
ARTIFACTS_DIR="${PAX_ARTIFACTS_DIR:-artifacts}"
STATIC_PAX_DIR="static/pax"

echo "Fetching latest registry artifacts from $REPO..."

mkdir -p "$ARTIFACTS_DIR" "$STATIC_PAX_DIR"

# Get download URLs from the latest release.
# Use GITHUB_TOKEN when present to avoid the 60/hr unauthenticated rate limit
# (shared runner IPs get exhausted quickly).
AUTH_ARGS=()
if [ -n "${GITHUB_TOKEN:-}" ]; then
    AUTH_ARGS=(-H "Authorization: Bearer $GITHUB_TOKEN")
fi
RELEASE_JSON=$(curl -sL "${AUTH_ARGS[@]}" "https://api.github.com/repos/$REPO/releases/latest")
if echo "$RELEASE_JSON" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'assets' in d" 2>/dev/null; then
    URLS=$(echo "$RELEASE_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for asset in data.get('assets', []):
    print(asset['browser_download_url'])
")
else
    echo "ERROR: Could not fetch release data from $REPO"
    echo "$RELEASE_JSON" | head -5
    exit 1
fi

# Download each asset
for url in $URLS; do
    filename=$(basename "$url")
    echo "  Downloading $filename..."
    curl -sL "$url" -o "$ARTIFACTS_DIR/$filename"
done

# Verify required files. PAX_*.md guides became release assets in pax-market#73
# (umbrella tracker pax-market#72) — both must be present.
for f in registry.json constructs.json full-catalog.json pax-archives.tar \
         PAX_CREATION_GUIDE.md PAX_USAGE_GUIDE.md; do
    if [ ! -f "$ARTIFACTS_DIR/$f" ]; then
        echo "ERROR: Missing $ARTIFACTS_DIR/$f"
        exit 1
    fi
done

# Validate guide markers — pax_schema.py in praxis parses these at import time.
# A guide without markers ships breakage downstream.
if ! grep -q '<!-- PAX_SCHEMA_START' "$ARTIFACTS_DIR/PAX_CREATION_GUIDE.md"; then
    echo "ERROR: PAX_CREATION_GUIDE.md missing PAX_SCHEMA_START marker"
    exit 1
fi
if ! grep -q '<!-- PAX_FIELDS_START' "$ARTIFACTS_DIR/PAX_CREATION_GUIDE.md"; then
    echo "ERROR: PAX_CREATION_GUIDE.md missing PAX_FIELDS_START marker"
    exit 1
fi

# Unpack pack archives into static/pax/
# Wipe existing archives first so pruned packs don't linger from prior runs.
echo "Unpacking pack archives..."
find "$STATIC_PAX_DIR" -maxdepth 1 -name '*.pax.tar.gz' -delete
tar -xf "$ARTIFACTS_DIR/pax-archives.tar" -C "$STATIC_PAX_DIR" --strip-components=1

# Copy data files
mkdir -p data
cp "$ARTIFACTS_DIR/registry.json" data/registry.json
cp "$ARTIFACTS_DIR/registry.json" static/registry.json
cp "$ARTIFACTS_DIR/constructs.json" data/constructs.json

# Copy PAX guides from release artifacts into static/ for download.
# pax-market is now the canonical home of both guides (migration #72).
# Praxis vendors its own copy via sync-guide.yml — we no longer read from
# /opt/praxis on the deploy host.
cp "$ARTIFACTS_DIR/PAX_CREATION_GUIDE.md" static/PAX_CREATION_GUIDE.md
cp "$ARTIFACTS_DIR/PAX_USAGE_GUIDE.md"    static/PAX_USAGE_GUIDE.md
echo "Copied PAX_CREATION_GUIDE.md and PAX_USAGE_GUIDE.md to static/"

PACK_COUNT=$(find "$STATIC_PAX_DIR" -name '*.pax.tar.gz' | wc -l)
echo "Done: $PACK_COUNT pack archives ready"
