#!/usr/bin/env bash
set -e
echo "Deploying Hiroshima Corporate Open Data Whitepaper to Cloudflare Pages..."
if [ -z "$CLOUDFLARE_ACCOUNT_ID" ]; then
  export CLOUDFLARE_ACCOUNT_ID="962e06193ba3f440c220306b591d03d1"
fi
npx wrangler pages deploy dist --project-name=hiroshima-opendata-whitepaper
