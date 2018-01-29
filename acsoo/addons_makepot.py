# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import os
import subprocess
import tempfile
from contextlib import contextmanager
from .manifest import get_installable_addons
from .checklog import do_checklog


@contextmanager
def tempinput(data):
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data)
    temp.close()
    try:
        yield temp.name
    finally:
        os.unlink(temp.name)


def do_makepot(database, odoo_bin, addons_dirs, odoo_config):
    odoo_shell_cmd = [
        odoo_bin,
        'shell',
        '-d', database,
        '--log-level=error',
        '--no-xmlrpc',
    ]
    if odoo_config:
        odoo_shell_cmd.extend([
            '-c', odoo_config
        ])
    script_dir = os.path.dirname(__file__)
    script_path = os.path.join(script_dir, 'makepot_script')
    proc = subprocess.Popen(
        odoo_shell_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    with open(script_path) as f:
        script_cmd = f.read()
    installable_addons = get_installable_addons(addons_dirs).items()
    for addon_name, (addon_dir, manifest) in installable_addons:
        kwargs = {
            'module_name': addon_name,
            'module_path': os.path.join(addon_dir, addon_name),
        }
        module_cmd = script_cmd % kwargs
        proc.stdin.write(module_cmd)
    proc.stdin.close()
    out = proc.stdout.read()
    if out:
        with tempinput(out) as tempfilename:
            do_checklog(tempfilename, [], None)
    proc.terminate()
