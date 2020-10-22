import re
import sys
import time
import yaml
from clint.textui import puts as _puts, indent as _indent, colored as _colored
import os
from inspect import getmembers as _getmembers
from inspect import isfunction as _isfunction

from pygit import PyGit

from daybook import Daybook, encryption
from daybook.utils import str_to_bool, get_entry_filename
from fileio import editor_create_entry, write_config, read_config

DAYBOOK_CFG = os.path.join(os.getenv("HOME"), ".daybook.yml")
_CFG = None


def get_commands() -> list:
    this_module = sys.modules[__name__]
    functions_list = [o[0] for o in _getmembers(this_module) if _isfunction(o[1]) and not o[0].startswith('_')]
    return [getattr(this_module, f) for f in functions_list if f != 'get_commands']


def _get_daybook_cfg():
    global _CFG
    if not _CFG:
        _CFG = read_config(DAYBOOK_CFG)
    return _CFG

def _get_remote_url_for_diary(d):
    if not d in _get_daybook_cfg()['daybooks']:
        print("You must install your diary first")
        sys.exit(1)
    else:
        return _get_daybook_cfg()['daybooks'][d]['remote_url']


def _get_base_dir_for_diary(d):
    if not d in _get_daybook_cfg()['daybooks']:
        print("You must install your diary first")
        sys.exit(1)
    else:
        return _get_daybook_cfg()['daybooks'][d]['base_dir']



def _add_project_to_cfg(existing_cfg, name, base_dir, remote_url, default_template_filename=None):
    if 'daybooks' not in existing_cfg:
        existing_cfg['daybooks'] = {}
    cfg = {
        'base_dir': base_dir,
        'remote_url': remote_url
    }
    if default_template_filename:
        cfg['default_template'] = default_template_filename

    existing_cfg['daybooks'][name] = cfg
    write_config(DAYBOOK_CFG, existing_cfg)


def install(diary_name: str, base_dir: str, remote_url: str, default_template_filename: str = None):
    _add_project_to_cfg(_get_daybook_cfg(), diary_name, base_dir, remote_url,
                        default_template_filename=default_template_filename)


def list_daybooks():
    for db in _get_daybook_cfg()['daybooks']:
        print(db)




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


def delete_entry(diary_name: str,
               entries_back_num:int=0,
               with_tags:str=None,
               before_date=None,
               after_date=None,
               is_encrypted_on_create:bool=None,
               title_on_create:str="",
               tags_on_create:str="",
               create_if_missing:bool=False) -> None:
    """
     Delete entries.  This deletes the underlying files, and does not rewind entries back in time, per se.

    :param diary_name: the name of the diary
    :param entries_back_num: the entry number to edit.  The most recent is 0 (default), before that is 1, etc.
    :param with_tags: filter entries with tags given
    :param before_date: filter entries found via git time filtering (like with git --until)
    :param after_date: filter entries found via git time filtering (like with git --since)
    :param is_encrypted_on_create: if create_if_missing, should the new entry be encrypted?
    :return: None
    """
    book = Daybook(diary_name, _get_base_dir_for_diary(diary_name), _get_remote_url_for_diary(diary_name))
    max_entries = entries_back_num + 1

    # Tempoary workaround to argh not processing boolean strings properly...
    try:
        is_encrypted_on_create = str_to_bool(is_encrypted_on_create)
    except:
        print("is_encrypted must only be True or False")
        sys.exit(1)

    entries = book.list_entries(
        max_entries=max_entries,
        after_date=after_date,
        before_date=before_date,
        with_tags=with_tags
    )
    if not entries:
        print("No entry/entries found")
        return
    else:
        filenames = [f for f,_ in entries]
        num_entries = len(filenames)
        print("You are about to delete the following {} entries.".format(num_entries))
        print(50 * '-')
        for f in filenames:
            with open(f, 'r') as fp:
                for line in fp.readlines():
                    print(line.strip())
        print(50 * '-')
        print("Confirm deletion -- y/n")
        resp = sys.stdin.readline().strip()
        if resp == 'y':
            print("Deleting {} entries.".format(num_entries))
            book.execute_cmd(["rm", "{}".format(' '.join(filenames))])
            book.execute_cmd(["commit", "-m", '{}'.format("deletion of entries: {}".format(', '.join(filenames)))])


