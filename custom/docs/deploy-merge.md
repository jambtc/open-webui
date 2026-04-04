# Deploy Merge — aggiornare Open WebUI senza rompere il branch custom

Obiettivo: aggiornare il fork rispetto a `upstream/main` senza reiniettare automaticamente fix locali, esperimenti auth o override di sviluppo dentro `openclaw-custom`.

## Problema del workflow precedente

Il vecchio approccio basato su:
- update di `main`
- `rebase openclaw-custom` su `upstream/main`
- `push --force-with-lease`

nel nostro caso si e' rivelato troppo fragile.

Perche':
- riproduce sopra il nuovo upstream anche commit temporanei o locali
- puo' trascinarsi dietro fix non destinati alla VPS
- rende difficile separare prodotto, branding e override locali
- puo' costringere a molte ore di recovery dopo il merge

## Regola nuova

Non aggiornare piu' `openclaw-custom` con `rebase` diretto su `upstream/main` come procedura standard.

La procedura corretta e':
1. allineare `main` del fork a `upstream/main`
2. creare un branch di upgrade dedicato
3. riportare sul branch di upgrade solo le personalizzazioni volute
4. aprire una PR verso `openclaw-custom`
5. testare prima in locale e poi sulla VPS

## Ruoli dei branch

### `main`
- deve restare il piu' possibile allineato a `upstream/main`
- non va usato come branch di customizzazione prodotto

### `openclaw-custom`
- e' il branch stabile del fork con le personalizzazioni BoxedAI approvate
- e' il branch di riferimento per il deploy applicativo del fork

### `upgrade/openwebui-vX.Y.Z`
- branch temporaneo per ogni upgrade upstream
- si crea da `main` aggiornato
- contiene solo il delta necessario a riallineare `openclaw-custom` alla nuova versione

### branch locali / override locali
- servono per prove, recovery o sviluppo macchina-locale
- non devono finire automaticamente nel branch prodotto

## Cosa NON va nel branch prodotto

Esempi tipici da tenere fuori da `openclaw-custom` salvo decisione esplicita:
- override compose locali, ad esempio `docker-compose.localhost-develop.yml`
- mapping `kc-boxedai.local`
- fix temporanei per Keycloak locale
- workaround per `localhost` o `host.docker.internal`
- prove auth/OIDC non approvate per la VPS
- documentazione puramente locale o di recovery temporanea

## Procedura corretta di upgrade

### 1. Salva eventuale lavoro locale

Se hai modifiche non committate:

```bash
cd /var/www/open-webui
git status --short
```

Se necessario:

```bash
git add -A
git commit -m "WIP: local work before upgrade"
```

oppure:

```bash
git stash push -u -m "wip before upgrade"
```

### 2. Aggiorna `main` dal repository ufficiale

```bash
cd /var/www/open-webui
git fetch upstream
git switch main
git merge --ff-only upstream/main
git push origin main
```

### 3. Crea un branch di upgrade dedicato

Esempio per `v0.8.12`:

```bash
cd /var/www/open-webui
git switch main
git switch -c upgrade/openwebui-v0.8.12
```

### 4. Porta dentro solo le personalizzazioni volute

Non fare un merge cieco dell'intero vecchio branch.

Strategie corrette:
- cherry-pick selettivo dei commit davvero utili
- ripresa manuale dei file custom necessari
- confronto mirato con `openclaw-custom`

Comando utile:

```bash
git diff --stat main..openclaw-custom
```

Oppure, per file specifici:

```bash
git diff main..openclaw-custom -- src/ custom/ docker-compose.yaml
```

### 5. Test locale completo

Prima della PR, verificare almeno:
- login
- logout
- chat
- streaming
- branding essenziale
- assenza di regressioni auth

### 6. Apri PR verso `openclaw-custom`

Base:
- `openclaw-custom`

Head:
- `upgrade/openwebui-v0.8.12`

### 7. Dopo approvazione, merge verso `openclaw-custom`

Solo dopo i test e la verifica che il delta non includa override locali.

## Recovery se qualcosa va storto

Se l'upgrade rompe il branch custom:
- non correggere subito dentro `openclaw-custom`
- crea un branch di restore dal commit VPS funzionante
- ripristina il servizio
- solo dopo ricostruisci il delta giusto

## Comandi utili

### Vedere il delta tra upstream aggiornato e branch custom

```bash
cd /var/www/open-webui
git diff --stat main..openclaw-custom
```

### Vedere i commit custom sopra `main`

```bash
cd /var/www/open-webui
git log --oneline main..openclaw-custom
```

### Creare branch di upgrade

```bash
cd /var/www/open-webui
git switch main
git switch -c upgrade/openwebui-v0.8.12
```

## Regola finale

Per questo repository, la disciplina giusta e':
- `main` aggiornato da upstream
- `openclaw-custom` stabile
- `upgrade/*` per gli aggiornamenti
- override locali fuori dal branch prodotto

Questo riduce drasticamente il rischio di dover rifare recovery lunghe dopo un upgrade upstream.
