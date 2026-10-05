# Pinned by digest (Harbor: same base as the original morefine build, 2026-10-05).
FROM frappe/erpnext:v15.107.0@sha256:8d75a47992cd4c84f6ea8cf9e24e1e00ae6bca9775c82f636d31fb5f9181bd6d

USER frappe
WORKDIR /home/frappe/frappe-bench

# Install print_designer into the bench
RUN bench get-app print_designer https://github.com/frappe/print_designer --branch v1.6.7 --skip-assets
# Remove the hardcoded "Beta" badge from the header UI
RUN sed -i '/<span class="indicator-pill no-indicator-dot ellipsis gray">Beta<\/span>/d' \
    apps/print_designer/print_designer/public/js/print_designer/components/layout/AppHeader.vue

# Fix: always clear image.value for dynamic images when saving (cleanUpDynamicContent).
# Without this, non-standard formats persist the last-previewed doc's image URL as a
# stale cached value, causing every print to show that stale image instead of the
# current document's image.
COPY patch_elementstore.py /tmp/patch_elementstore.py
RUN python3 /tmp/patch_elementstore.py

# Fix: dynamic image macro checks element.image.parent but Print Designer stores
# the doctype under element.image.doctype (not element.image.parent). This causes
# the condition to always fail, falling through to frappe.db.get_value() with an
# empty parentField, which returns the first DB record's image for every document.
COPY patch_image_macro.py /tmp/patch_image_macro.py
RUN python3 /tmp/patch_image_macro.py

# Fix: print_format.html iterates pd_format.body pages with no CSS page break
# between them, so the PDF renderer (wkhtmltopdf/Chrome) decides the break point
# arbitrarily — cutting content mid-element. Inject a page-break-before:always div
# before every page after the first so each design page = one PDF page.
COPY patch_print_format_html.py /tmp/patch_print_format_html.py
RUN python3 /tmp/patch_print_format_html.py

# Inject io/os/PIL.Image/fitz/save_file into Frappe's safe_exec globals so that
# Server Scripts can perform image processing without hitting the sandbox's
# `ImportError: __import__ not found` restriction.
COPY patch_safe_exec.py /tmp/patch_safe_exec.py
COPY repatch.py /tmp/repatch.py
RUN /home/frappe/frappe-bench/env/bin/pip install PyMuPDF==1.27.2.3 --quiet
RUN python3 /tmp/repatch.py && python3 /tmp/patch_safe_exec.py

# Build assets (writes to apps/print_designer/print_designer/public/dist/): done in the Harbor step
# at the end, because sites/ is a VOLUME in the base image and the classic builder drops writes to it
# between steps (apps.txt from get-app, sites/assets/assets.json from the build).

# ── Custom order/invoice portal template ─────────────────────────────────────
# Adds "Payments Received" and "Outstanding Balance" sections to the
# /invoices/<name> customer portal page (order.html is shared by all portal
# transaction doctypes; the new block is guarded by {% if doc.doctype == 'Sales Invoice' %})
COPY order.html apps/erpnext/erpnext/templates/pages/order.html

# ── Invoice list: total outstanding banner + per-row outstanding amount ────────
# Patches sales_invoice.get_list_context to compute and inject a total
# outstanding banner as context.introduction on /invoices
COPY patch_sales_invoice_list.py /tmp/patch_sales_invoice_list.py
RUN python3 /tmp/patch_sales_invoice_list.py
# Adds an "Outstanding: …" sub-line under each invoice's grand total on the list
COPY transaction_row.html apps/erpnext/erpnext/templates/includes/transaction_row.html

# ── Remove "Powered by ERPNext" footer ────────────────────────────────────────
COPY footer_powered.html apps/erpnext/erpnext/templates/includes/footer/footer_powered.html

# ── Custom portal theme ───────────────────────────────────────────────────────
# Copy the theme CSS into frappe's public directory so the configurator's
# asset-copy step (cp -rL apps/frappe/frappe/public → sites/assets/frappe)
# publishes it at /assets/frappe/css/custom_theme.css
RUN mkdir -p apps/frappe/frappe/public/css
COPY custom_theme.css apps/frappe/frappe/public/css/custom_theme.css

# Script that writes the <link> tag into Website Settings head_include
# (run by the apply-theme service in docker-compose after the site exists)
COPY apply_website_theme.py /tmp/apply_website_theme.py

# ── Harbor: what the one-shot services (configurator, create-site, apply-theme) did ──
# Stage the complete built asset set once, at build time: the base image's bundles plus Print
# Designer's, and every app's public folder (custom theme included), dereferenced like the old
# configurator's `cp -rL`. The backend copies it into the shared assets volume when the build changes.
USER root
COPY startup/ /home/frappe/harbor/
RUN chmod 0755 /home/frappe/harbor/*.sh && chown -R frappe:frappe /home/frappe/harbor
USER frappe
RUN cd /home/frappe/frappe-bench \
 && printf 'frappe\nerpnext\nprint_designer' > sites/apps.txt \
 && bench build --app print_designer \
 && rm -rf /home/frappe/harbor/assets \
 && cp -rL assets /home/frappe/harbor/assets \
 && for app in frappe erpnext print_designer; do \
      rm -rf /home/frappe/harbor/assets/$app \
      && cp -rL apps/$app/$app/public /home/frappe/harbor/assets/$app; \
    done \
 && cp -rn sites/assets/css/. /home/frappe/harbor/assets/css/ \
 && cp -rn sites/assets/js/. /home/frappe/harbor/assets/js/ \
 && jq -s '.[0] * .[1]' assets/assets.json sites/assets/assets.json > /home/frappe/harbor/assets/assets.json \
 && jq -s '.[0] * .[1]' assets/assets-rtl.json sites/assets/assets-rtl.json > /home/frappe/harbor/assets/assets-rtl.json \
 && grep -q print_designer.bundle.js /home/frappe/harbor/assets/assets.json \
 && date -u +%Y%m%dT%H%M%SZ > /home/frappe/harbor/build-id
