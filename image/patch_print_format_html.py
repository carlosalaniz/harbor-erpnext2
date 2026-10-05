"""
Patch: inject CSS page-break-before between consecutive pages in Print Designer's
print_format.html Jinja template.

Root cause (print_format.html):
  The template loops over pd_format.body and calls render() for each "page", but
  there is NO page-break CSS between iterations. As a result, when a Print Designer
  format has 2+ design pages, the PDF renderer (wkhtmltopdf) has no instruction to
  start a new physical PDF page between them and breaks at an arbitrary position.

Fix:
  Before rendering every page except the first one, emit a zero-height div with
  page-break-before: always. This is the standard CSS mechanism for forcing a new
  PDF page and works with both wkhtmltopdf and Chrome (Puppeteer).
"""
import sys

PATH = (
    "apps/print_designer/print_designer/print_designer/"
    "page/print_designer/jinja/print_format.html"
)

OLD = (
    "    {%- for body in pd_format.body -%}\n"
    "        {{ render(body.childrens, send_to_jinja) }}\n"
    "    {%- endfor -%}"
)

NEW = (
    "    {%- for body in pd_format.body -%}\n"
    "        {%- if loop.index > 1 %}<div style=\"page-break-before: always;\"></div>{% endif -%}\n"
    "        {{ render(body.childrens, send_to_jinja) }}\n"
    "    {%- endfor -%}"
)

with open(PATH) as f:
    src = f.read()

if NEW in src:
    print("print_format.html already patched — skipping")
    sys.exit(0)

if OLD not in src:
    print("Current for-loop block in print_format.html:")
    import re
    m = re.search(r'\{%-? for body in pd_format\.body.*?\{%-? endfor -%\}', src, re.DOTALL)
    if m:
        print(repr(m.group()))
    sys.exit("PATCH FAILED: target string not found in " + PATH)

patched = src.replace(OLD, NEW, 1)

with open(PATH, "w") as f:
    f.write(patched)

print("print_format.html patched OK")
