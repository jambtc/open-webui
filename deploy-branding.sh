#!/bin/bash
# deploy-branding.sh
# Installa il branding Boxed AI in open-webui su Docker (persistente tramite bind mount)
#
# Uso:
#   ./deploy-branding.sh                          # container default: open-webui
#   ./deploy-branding.sh altro-container-name
#
# Questo script:
#   1. Crea ./custom/ nella stessa cartella del docker-compose.yml
#   2. Copia i file di branding in ./custom/
#   3. Estrae env.py dal container, lo patcha (rimuove suffisso Open WebUI) e lo salva in ./custom/
#   4. Stampa le righe da aggiungere al docker-compose.yml
#   5. NON modifica docker-compose.yml automaticamente (operazione manuale dell'utente)
#
# Dopo aver aggiunto i volumi al compose, eseguire:
#   docker compose up -d
#
# Richiede permessi Docker (sudo o gruppo docker)

set -e

CONTAINER="${1:-open-webui}"
CONTAINER_STATIC="/app/backend/open_webui/static"
CONTAINER_ENV="/app/backend/open_webui/env.py"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ZIP="$SCRIPT_DIR/boxedai-branding.zip"
CUSTOM_DIR="$SCRIPT_DIR/custom"   # directory che verrà montata come volume

# Verifica prerequisiti
if [ ! -f "$ZIP" ]; then
    echo "Errore: file $ZIP non trovato."
    echo "Assicurati di eseguire lo script dalla stessa cartella del .zip"
    exit 1
fi

if ! docker inspect "$CONTAINER" > /dev/null 2>&1; then
    echo "Errore: container '$CONTAINER' non trovato o Docker non accessibile."
    echo "Prova con: sudo $0 $CONTAINER"
    exit 1
fi

echo "Container : $CONTAINER"
echo "Custom dir: $CUSTOM_DIR"
echo ""

# --- 1. PREPARA DIRECTORY HOST ---
echo "=== 1/3 Preparazione file statici in $CUSTOM_DIR ==="
mkdir -p "$CUSTOM_DIR"

# Estrae i file di branding in ./custom/
TMP=$(mktemp -d)
python3 -c "import zipfile, sys; zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$ZIP" "$TMP"

for f in "$TMP"/*.png "$TMP"/*.ico "$TMP"/custom.css "$TMP"/site.webmanifest; do
    [ -f "$f" ] || continue
    cp "$f" "$CUSTOM_DIR/$(basename "$f")"
    echo "  copiato: $(basename "$f")"
done
rm -rf "$TMP"

# --- 2. PATCHA env.py E SALVALO IN ./custom/ ---
echo ""
echo "=== 2/3 Patch env.py (rimuove suffisso Open WebUI) ==="

# Estrae env.py dal container (funziona solo se il container è running)
CONTAINER_RUNNING=$(docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null || echo "false")
if [ "$CONTAINER_RUNNING" = "true" ]; then
    docker cp "$CONTAINER:$CONTAINER_ENV" "$CUSTOM_DIR/env.py"
    echo "  estratto: env.py dal container"
elif [ -f "$CUSTOM_DIR/env.py" ]; then
    echo "  Container spento — uso env.py già presente in ./custom/"
else
    echo "  ERRORE: container spento e env.py non trovato in ./custom/"
    echo "  Avvia il container almeno una volta prima di eseguire questo script."
    exit 1
fi

# Applica la patch con python3
python3 - "$CUSTOM_DIR/env.py" <<'PYEOF'
import re, sys

path = sys.argv[1]
with open(path, "r") as f:
    content = f.read()

patched = re.sub(
    r'\nif WEBUI_NAME != "Open WebUI":\n    WEBUI_NAME \+= " \(Open WebUI\)"\n',
    "\n",
    content
)

if patched == content:
    print("  Nessuna modifica necessaria (patch già applicata)")
else:
    with open(path, "w") as f:
        f.write(patched)
    print("  Patch applicata: suffisso '(Open WebUI)' rimosso")
PYEOF

# site.webmanifest è già incluso nello zip (pre-patchato con name=Boxed AI)

# --- 4. STAMPA ISTRUZIONI docker-compose ---
echo ""
echo "=== 3/3 Istruzioni docker-compose ==="
echo ""
echo "Aggiungi questi bind mount alla sezione 'volumes' del servizio open-webui:"
echo ""
echo "    volumes:"
echo "      - ./data/open-webui:/app/backend/data"
echo "      - ./custom/env.py:$CONTAINER_ENV:ro"
for f in "$CUSTOM_DIR"/*.png "$CUSTOM_DIR"/*.ico "$CUSTOM_DIR"/custom.css "$CUSTOM_DIR"/site.webmanifest; do
    [ -f "$f" ] || continue
    fname="$(basename "$f")"
    echo "      - ./custom/$fname:$CONTAINER_STATIC/$fname:ro"
done

echo ""
echo "Poi esegui:"
echo "  docker compose up -d"
echo ""
echo "============================================"
echo "File pronti in: $CUSTOM_DIR"
ls "$CUSTOM_DIR"
echo "============================================"