def edit_entry(diary_name: str,
               entries_back_num:int=0,
               with_tags:str=None,
               before_date=None,
               after_date=None,
               is_encrypted_on_create:bool=None,
               title_on_create:str="",
               tags_on_create:str="",
               create_if_missing:bool=False) -> None:
    """
    Edit an entry.  Optionally this can be created if it didn't already exist.

    :param diary_name: the name of the diary
    :param entries_back_num: the entry number to edit.  The most recent is 0 (default), before that is 1, etc.
    :param with_tags: filter entries with tags given
    :param before_date: filter entries found via git time filtering (like with git --until)
    :param after_date: filter entries found via git time filtering (like with git --since)
    :param is_encrypted_on_create: if create_if_missing, should the new entry be encrypted?
    :param title_on_create: if create_if_missing, optional title
    :param tags_on_create: if create_if_missing, optional tags
    :param create_if_missing: should the entry be created if nothing was found?
    :return: None
    """
    book = Daybook(diary_name, _get_base_dir_for_diary(diary_name), _get_remote_url_for_diary(diary_name))
    max_entries = entries_back_num + 1

    # Tempoary workaround to argh not processing boolean strings properly...
    try:
        is_encrypted_on_create = str_to_bool(is_encrypted_on_create)
    except:
        print("is_encrypted must only be True or False")
        sys.exit(1)

    entries = book.list_entries(
        max_entries=max_entries,
        after_date=after_date,
        before_date=before_date,
        with_tags=with_tags
    )

    if not entries:
        if create_if_missing:
            if is_encrypted_on_create == None:
                print("You must pass in either True or False for --is-encrypted when creating a new entry implicitly.")
                return
            else:
                create_entry(
                    diary_name,
                    is_encrypted=is_encrypted_on_create,
                    tags=tags_on_create,
                    title=title_on_create
                )
        else:
            print("No entry found")
            return
    else:
        f, entry = entries[-1]
        entry = ''.join(entry)
        title = _get_entry_title(entry)
        entry_modified = editor_create_entry(entry)

        if not entry_modified:
            print("No entry.  Nothing committed.")
        elif entry_modified == entry:
            print("No changes.  Nothing committed.")
        else:
            print(book.commit_edited_entry(f, title, entry_modified))


def create_entry(diary_name: str, tags:str="", title:str=None, is_encrypted:bool=False) -> None:
    book = Daybook(diary_name, _get_base_dir_for_diary(diary_name), _get_remote_url_for_diary(diary_name))
    entry = editor_create_entry(title=title, tags=tags)
    title = _get_entry_title(entry)

    entry_filename = get_entry_filename(book.project_dir, time.time(), is_encrypted)
    try:
        is_encrypted = str_to_bool(is_encrypted)
    except:
        print("is_encrypted must only be True or False")
        sys.exit(1)

    if is_encrypted:
        entry = encryption.encrypt(entry)

    if not entry:
        print("No entry.  Nothing committed.")
    else:
        print(book.commit_entry(entry, filename=entry_filename, title=title))


def list_entries(diary_name: str, max_entries:int=None, with_tags=None, with_text=None, before_date=None, after_date=None):
    max_entries=int(max_entries or '1000') #FIXME: how do we do this generally correctly?
    book = Daybook(diary_name, _get_base_dir_for_diary(diary_name), _get_remote_url_for_diary(diary_name))
    entries = book.list_entries(
        max_entries=max_entries,
        with_tags=with_tags,
        with_text=with_text,
        after_date=after_date,
        before_date=before_date
    )
    n=0
    for f, e in entries:
        order_description = "(most recent)" if n==0 else "({n} back)".format(n=n)
        _puts(_colored.blue("----- {f} {order_description} -----".format(f=f, order_description=order_description)))
        n+=1
        for line in e:
            with _indent(4):
                _puts(line.strip())



def list_tags(diary_name: str) -> None:
    book = Daybook(diary_name, _get_base_dir_for_diary(diary_name), _get_remote_url_for_diary(diary_name))
    print(book.list_tags())


def sync():
    base_dirs = [v[1]['base_dir'] for v in _get_daybook_cfg()['daybooks'].items()]
    for b in base_dirs:
        PyGit(b)("pull origin master")
        PyGit(b)("rebase origin/master")
        PyGit(b)("push origin master")

def list_commands() -> None:
    print("""
    
    Comamnds: {}
    
    """.format(', '.join([f.__name__ for f in get_commands()])))
