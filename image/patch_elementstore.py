"""
Patch: always clear image.value for dynamic images in cleanUpDynamicContent.

Without this fix, non-standard print_designer formats persist the last-previewed
document's image URL as a cached `image.value`. Every subsequent print then shows
that stale document's image instead of the current document's image.

Root cause (ElementStore.js cleanUpDynamicContent):
  The `image.value = ""` cleanup was gated on `is_standard`, so custom (non-standard)
  formats never cleared it on save.
"""
import sys

PATH = (
    "apps/print_designer/print_designer/public/js/"
    "print_designer/store/ElementStore.js"
)

OLD = (
    "\t\t\t\t\telement.image = { ...element.image };\n"
    "\t\t\t\t\tif (MainStore.is_standard) {"
)

NEW = (
    "\t\t\t\t\telement.image = { ...element.image };\n"
    "\t\t\t\t\telement.image.value = ''; // patch: always clear stale preview value\n"
    "\t\t\t\t\tif (MainStore.is_standard) {"
)

with open(PATH) as f:
    src = f.read()

if OLD not in src:
    sys.exit("PATCH FAILED: target string not found in " + PATH)

patched = src.replace(OLD, NEW, 1)

with open(PATH, "w") as f:
    f.write(patched)

print("ElementStore.js patched OK")
