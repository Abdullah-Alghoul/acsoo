# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import os
import subprocess
import click
from .tools import cmd_push, cmd_check_current_branch, tempinput
from .checklog import do_checklog


def do_makepot(database, odoo_bin, installable_addons, odoo_config, push,
               branches):
    if push and branches:
        if not cmd_check_current_branch(branches):
            click.echo('acsoo addons makepot : Current branch ignored')
            return
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
    pot_files_path = []
    for addon_name, (addon_dir, manifest) in installable_addons.items():
        module_path = os.path.join(addon_dir, addon_name)
        i18n_path = os.path.join(module_path, 'i18n')
        if not os.path.isdir(i18n_path):
            os.makedirs(i18n_path)
        file_name = addon_name + '.pot'
        pot_file_path = os.path.join(i18n_path, file_name)
        kwargs = {
            'module_name': addon_name,
            'pot_file_path': pot_file_path,
        }
        module_cmd = script_cmd % kwargs
        proc.stdin.write(module_cmd)
        pot_files_path.append(pot_file_path)
    proc.stdin.close()
    out = proc.stdout.read()
    click.echo(out)
    if out:
        with tempinput(out) as tempfilename:
            try:
                do_checklog(tempfilename, [], None)
            except click.ClickException as e:
                if e.message == "No Odoo log record found in input.":
                    pass
                else:
                    raise e
    if push:  # Add condition
        cmd_push(pot_files_path, "Update POT files")
