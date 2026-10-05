#!/bin/bash
# Harbor start for the ERPNext backend. Replaces the old Compose stack's one-shot services
# (configurator, create-site, apply-theme) and its asset rebuild; idempotent, runs on every
# start, then becomes gunicorn. Env: SITE_NAME, DB_ROOT_PASSWORD (Harbor secret), ADMIN_PASSWORD
# (Harbor-provisioned, used only when the site is created).
set -euo pipefail
cd /home/frappe/frappe-bench
SITE="${SITE_NAME:?SITE_NAME is not set}"
log() { echo "[harbor] $*"; }

# Same runtime patches as the original backend command.
python3 /tmp/repatch.py
python3 /tmp/patch_safe_exec.py

# 1. Assets: the image carries the complete built set; copy it into the shared volume
#    (mounted at /home/frappe/frappe-bench/assets) whenever the image build changed.
ASSETS=/home/frappe/frappe-bench/assets
if [ ! -f "$ASSETS/assets.json" ] || ! cmp -s /home/frappe/harbor/build-id "$ASSETS/.harbor-build-id"; then
  log "copying assets from image build $(cat /home/frappe/harbor/build-id)"
  find "$ASSETS" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a /home/frappe/harbor/assets/. "$ASSETS/"
  cp /home/frappe/harbor/build-id "$ASSETS/.harbor-build-id"
fi

# 2. common_site_config.json (was the configurator): the Compose service names are the addresses.
ls -1 apps > sites/apps.txt
python3 - <<'PY'
import json, os
p = 'sites/common_site_config.json'
try:
    c = json.load(open(p))
except (FileNotFoundError, ValueError):
    c = {}
c.update({
    'db_host': 'erpnext2-db', 'db_port': 3306,
    'redis_cache': 'redis://erpnext2-redis-cache:6379',
    'redis_queue': 'redis://erpnext2-redis-queue:6379',
    'redis_socketio': 'redis://erpnext2-redis-queue:6379',
    'socketio_port': 9000, 'allow_cors': '*', 'socketio_cors_origin': '*',
    'server_script_enabled': 1, 'chromium_binary_path': '/usr/bin/chromium-headless-shell',
})
tmp = p + '.tmp'
json.dump(c, open(tmp, 'w'), indent=1, sort_keys=True)
os.replace(tmp, p)
PY

wait-for-it -t 120 erpnext2-db:3306
wait-for-it -t 60 erpnext2-redis-cache:6379
wait-for-it -t 60 erpnext2-redis-queue:6379

# 3. The site: created only when missing. A site copied from another machine is kept as is.
if [ ! -f "sites/$SITE/site_config.json" ]; then
  log "creating site $SITE (first start; a few minutes)"
  bench new-site "$SITE" --mariadb-user-host-login-scope='%' \
    --db-root-password "$DB_ROOT_PASSWORD" --admin-password "$ADMIN_PASSWORD" \
    --install-app erpnext --install-app print_designer --set-default
  bench --site "$SITE" enable-scheduler
  # 4. Theme (was apply-theme): only on a new site. An existing site keeps whatever theme its
  #    Website Settings chose (the original site switched back to Standard).
  log "applying the website theme"
  (cd sites && ../env/bin/python - <<'PY'
import os, runpy, frappe
run = runpy.run_path('/tmp/apply_website_theme.py')['run']
frappe.init(site=os.environ['SITE_NAME'], sites_path='.')
frappe.connect()
try:
    run()
finally:
    frappe.destroy()
PY
  ) || log "theme step failed; apply it from Website Settings"
fi

log "starting gunicorn"
exec /home/frappe/frappe-bench/env/bin/gunicorn \
  --chdir=/home/frappe/frappe-bench/sites \
  --bind=0.0.0.0:8000 --threads=4 --workers=2 --worker-class=gthread \
  --worker-tmp-dir=/dev/shm --timeout=120 --preload \
  frappe.app:application
