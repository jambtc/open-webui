# Personalizzazione dell'interfaccia Open WebUI

Open WebUI è un'applicazione **SvelteKit** con **TailwindCSS**. Esistono due livelli di personalizzazione: **senza rebuild** (immediata) e **con rebuild** (strutturale).

---

## 1. CSS Personalizzato (senza rebuild)

Il file caricato dall'app è `/static/custom.css` (link in `src/app.html`). In deploy Docker viene generato da `/app/build/static/custom.css`.


```css
/* ============================= */
/* 🌑 EXAMPLE DARK GREEN PREMIUM THEME  */
/* ============================= */

/* ---- Variabili principali ---- */
:root {
    --bg-main: #0b1210;
    --bg-secondary: #101c18;
    --bg-sidebar: #0f1714;
    --green-primary: #00c896;
    --green-soft: #00a37a;
    --green-glow: rgba(0, 200, 150, 0.35);
    --border-soft: #1b2a25;
    --text-main: #e6f4f1;
    --text-muted: #9fb3ad;
}
```

> ✅ Le modifiche sono **immediate**, senza riavvio o rebuild.

---

## 2. Logo e Icone (senza rebuild)

In Docker i file personalizzati vanno preparati in `/app/build/static/`.
Open WebUI, all'avvio, ricrea `/app/backend/open_webui/static/` copiando da `/app/build/static/`.

### Branding attuale: Boxed AI

I file originali sono archiviati in `progetti/openclaw/open-webui/images/` (copia di documentazione).

I file sono stati aggiornati con il branding da `/var/www/boxedai-web-ui`:

| File | Sorgente boxedai-web-ui | Dimensioni |
| ---- | ---------------------- | ---------- |
| `logo.png` | `assets/icons/app_icon.png` | 327×298px |
| `favicon.png` | `web/icons/Icon-192.png` | 192×192px |
| `favicon-96x96.png` | `web/icons/Icon-192.png` | 192×192px |
| `favicon-dark.png` | `web/icons/Icon-192.png` | 192×192px |
| `favicon.ico` | `windows/runner/resources/app_icon.ico` | multi-res ICO |
| `apple-touch-icon.png` | `web/icons/Icon-192.png` | 192×192px |
| `splash.png` | `assets/icons/app_icon.png` | 327×298px |
| `splash-dark.png` | `assets/icons/app_icon.png` | 327×298px |
| `web-app-manifest-192x192.png` | `web/icons/Icon-192.png` | 192×192px |
| `web-app-manifest-512x512.png` | `web/icons/Icon-512.png` | 512×512px |
| `enac-logo-bianco.png` | `assets/examples_app_assets/enac-logo-bianco.png` | logo ENAC bianco |
| `enac-logo-blu.png` | `assets/examples_app_assets/enac-logo-blu.png` | logo ENAC blu |

> `favicon.svg` non è stato sostituito (nessun SVG disponibile in boxedai — viene usato quello originale di Open WebUI).

### Deploy su server Docker

Il container si chiama `open-webui`. Il path interno servito è:

```text
/app/backend/open_webui/static/
```

**Non è necessario `npm run build`** — il backend Python serve i file statici direttamente senza compilazione.

> I file copiati direttamente in `/app/backend/open_webui/static` vengono sovrascritti al boot. La soluzione robusta è aggiornare `/app/build/static` prima di avviare l'app (es. via `entrypoint.sh` + zip).
> `WEBUI_NAME=Boxed AI` nell'environment aggiunge automaticamente il suffisso `(Open WebUI)` — va rimosso patchando `env.py`.

I file di branding, lo script e la procedura operativa completa sono in:

- **File**: `custom/` (loghi, zip, script)
- **Procedura**: [deploy-branding.md](deploy-branding.md)

### Uso dei loghi ENAC nel CSS

I file `enac-logo-bianco.png` e `enac-logo-blu.png` sono disponibili in `/static/` e possono essere usati nel `custom.css`:

```css
/* Sostituisce il logo nella sidebar con il logo ENAC blu */
img[src*="logo.png"] {
    content: url('/static/enac-logo-blu.png');
}
```

---

## 3. Nome Applicazione (senza rebuild)

**Via interfaccia** — Admin Panel → General → WebUI Name (consigliato, non richiede rebuild).

Il nome attuale in codice è `Open WebUI`. Per cambiarlo strutturalmente:

- **Frontend**: `/var/www/open-webui/src/lib/constants.ts` riga 4 → `APP_NAME = 'Boxed AI'`
- **Backend**: variabile d'ambiente `WEBUI_NAME=Boxed AI` (se diverso da "Open WebUI", aggiunge il suffisso automaticamente)
- **Web Manifest**: `/var/www/open-webui/backend/open_webui/static/site.webmanifest` → aggiornato a `"name": "Boxed AI"`

> Il file `site.webmanifest` è già stato aggiornato con `"name": "Boxed AI"`.

---

## 4. Temi CSS

La cartella `/var/www/open-webui/static/themes/` contiene temi di esempio (`rosepine.css`, `rosepine-dawn.css`).
È possibile creare un tema personalizzato seguendo lo stesso pattern: classi CSS applicate quando il tema è attivo.

---

## 5. Titolo della Pagina HTML

**Via file** — modificare `/var/www/open-webui/src/app.html` riga 106:
```html
<title>Open WebUI</title>
```

> Richiede rebuild (`npm run build`)

**Via interfaccia** — Admin Panel → General → WebUI Name (non richiede rebuild).

---

## 6. Modifiche Strutturali (richiede rebuild)

Per modificare layout, componenti o logica dell'interfaccia, editare i file `.svelte` in `src/lib/components/` e poi:

```bash
cd /var/www/open-webui
npm run build
```

Componenti principali:

| File | Descrizione |
|------|-------------|
| `src/lib/components/layout/Sidebar.svelte` | Sidebar laterale |
| `src/lib/components/layout/Navbar.svelte` | Barra superiore |
| `src/app.html` | HTML base con splash screen e favicon |
| `src/app.css` | CSS globale (font, scrollbar, animazioni) |

---

## Riepilogo

| Modifica | Rebuild necessario? |
|----------|-------------------|
| CSS custom (`custom.css`) | ❌ No |
| Sostituzione logo/icone | ❌ No |
| Nome app via Admin Panel | ❌ No |
| Web Manifest (`site.webmanifest`) | ❌ No |
| Titolo via `app.html` | ✅ Sì |
| Nome app via `constants.ts` | ✅ Sì |
| Componenti Svelte | ✅ Sì |
