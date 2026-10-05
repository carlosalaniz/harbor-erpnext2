#!/bin/bash
# Harbor afterStart hook (runs after every start, Restart, publish, unpublish): links ERPNext sends
# out (emails, portal links) use Harbor's main address for this app.
set -euo pipefail
cd /home/frappe/frappe-bench
SITE="${SITE_NAME:?SITE_NAME is not set}"
if [ -n "${HARBOR_URL:-}" ]; then
  bench --site "$SITE" set-config host_name "${HARBOR_URL%/}" >/dev/null
  echo "host_name set to ${HARBOR_URL%/}"
fi
