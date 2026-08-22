# Deploying camplux to a shared host

This is for running camplux continuously on a machine other than your own
laptop (e.g. `lamp-compute-01`), reachable remotely, instead of the
`python run.py` / Beacon flow in the main README (which is built for
interactive local use on your own machine).

## What actually runs here

- **Vault** (archive builder) and **Quarry** (on-demand export/query tool)
  run always-on (`docker compose up -d`, no profile needed).
- **Cleaner**, **Weaver**, **Stats** are batch-processing steps you run
  occasionally, not services that need to sit online — start one when you
  need it, stop it after:
  ```bash
  docker compose --profile batch up -d cleaner
  # ... use it ...
  docker compose --profile batch stop cleaner
  ```
- **Prism** isn't deployed here at all -- it needs a local Ollama LLM
  server, which needs RAM most small shared hosts won't have free. Run it
  locally on your own machine when you need LLM analysis.

## Why Vault and Quarry get separate ports, not one path-routed URL

Both apps' frontend JS calls absolute paths (`fetch('/status')`,
`fetch('/scrape?...')`). Mounting them under e.g. `/vault/*` and
`/quarry/*` behind one reverse proxy would strip that prefix before the
request reaches the backend, but the *page's own JS* would still call
plain `/status` at the site root and miss the backend -- silently broken
AJAX calls, not an error you'd see immediately. Separate ports (see
`Caddyfile`) sidestep this entirely: each app is still served from its own
root exactly as its own code expects, no changes needed to either app.

## One-time setup

```bash
cp .env.example .env
docker run --rm caddy:2-alpine caddy hash-password --plaintext 'choose-a-real-password'
# paste the bcrypt output into .env as CAMPLUX_AUTH_HASH
docker compose up -d --build
```

## Exposing it remotely

This deployment doesn't handle its own public exposure -- that's the host
machine's job (e.g. Tailscale Funnel on `lamp-compute-01`, see that
machine's own `ARCHITECTURE.md`). It expects something in front to forward
two ports to Caddy's `5081` (Vault) and `5082` (Quarry).

## Archive persistence

`vault/data/*.db` lives in the `vault_data` named Docker volume, not a
bind-mounted host directory -- it survives container rebuilds/restarts but
back it up like any other volume you care about (`docker run --rm -v
camplux_vault_data:/data -v $PWD:/backup alpine tar czf
/backup/vault_data_$(date +%F).tar.gz -C /data .`).

## Keeping the archive growing automatically

See `nightly-archive.sh` and the systemd timer it's meant to run under --
hits Vault's `/archive?source=X&mode=update` for every configured source,
which does an incremental scrape (only what's new since last time) and
persists straight into the archive. Not part of this compose file itself
since scheduling is a host concern, not a container concern.
