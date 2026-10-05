"""
patch_safe_exec.py
──────────────────
Injects io, os, save_file, PIL.Image (as `Image`), and fitz into Frappe's
safe_exec globals so that Server Scripts can use image-processing code
without hitting the `ImportError: __import__ not found` sandbox restriction.

Run once inside the erpnext2 container before starting gunicorn:
    python3 /tmp/patch_safe_exec.py
"""

SAFE_EXEC_PATH = (
    "/home/frappe/frappe-bench/apps/frappe/frappe/utils/safe_exec.py"
)

MARKER = "# ── Custom module injections (patch_safe_exec.py) ──"

INJECTION = """\
\t# ── Custom module injections (patch_safe_exec.py) ──
\t# Expose stdlib + third-party modules needed by shipping-label Server Scripts.
\t# Standard `import` statements are forbidden in safe_exec; injecting the
\t# module objects directly is the supported workaround.
\timport io as _io_mod
\timport os as _os_mod
\tfrom frappe.utils.file_manager import save_file as _save_file_fn
\tout["io"] = _io_mod
\tout["os"] = _os_mod
\tout["splitext"] = _os_mod.path.splitext
\tout["BytesIO"] = _io_mod.BytesIO
\tout["save_file"] = _save_file_fn
\ttry:
\t\timport PIL.Image as _pil_img
\t\tout["Image"] = _pil_img
\t\tout["PIL_open"] = _pil_img.open
\t\tout["PIL_new"] = _pil_img.new
\t\tout["PIL_LANCZOS"] = _pil_img.LANCZOS
\texcept Exception:
\t\tpass
\ttry:
\t\timport fitz as _fitz_mod
\t\tout["fitz"] = _fitz_mod
\t\tout["fitz_open"] = _fitz_mod.open
\t\tout["fitz_Matrix"] = _fitz_mod.Matrix
\texcept Exception:
\t\tpass
\t# ── End custom injections ──
"""

# The line immediately before `return out` at the end of get_safe_globals()
# Try both known anchor variants (Frappe 15.x has single blank line; some builds have two)
ANCHOR = "\tout.update(get_python_builtins())\n\n\treturn out\n"
ANCHOR2 = "\tout.update(get_python_builtins())\n\n\n\treturn out\n"
REPLACEMENT = "\tout.update(get_python_builtins())\n\n" + INJECTION + "\n\treturn out\n"

with open(SAFE_EXEC_PATH, "r") as fh:
    src = fh.read()

if MARKER in src:
    print("safe_exec.py already patched — nothing to do.")
else:
    if ANCHOR in src:
        src = src.replace(ANCHOR, REPLACEMENT, 1)
    elif ANCHOR2 in src:
        src = src.replace(ANCHOR2, REPLACEMENT, 1)
    else:
        raise RuntimeError(
            f"Anchor string not found in {SAFE_EXEC_PATH}. "
            "Frappe may have been updated; review the patch manually."
        )
    with open(SAFE_EXEC_PATH, "w") as fh:
        fh.write(src)
    print(f"Patched {SAFE_EXEC_PATH} successfully.")
