@echo off
echo ========================================================
echo Deploying Hiroshima Corporate Open Data Whitepaper to Cloudflare Pages
echo ========================================================
set CLOUDFLARE_ACCOUNT_ID=962e06193ba3f440c220306b591d03d1
call npx wrangler pages deploy dist --project-name=hiroshima-opendata-whitepaper
pause
