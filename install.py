#!/usr/bin/env python3

import os
import yaml
from argparse import ArgumentParser

from misc import get_daybook_config, DAYBOOK_CFG


def get_args():
    parser = ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--basedir", required=True)
    args = parser.parse_args()
    rv = (args.name, args.basedir)
    print("returning {}".format(rv))
    return rv


def add_project_to_cfg(existing_cfg, name, basedir, default_template=None):
    if 'daybooks' not in existing_cfg:
        existing_cfg['daybooks'] = {}
    cfg = {'basedir' : basedir}
    if default_template:
        cfg['default_template'] = default_template

    existing_cfg['daybooks'][name] = cfg
    with open(DAYBOOK_CFG, 'w') as fp:
        yaml.safe_dump(existing_cfg, fp)


def install():
    name, basedir = get_args()
    existing_cfg = get_daybook_config()
    add_project_to_cfg(existing_cfg, name, basedir)


if __name__ == "__main__":
    install()
