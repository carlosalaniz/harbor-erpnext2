import frappe
import os
import sys

def run():
    theme_name = "Pharma Blue Portal"
    css_path = "/home/frappe/frappe-bench/apps/frappe/frappe/public/css/custom_theme.css"
    
    if not os.path.exists(css_path):
        print(f"CSS file not found at {css_path}")
        return

    with open(css_path, "r") as f:
        css_content = f.read()
    
    if not frappe.db.exists("Website Theme", theme_name):
        doc = frappe.get_doc({
            "doctype": "Website Theme",
            "theme": theme_name,
            "custom": 1
        })
        doc.insert(ignore_permissions=True)
        print(f"Created new theme {theme_name}")
    else:
        doc = frappe.get_doc("Website Theme", theme_name)
        print(f"Updating existing theme {theme_name}")
    
    doc.custom_overrides = css_content
    doc.save(ignore_permissions=True)
    
    ws = frappe.get_doc("Website Settings", "Website Settings")
    ws.website_theme = theme_name
    ws.save(ignore_permissions=True)
    
    frappe.db.commit()
    print(f"Successfully applied {theme_name}")

if __name__ == "__main__":
    site = os.environ.get("FRAPPE_SITE_NAME_HEADER", "erp2.local")
    # Ensure we are in the bench directory
    os.chdir("/home/frappe/frappe-bench")
    sys.path.insert(0, "apps/frappe")
    
    frappe.init(site=site)
    frappe.connect()
    try:
        run()
    finally:
        frappe.destroy()
