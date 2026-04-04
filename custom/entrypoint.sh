#!/usr/bin/env bash
set -euo pipefail

# 1) Extract zip + copy assets into FRONTEND build static directory.
# Open WebUI rebuilds /app/backend/open_webui/static from /app/build/static on startup.
python3 - <<'PY'
import os
import zipfile
import shutil
import pathlib

zip_path = pathlib.Path("/custom/boxedai-branding.zip")
tmp = pathlib.Path("/tmp/boxedai-branding")
frontend_build_dir = pathlib.Path(os.environ.get("FRONTEND_BUILD_DIR", "/app/build"))
frontend_static = frontend_build_dir / "static"

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

frontend_static.mkdir(parents=True, exist_ok=True)
for name in files:
    src = tmp / name
    if src.exists():
        shutil.copy2(src, frontend_static / name)
PY

# 2) Patch env.py (remove suffix "(Open WebUI)") — idempotente
python3 - <<'PY'
import re, pathlib

p = pathlib.Path("/app/backend/open_webui/env.py")
s = p.read_text()

pattern = r"""\nif WEBUI_NAME != ['\"]Open WebUI['\"]:\n\s+WEBUI_NAME \+= ['\"] \(Open WebUI\)['\"]\n"""
patched = re.sub(pattern, "\n", s, flags=re.MULTILINE)

if patched != s:
    p.write_text(patched)
PY

exec bash start.sh
