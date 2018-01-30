# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV (<http://acsone.eu>)
# License GPL-3.0 or later (http://www.gnu.org/licenses/gpl.html).

import os
import subprocess
import click
from .tools import cmd_push, tempinput
from .checklog import do_checklog

NEW_LANGUAGE = '__new__'


def do_makepot(database, odoo_bin, installable_addons, odoo_config, git_push,
               git_user_name, git_user_email, languages, git_push_branch):
    if not languages:
        languages = [NEW_LANGUAGE]
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
    proc = subprocess.Popen(
        odoo_shell_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    script_dir = os.path.dirname(__file__)
    installlang_script_path = os.path.join(script_dir, 'installlang_script')
    with open(installlang_script_path) as f:
        install_language_cmd = f.read()
    for lang in languages:
        if lang == NEW_LANGUAGE:
            continue
        # TODO : check if the lang is already installed ?
        lang_kwargs = {
            'lang': lang,
        }
        install_lang_cmd = install_language_cmd % lang_kwargs
        proc.stdin.write(install_lang_cmd)

    script_path = os.path.join(script_dir, 'makepot_script')
    with open(script_path) as f:
        script_cmd = f.read()
    files_to_push = []
    for addon_name, (addon_dir, manifest) in installable_addons.items():
        if os.path.islink(addon_dir):
            click.echo("Module %s ignored : symlink" % addon_name)
            continue
        i18n_path = os.path.join(addon_dir, 'i18n')
        if not os.path.isdir(i18n_path):
            os.makedirs(i18n_path)
        for lang in languages:
            if lang == NEW_LANGUAGE:
                file_name = '%s.pot' % addon_name
            else:
                file_name = '%s.po' % lang
            pot_file_path = os.path.join(i18n_path, file_name)
            kwargs = {
                'module_name': addon_name,
                'pot_file_path': pot_file_path,
                'lang': lang,
            }
            module_cmd = script_cmd % kwargs
            proc.stdin.write(module_cmd)
            files_to_push.append(pot_file_path)
        break
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
    if git_push:  # Add condition
        cmd_push(files_to_push, "Update translation files",
                 git_user_name=git_user_name, git_user_email=git_user_email,
                 git_push_branch=git_push_branch)
