"""
Build-time patch: adds a "Total Outstanding" amber banner to the /invoices
customer portal list page by extending sales_invoice.get_list_context.
"""

import re

FILEPATH = (
    "/home/frappe/frappe-bench/apps/erpnext/erpnext/accounts/"
    "doctype/sales_invoice/sales_invoice.py"
)

OLD = '''\
def get_list_context(context=None):
\tfrom erpnext.controllers.website_list_for_contact import get_list_context

\tlist_context = get_list_context(context)
\tlist_context.update(
\t\t{
\t\t\t"show_sidebar": True,
\t\t\t"show_search": True,
\t\t\t"no_breadcrumbs": True,
\t\t\t"title": _("Invoices"),
\t\t}
\t)
\treturn list_context'''

NEW = '''\
def get_list_context(context=None):
\tfrom erpnext.controllers.website_list_for_contact import get_list_context, get_customers_suppliers

\tlist_context = get_list_context(context)

\t# Compute total outstanding across all invoices for the current customer
\ttry:
\t\tcustomers, _suppliers = get_customers_suppliers("Sales Invoice", frappe.session.user)
\t\tif customers:
\t\t\trows = frappe.db.sql(
\t\t\t\t"""
\t\t\t\tSELECT currency, SUM(outstanding_amount) AS total
\t\t\t\tFROM `tabSales Invoice`
\t\t\t\tWHERE customer IN %(customers)s
\t\t\t\t  AND outstanding_amount > 0
\t\t\t\t  AND docstatus = 1
\t\t\t\tGROUP BY currency
\t\t\t\t""",
\t\t\t\t{"customers": customers},
\t\t\t\tas_dict=True,
\t\t\t)
\t\t\tif rows:
\t\t\t\tfrom frappe.utils import fmt_money
\t\t\t\tparts = [
\t\t\t\t\tfmt_money(row.total, currency=row.currency) + "\u00a0" + row.currency
\t\t\t\t\tfor row in rows
\t\t\t\t]
\t\t\t\tlist_context.introduction = (
\t\t\t\t\t\'<div style="background:#fff8e1;border-left:4px solid #ffc107;\'\n\t\t\t\t\t\'border-radius:4px;padding:12px 20px;margin-bottom:20px;font-size:0.95em;">\'\n\t\t\t\t\t\'<strong>Total Outstanding:</strong>\u00a0\' + "\u00a0+\u00a0".join(parts) +
\t\t\t\t\t\'</div>\'
\t\t\t\t)
\texcept Exception:
\t\tpass

\tlist_context.update(
\t\t{
\t\t\t"show_sidebar": True,
\t\t\t"show_search": True,
\t\t\t"no_breadcrumbs": True,
\t\t\t"title": _("Invoices"),
\t\t}
\t)
\treturn list_context'''

with open(FILEPATH, "r") as f:
    content = f.read()

if OLD not in content:
    raise RuntimeError(
        "patch_sales_invoice_list: target function not found — "
        "the upstream source may have changed."
    )

content = content.replace(OLD, NEW, 1)

with open(FILEPATH, "w") as f:
    f.write(content)

print("patch_sales_invoice_list: OK")
