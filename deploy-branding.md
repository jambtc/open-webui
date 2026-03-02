# Deploy Branding Boxed AI — Procedura Operativa

File di riferimento: `custom/` (loghi, script, zip)
<<<<<<< HEAD
Documentazione concettuale: [customizzazione-interfaccia.md](customizzazione-interfaccia.md)

---

## Come funziona

Il branding viene applicato **automaticamente ad ogni avvio del container** tramite `custom/entrypoint.sh`:

1. Estrae `boxedai-branding.zip` in `/app/build/static/`
2. Patcha `env.py` per rimuovere il suffisso automatico "(Open WebUI)"
3. Avvia Open WebUI normalmente (`bash start.sh`)

Nota tecnica: Open WebUI ricrea `/app/backend/open_webui/static/` da `/app/build/static/` a ogni avvio. Per questo i file vanno copiati in `/app/build/static/`.

Il `docker-compose.yaml` monta solo due file:

```yaml
volumes:
  - open-webui:/app/backend/data
  - ./custom/boxedai-branding.zip:/custom/boxedai-branding.zip:ro
  - ./custom/entrypoint.sh:/entrypoint.sh:ro
```

E usa `entrypoint: ["bash", "/entrypoint.sh"]`.
=======
Documentazione concettuale: [deploy-concept.md](deploy-concept.md)
>>>>>>> aab1f57c6 (WIP: branding/custom)

---

## Prima installazione (una tantum)

### 1. Carica sul server

<<<<<<< HEAD
Dal PC locale, dalla cartella `open-webui/`:

```bash
cd /var/www/documents/progetti/openclaw/open-webui
scp custom/boxedai-branding.zip custom/entrypoint.sh root@SERVER:/home/node/mvp-ai/custom/
```

### 2. Verifica il docker-compose.yaml sul server

La sezione `open-webui` deve avere:

```yaml
  open-webui:
    image: ghcr.io/open-webui/open-webui:${WEBUI_DOCKER_TAG-main}
    container_name: open-webui
    volumes:
      - open-webui:/app/backend/data
      - ./custom/boxedai-branding.zip:/custom/boxedai-branding.zip:ro
      - ./custom/entrypoint.sh:/entrypoint.sh:ro
    environment:
      - WEBUI_NAME=Boxed AI
      # ... altri env var
    entrypoint: ["bash", "/entrypoint.sh"]
```

### 3. Avvia

```bash
docker compose up -d
```

Il branding sopravvive a qualsiasi `docker compose up` o aggiornamento dell'immagine.

---

## Aggiornare i file di branding in futuro

Aggiorna il file locale, ricarica sul server e riavvia:

```bash
# Aggiorna lo zip (contiene loghi, icone, css, webmanifest)
cd /var/www/documents/progetti/openclaw/open-webui
scp custom/boxedai-branding.zip root@SERVER:/home/node/mvp-ai/custom/

# Sul server
docker compose restart open-webui
=======
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
>>>>>>> aab1f57c6 (WIP: branding/custom)
```

---

## Troubleshooting

<<<<<<< HEAD
### Nome app mostra "Boxed AI (Open WebUI)"

La patch a `env.py` non è stata applicata. Verifica che `entrypoint.sh` sia montato e che `command` sia configurato nel compose. Per diagnosticare:

```bash
docker exec open-webui grep -A2 'if WEBUI_NAME' /app/backend/open_webui/env.py
# Se le righe del suffisso sono ancora presenti, l'entrypoint non ha girato
```

In alternativa rapida: Admin Panel → General → WebUI Name → imposta `Boxed AI` (salvato nel DB, sovrascrive l'env var).

### File statici non aggiornati dopo il riavvio

Verifica che lo zip sia montato correttamente:

```bash
docker exec open-webui ls /custom/
# deve mostrare boxedai-branding.zip

docker exec open-webui ls /app/build/static/logo.png
# deve esistere

docker exec open-webui ls /app/backend/open_webui/static/logo.png
# deve esistere
```

### Errore all'avvio del container

Controlla i log per errori nell'entrypoint:

```bash
docker logs open-webui | head -30
```
=======
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
>>>>>>> aab1f57c6 (WIP: branding/custom)
