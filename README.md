# ERPNext (custom build) for Harbor

A [Harbor](https://github.com/carlosalaniz/harbor) app: ERPNext 15.107 with Print Designer 1.6.7,
a custom portal theme, and a handful of print/invoice fixes, built from this repository on the
Harbor machine.

```
harbor/            the Harbor package (manifest.yaml + compose.yaml)
image/             the Docker build context
  Dockerfile       frappe/erpnext:v15.107.0 (pinned by digest) + Print Designer + patches
  patch_*.py …     source fixes applied at build time
  startup/         backend-start.sh (config, site creation, assets, theme) and the after-start hook
```

## Install

In Harbor: **App Store → Your own app → git repository** with this repository's HTTPS URL and branch `main`
(or `harbor sources add https://github.com/carlosalaniz/harbor-erpnext2 --branch main`), then
install **ERPNext**. The first start builds the image and creates the site `erp2.local`
(a few minutes); Harbor shows the Administrator password once.

## How it runs

| Service | Role |
|---|---|
| `frontend` | nginx: serves assets, proxies to the backend and socket.io; answers as `erp2.local` on any address |
| `erpnext2` | gunicorn; on every start writes `common_site_config.json`, creates the site if it is missing, refreshes the assets volume when the image changed, applies the theme |
| `websocket`, `scheduler`, `worker-{default,short,long}` | socket.io, cron, background queues |
| `erpnext2-db`, `erpnext2-redis-cache`, `erpnext2-redis-queue` | MariaDB 11 (utf8mb4), Redis 7 |

Service names match the original Compose stack, so a site copied from it (volumes `sites`,
`assets`, `logs`, `mariadb`) starts as is. Nothing secret lives in this repository: Harbor
generates the database root password and the Administrator password.
