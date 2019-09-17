import re
import sys
import yaml
from clint.textui import puts as _puts, indent as _indent, colored as _colored
import os
import tempfile
import subprocess
from inspect import getmembers as _getmembers
from inspect import isfunction as _isfunction

from daybook import Daybook, encryption

DAYBOOK__CFG = os.path.join(os.getenv("HOME"), ".daybook.yml")
EDITOR = os.environ.get('EDITOR', 'vim')
_CFG = None


def get_commands() -> list:
    this_module = sys.modules[__name__]
    functions_list = [o[0] for o in _getmembers(this_module) if _isfunction(o[1]) and not o[0].startswith('_')]
    return [getattr(this_module, f) for f in functions_list if f != 'get_commands']


def _get_daybook_cfg():
    global _CFG
    if not _CFG:
        _CFG = _get_daybook_config()
    return _CFG


def _get_basedir_for_diary(d):
    if not d in _get_daybook_config()['daybooks']:
        print("You must install your diary first")
        sys.exit(1)
    else:
        return _get_daybook_config()['daybooks'][d]['basedir']


def _get_daybook_config():
    if os.path.exists(DAYBOOK__CFG):
        with open(DAYBOOK__CFG) as fp:
            return yaml.safe_load(fp)
    else:
        return {'daybooks': {}}


def _add_project_to_cfg(existing_cfg, name, basedir, default_template_filename=None):
    if 'daybooks' not in existing_cfg:
        existing_cfg['daybooks'] = {}
    cfg = {'basedir': basedir}
    if default_template_filename:
        cfg['default_template'] = default_template_filename

    existing_cfg['daybooks'][name] = cfg
    with open(DAYBOOK__CFG, 'w') as fp:
        yaml.safe_dump(existing_cfg, fp)


def install(diary_name: str, base_dir: str, default_template_filename: str = None):
    _add_project_to_cfg(_get_daybook_config(), diary_name, base_dir,
                        default_template_filename=default_template_filename)


def list_daybooks():
    for db in _get_daybook_config()['daybooks']:
        print(db)


def _editor_create_new_entry() -> str:
    initial_message = b""
    with tempfile.NamedTemporaryFile(suffix=".tmp") as tf:
        tf.write(initial_message)
        tf.flush()
        subprocess.call([EDITOR, tf.name])

        # do the parsing with `tf` using regular File operations.
        # for instance:
        tf.seek(0)
        edited_message = tf.read()
        return edited_message.decode("utf-8")


def _get_entry_title(entry: str):
    """
    Get the title from an entry.  The title is the first non-whitespace line.

    :param entry: the entry as a newline-delimited string
    :return: the first non-whitespace line of an entry and return it as the title
    """
    lines = entry.split("\n")
    for l in lines:
        if re.match('^(\s+)?$', l):
            continue
        else:
            return l


def create_entry(diary_name: str, is_encrypted=False) -> None:
    book = Daybook(diary_name, _get_basedir_for_diary(diary_name))
    entry = _editor_create_new_entry()
    title = _get_entry_title(entry)
    if is_encrypted:
        entry = encryption.encrypt(entry)
    book.commit_entry(entry, title=title, is_encrypted=is_encrypted)


def list_entries(diary_name: str, max_entries=None, with_tags=None, with_text=None, before_date=None, after_date=None):
    book = Daybook(diary_name, _get_basedir_for_diary(diary_name))
    entries = book.list_entries(
        max_entries=max_entries,
        with_tags=with_tags,
        with_text=with_text,
        after_date=after_date,
        before_date=before_date
    )
    for f, e in entries:
        _puts(_colored.blue("----- {f} -----".format(f=f)))
        for line in e:
            with _indent(4):
                _puts(line)


def list_tags(diary_name: str) -> None:
    book = Daybook(diary_name, _get_basedir_for_diary(diary_name))
    print(book.list_tags())


def list_commands() -> None:
    print("""
    
    Comamnds: {}
    
    """.format(', '.join([f.__name__ for f in get_commands()])))
