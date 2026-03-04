# Deploy Branding Boxed AI — Procedura Operativa

File di riferimento: `custom/` (loghi, script, zip)
Documentazione concettuale: [customizzazione-interfaccia.md](customizzazione-interfaccia.md)

---

## Come funziona

Il branding viene applicato **automaticamente ad ogni avvio del container** tramite `custom/entrypoint.sh`:

1. Estrae `boxedai-branding.zip` in `/app/backend/open_webui/static/`
2. Patcha `env.py` per rimuovere il suffisso automatico "(Open WebUI)"
3. Avvia Open WebUI normalmente (`bash start.sh`)

Il `docker-compose.yaml` monta solo due file:

```yaml
volumes:
  - open-webui:/app/backend/data
  - ./custom/boxedai-branding.zip:/custom/boxedai-branding.zip:ro
  - ./custom/entrypoint.sh:/entrypoint.sh:ro
```

E usa `command: ["bash", "/entrypoint.sh"]` al posto dell'entrypoint di default.

---

## Prima installazione (una tantum)

### 1. Carica sul server

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
    command: ["bash", "/entrypoint.sh"]
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
```

---

## Troubleshooting

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

docker exec open-webui ls /app/backend/open_webui/static/logo.png
# deve esistere
```

### Errore all'avvio del container

Controlla i log per errori nell'entrypoint:

```bash
docker logs open-webui | head -30
```
