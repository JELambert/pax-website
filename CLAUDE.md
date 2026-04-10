# PAX Website

## What This Is
Hugo static site + FastAPI upload service for pax-market.com. This repo is the **frontend only** — pack data comes from the [pax-market](https://github.com/JELambert/pax-market) registry via GitHub Releases.

**Live at [pax-market.com](https://pax-market.com)**

## Architecture
```
Registry (pax-market repo)
  → publish-artifacts.yml creates GitHub Release on push to main
  → Release contains: registry.json, constructs.json, full-catalog.json, pax-archives.tar

Website (this repo)
  → fetch-artifacts.sh downloads latest release
  → generate-content.py reads full-catalog.json, writes content/pax/*/index.md
  → hugo --minify builds static site
  → rsync to CT 110 (nginx + Cloudflare tunnel)
```

## Key Commands
- `bash scripts/fetch-artifacts.sh` — Download registry artifacts
- `python3 scripts/generate-content.py` — Generate Hugo content from catalog
- `hugo server` — Local dev server at localhost:1313
- `hugo --minify` — Production build

## Upload Service
FastAPI app at submit.pax-market.com. Accepts zip uploads, validates pack structure, creates PRs on the **pax-market** registry repo. Lives in `upload-service/`.

## Deploy
- **CT 105** = build server + upload service. Autodeploy timer polls every 5 min.
- **CT 110** = nginx serving /var/www/marketplace/ via Cloudflare tunnel
- Script: `scripts/ct105-autodeploy.sh`

## Generated Files (not committed)
These are created by fetch-artifacts.sh + generate-content.py at build time:
- `content/pax/` — Hugo content pages for each pack
- `static/pax/*.pax.tar.gz` — Pack download archives
- `data/registry.json` — Registry install contract
- `data/constructs.json` — Cross-pack construct index
- `static/registry.json` — Served at site root
- `artifacts/` — Raw downloaded release files

## Project Structure
```
layouts/                  Hugo templates
content/                  Static pages (about, guide, showcase, etc.)
content/pax/              GENERATED — pack pages from full-catalog.json
static/                   Static assets
static/pax/               GENERATED — .pax.tar.gz archives
data/                     GENERATED — registry.json, constructs.json
upload-service/           FastAPI upload app (submit.pax-market.com)
scripts/
  generate-content.py     Reads full-catalog.json → writes Hugo pages
  fetch-artifacts.sh      Downloads latest release from pax-market
  ct105-autodeploy.sh     Polls both repos, builds, deploys
  deploy.sh               Emergency local deploy
.github/workflows/
  deploy-website.yml      CI: build verification on push
```
