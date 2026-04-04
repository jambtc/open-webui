# Deploy Merge — riallineare fork e branch custom

Obiettivo: aggiornare il fork con la nuova `main` di `upstream` e riagganciare `openclaw-custom`.

## Prerequisiti

Verifica remoti e branch:

```bash
cd /var/www/open-webui
git branch --show-current
git remote -v
```

Atteso:
- `origin` -> tuo fork
- `upstream` -> repository ufficiale (`open-webui/open-webui`)

---

## 1) Salva il lavoro locale

Se hai modifiche non committate su `openclaw-custom`, mettile in sicurezza prima del sync.

Opzione consigliata (commit WIP):

```bash
cd /var/www/open-webui
git add -A
git commit -m "WIP: branding/custom"
```

Alternativa (stash):

```bash
git stash push -u -m "wip before upstream sync"
```

---

## 2) Aggiorna `main` dal repository ufficiale

```bash
cd /var/www/open-webui
git fetch upstream
git switch main
git merge --ff-only upstream/main
git push origin main
```

---

## 3) Riaggancia `openclaw-custom`

### Opzione A (consigliata): `rebase` su `upstream/main`

Mantiene una history pulita, ma riscrive i commit del branch.

```bash
cd /var/www/open-webui
git switch openclaw-custom
git rebase upstream/main
```

Se ci sono conflitti:

```bash
git add <file-risolto>
git rebase --continue
```

Quando il rebase è completato:

```bash
git push --force-with-lease origin openclaw-custom
```

## Note operative

- Se avevi usato stash, riapplica a fine sync:

```bash
git stash list
git stash pop
```
