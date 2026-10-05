"""
Patch: fix dynamic image rendering in Print Designer's image.html Jinja macro.

Root cause (image.html):
  The macro checks `element.image.parent == doc.doctype` to decide whether to pull
  the image URL from the current document or from a related document via
  frappe.db.get_value(). However, when the image element is configured via the
  Print Designer UI, the JSON stored in print_designer_print_format uses
  `element.image.doctype` (not `element.image.parent`). Since `parent` is absent,
  the condition always evaluates False, causing the macro to call:

      frappe.db.get_value(doctype, doc[parentField], fieldname)

  where parentField == "" → doc[''] == None → get_value returns the first DB record
  regardless of the current document, so every print shows the same stale image.

Fix:
  Also accept `element.image.doctype == doc.doctype` (with no parentField) as the
  condition for pulling the value directly from the current doc.
"""
import sys

PATH = (
    "apps/print_designer/print_designer/print_designer/"
    "page/print_designer/jinja/macros/image.html"
)

OLD = (
    "    {%- if element.image.parent == doc.doctype -%}\n"
    "    {%- set value = doc.get(element.image.fieldname) -%}\n"
    "    {%- else -%}\n"
    "    {%- set value = frappe.db.get_value(element.image.doctype, doc[element.image.parentField], element.image.fieldname) -%}\n"
    "    {%- endif -%}"
)

NEW = (
    "    {%- if element.image.parent == doc.doctype or (element.image.doctype == doc.doctype and not element.image.parentField) -%}\n"
    "    {%- set value = doc.get(element.image.fieldname) -%}\n"
    "    {%- else -%}\n"
    "    {%- set value = frappe.db.get_value(element.image.doctype, doc[element.image.parentField], element.image.fieldname) -%}\n"
    "    {%- endif -%}"
)

with open(PATH) as f:
    src = f.read()

if NEW in src:
    print("image.html already patched — skipping")
    sys.exit(0)

if OLD not in src:
    print("Current image.html content:")
    print(repr(src))
    sys.exit("PATCH FAILED: target string not found in " + PATH)

patched = src.replace(OLD, NEW, 1)

with open(PATH, "w") as f:
    f.write(patched)

print("image.html patched OK")
