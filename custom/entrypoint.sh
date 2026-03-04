#!/usr/bin/env bash
set -euo pipefail

ZIP="/custom/boxedai-branding.zip"
STATIC="/app/backend/open_webui/static"
TMP="/tmp/boxedai-branding"
ENV_PY="/app/backend/open_webui/env.py"

# 1) Extract zip + copy assets in /static
python3 - <<'PY'
import zipfile, shutil, pathlib

zip_path = pathlib.Path("/custom/boxedai-branding.zip")
tmp = pathlib.Path("/tmp/boxedai-branding")
static = pathlib.Path("/app/backend/open_webui/static")

tmp.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(zip_path) as z:
    z.extractall(tmp)

files = [
    "logo.png","logo-testo.png",
    "favicon.ico","favicon.png","favicon-96x96.png","favicon-dark.png",
    "custom.css","site.webmanifest",
    "apple-touch-icon.png",
    "splash.png","splash-dark.png",
    "web-app-manifest-192x192.png","web-app-manifest-512x512.png",
    "enac-logo-bianco.png","enac-logo-blu.png",
]

for name in files:
    src = tmp / name
    if src.exists():
        shutil.copy2(src, static / name)
PY

# 2) Patch env.py (remove suffix "(Open WebUI)") — idempotente
python3 - <<'PY'
import re, pathlib

p = pathlib.Path("/app/backend/open_webui/env.py")
s = p.read_text()

pattern = r'\nif WEBUI_NAME != "Open WebUI":\n\s+WEBUI_NAME \+= " \(Open WebUI\)"\n'
patched = re.sub(pattern, "\n", s, flags=re.MULTILINE)

if patched != s:
    p.write_text(patched)
PY

exec bash start.sh
