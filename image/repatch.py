import re

path = '/home/frappe/frappe-bench/apps/frappe/frappe/utils/safe_exec.py'
with open(path) as f:
    src = f.read()

marker = '# \u2500\u2500 Custom module injections (patch_safe_exec.py) \u2500\u2500'
if marker in src:
    src = re.sub(
        r'\t# \u2500\u2500 Custom module injections.*?# \u2500\u2500 End custom injections \u2500\u2500\n',
        '',
        src,
        flags=re.DOTALL
    )
    with open(path, 'w') as f:
        f.write(src)
    print('Old injection removed.')
else:
    print('Marker not found — nothing to remove.')
