# Deploy Branding Boxed AI — Procedura Operativa

File di riferimento: `custom/` (loghi, script, zip)
Documentazione concettuale: [deploy-concept.md](deploy-concept.md)

---

## Prima installazione (una tantum)

### 1. Carica sul server

Dal PC locale, nella cartella `custom/`:

```bash
cd /var/www/documents/progetti/openclaw/open-webui/custom
scp boxedai-branding.zip deploy-branding.sh root@SERVER:/home/node/mvp-ai/
```

### 2. Esegui lo script sul server

```bash
cd /home/node/mvp-ai
bash deploy-branding.sh
```

Lo script crea `./custom/` con tutti i file patchati e stampa i volumi da aggiungere al compose.

> Il container deve essere **running** alla prima esecuzione (serve per estrarre `env.py`).

### 3. Aggiungi i volumi al `docker-compose.yml`

Sezione `open-webui → volumes`:

```yaml
    volumes:
      - ./data/open-webui:/app/backend/data
      - ./custom/env.py:/app/backend/open_webui/env.py:ro
      - ./custom/logo.png:/app/backend/open_webui/static/logo.png:ro
      - ./custom/favicon.png:/app/backend/open_webui/static/favicon.png:ro
      - ./custom/favicon.ico:/app/backend/open_webui/static/favicon.ico:ro
      - ./custom/favicon-96x96.png:/app/backend/open_webui/static/favicon-96x96.png:ro
      - ./custom/favicon-dark.png:/app/backend/open_webui/static/favicon-dark.png:ro
      - ./custom/apple-touch-icon.png:/app/backend/open_webui/static/apple-touch-icon.png:ro
      - ./custom/splash.png:/app/backend/open_webui/static/splash.png:ro
      - ./custom/splash-dark.png:/app/backend/open_webui/static/splash-dark.png:ro
      - ./custom/web-app-manifest-192x192.png:/app/backend/open_webui/static/web-app-manifest-192x192.png:ro
      - ./custom/web-app-manifest-512x512.png:/app/backend/open_webui/static/web-app-manifest-512x512.png:ro
      - ./custom/custom.css:/app/backend/open_webui/static/custom.css:ro
      - ./custom/site.webmanifest:/app/backend/open_webui/static/site.webmanifest:ro
      - ./custom/enac-logo-bianco.png:/app/backend/open_webui/static/enac-logo-bianco.png:ro
      - ./custom/enac-logo-blu.png:/app/backend/open_webui/static/enac-logo-blu.png:ro
```

### 4. Applica

```bash
docker-compose up -d
```

Da questo momento il branding sopravvive a qualsiasi `docker-compose up` o aggiornamento dell'immagine.

---

## Aggiornare i file in futuro

Modifica i file in `custom/` in locale, ricaricali sul server e riavvia:

```bash
scp custom/logo.png root@SERVER:/home/node/mvp-ai/custom/
docker-compose restart mvp-open-webui   # sul server
```

---

## Troubleshooting

### Errore: "not a directory" al docker-compose up

Docker ha creato una **directory** al posto di un file (succede se il file non esisteva sull'host al momento del bind mount). Fix:

```bash
# Sul server — identifica e rimuovi le directory spurie
ls -la /home/node/mvp-ai/custom/
rm -rf /home/node/mvp-ai/custom/site.webmanifest   # se è una directory
docker-compose up -d
```

### Errore: container spento al primo avvio dello script

```bash
docker-compose up -d          # avvia il container
bash deploy-branding.sh       # poi esegui lo script
docker-compose up -d          # riavvia con i nuovi volumi
```

### Nome app mostra "Boxed AI (Open WebUI)"

La patch a `env.py` non è stata applicata o il bind mount non è attivo. Verifica:

```bash
docker exec mvp-open-webui grep "WEBUI_NAME" /app/backend/open_webui/env.py
# deve mostrare solo: WEBUI_NAME = os.environ.get("WEBUI_NAME", "Open WebUI")
# senza le due righe del suffisso
```

In alternativa: Admin Panel → General → WebUI Name → imposta `Boxed AI` (sovrascrive l'env var, salvato nel DB).
