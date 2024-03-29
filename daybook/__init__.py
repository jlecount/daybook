import datetime
import os
import re
import shutil
import subprocess
import sys
import time

import yaml
from pygit import PyGit

from daybook.utils import get_current_date, sort_filename_by_date, get_entry_filename


class Daybook(object):

    def __init__(self, book_name, base_dir, remote_url):
        self.book_name = book_name
        self.remote_url = remote_url
        self.base_dir = os.path.expanduser(base_dir)
        self.project_dir = os.path.join(self.base_dir, self.book_name)
        if os.path.exists(os.path.join(self.base_dir, '.git')):
            self.git = PyGit(self.base_dir, new_repo=False)
        else:
            print(
                "Creating project {0} within {1} with remote {2}".format(
                    self.book_name,
                    self.base_dir,
                    self.remote_url
                )
            )
            os.makedirs(self.base_dir, exist_ok=True)
            self.git = PyGit(self.base_dir, new_repo=True)
            self.git("remote add origin {}".format(self.remote_url))

        os.makedirs(self.project_dir, exist_ok=True)

    def execute_cmd(self, cmd: list) -> list:
        try:
            return self.git(cmd)
        except subprocess.CalledProcessError as e:
            return []

    def commit_edited_entry(self, filename: str, title:str, entry: str) -> None:
        self._write_entry_to_disk(filename, entry)
        self.execute_cmd("add {}".format(filename))

        results = self.execute_cmd(['commit', '-m', '{}'.format("{}".format(title))])
        return "Updated entry: {0} with title: {1}".format(filename, title)

    def commit_entry(self, entry: str, filename:str, title=None) -> None:
        """Commit the entry to git"""
        if not title:
            title = "<no title given>"
        self._write_entry_to_disk(filename, entry)
        self.execute_cmd("add {}".format(filename))

        results = self.execute_cmd(['commit', '-m', '{}'.format("{}".format(title))])
        return "Saved entry: {0} with title: {1}".format(filename, title)

    def _get_entry_filename(self, timestamp=time.time(), is_encrypted=False):
        """
        Get a filename for a new entry.
        Sure, you could get name collisions if you call this more than once a second, but that's not a use-case here.
        :return str: the filename
        """
        return get_entry_filename(self.project_dir, timestamp, is_encrypted)

    def _write_entry_to_disk(self, filename: str, entry: str) -> None:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as fp:
            fp.writelines(entry)

    def _get_files_matching_dates(self, before_date, after_date):
        """

        :param before_date: a date format to be parsed by git --until
        :param after_date: a date format to be parsed by git --since
        
        :return: a set of files between two dates.  The format should be that which can be parsed by git.
        """
        cmd = ['git', 'log', '--name-only', '--author-date-order', '--pretty=%b']
        if before_date:
            cmd += [f"--until={before_date}"]
        if after_date:
            cmd += [f"--since={after_date}"]

        cmd += ['.'] # append the relative-dir that represents the book context we're in

        raw = subprocess.check_output(cmd, cwd=self.project_dir).decode('ascii').split('\n')

        filenames = [f for f in raw if f and os.path.exists(os.path.join(self.base_dir, f))]
        out = []
        sorted_filenames = sorted(filenames, key=sort_filename_by_date, reverse=True)
        for fn in sorted_filenames:
            if fn:
                value = os.path.join(os.path.dirname(self.project_dir), fn)
                if value not in out:
                    out.append(value)
        return out


    def _found_any_tag_in_entry(self, entry_lines, tag_list):
        entry_str = '\n'.join(entry_lines)
        for tag in tag_list:
            if tag in entry_str:
                return True
        return False

    def _found_any_text_in_entry(self, entry_list, text):
        return text in '\n'.join(entry_list)

    def _get_matches(self, max_entries:int=-1, with_tags:str=None, with_text:str=None, after_date=None, before_date=None) -> tuple:
        """
        :param max_entries: max number of matches to return.  If negative, return all
        :param with_tags: filter on tags.  None means no tag filtering
        :param with_text: filter on text.  None means no text filtering
        :param after_date: Only return entries after date. None means no after date filtering
        :param before_date: Only return entries before date. None means no after date filtering
        :return: A tuple of (file, entry) all entries matching the given criteria
        """
        yaml_list = []
        files = self._get_files_matching_dates(before_date, after_date)
        num_found = 0
        for f in files:
            with open(f, 'r') as fp:
                entry = fp.readlines()
                if with_tags:
                    if not self._found_any_tag_in_entry(entry, with_tags.split(',')):
                        continue
                if with_text:
                    if not self._found_any_text_in_entry(entry, with_text):
                        continue

                num_found += 1
                if max_entries > 0 and num_found > max_entries:
                    return yaml_list

                yaml_list.append((f, entry))
        return yaml_list

    def list_entries(self, max_entries=-1, with_tags=None, with_text=None, after_date=None, before_date=None) -> tuple:
        """
        :param max_entries: max number of matches to return.  If negative, return all
        :param with_tags: filter on tags.  None means no tag filtering
        :param with_text: filter on text.  None means no text filtering
        :param after_date: Only return entries after date. None means no after date filtering
        :param before_date: Only return entries before date. None means no after date filtering
        :return: tuple of (file, entry) of all entries matching the given criteria.  All entries are decrypted.
        """
        filenames_and_entries = self._get_matches(max_entries, with_tags, with_text, after_date, before_date)

        def possible_decrypt(f: str, e: str) -> str:
            if f.endswith(".txt.encrypted"):
                return self._decrypt(e)
            else:
                return e

        return [(f, possible_decrypt(f, e)) for f, e in filenames_and_entries]

    def _find_tags_in_entry(self, entry: list) -> list:
        return [t.replace("@@", '') for t in re.findall(r'@@\S+', '\n'.join(entry))]

    def list_tags(self):
        files_and_entries = self._get_matches()
        tags = []
        for f, e in files_and_entries:
            tags += self._find_tags_in_entry(e)

        return list(set(tags))

    def _decrypt(self, body):
        raise Exception("Encrypted data not yet supported")
