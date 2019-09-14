import datetime
import os
import shutil
import time

import yaml
from pygit import PyGit

from daybook.utils import get_current_date


class Daybook(object):

    def __init__(self, book_name, base_dir):
        self.book_name = book_name
        self.base_dir = os.path.expanduser(base_dir)
        self.project_dir = os.path.join(self.base_dir, self.book_name)
        if os.path.exists(os.path.join(self.base_dir, '.git')):
            self.git = PyGit(self.base_dir, new_repo=False)
        else:
            print("Creating project {0} within {1}".format(self.book_name, self.base_dir))
            os.makedirs(self.base_dir, exist_ok=True)
            self.git = PyGit(self.base_dir, new_repo=True)

        os.makedirs(self.project_dir, exist_ok=True)

    def commit_entry(self, entry):
        """Commit the entry to git"""
        filename = self._get_entry_filename()
        self._write_entry_to_disk(filename, entry.to_yaml())
        self.git("add {}".format(filename))

        return self.git(['commit', '-m', '{}'.format("New entry: {}".format(entry.title))])

    def _get_entry_filename(self):
        """
        Get a filename for a new entry.
        Sure, you could get name collisions if you call this more than once a second, but that's not a use-case here.
        :return:
        """
        return os.path.join(self.project_dir, get_current_date(), str(time.time()) + ".txt")

    def _write_entry_to_disk(self, filename, entry):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as fp:
            fp.writelines(entry)

    def _get_files_matching_dates(self, before_date, after_date):
        log_stmt = ["log", "--name-only", "--pretty=%b"]
        if before_date:
            log_stmt += [f"--until={before_date}"]
        if after_date:
            log_stmt += [f"--since={after_date}"]

        filenames = self.git(log_stmt)
        return [os.path.join(os.path.dirname(self.project_dir), fn) for fn in filenames if fn]

    def _get_matches(self, max_entries=10, with_tags=None, with_text=None, after_date=None, before_date=None):
        """
        :param max_entries: max number of matches to return
        :param with_tags: filter on tags.  None means no tag filtering
        :param with_text: filter on text.  None means no text filtering
        :param after_date: Only return entries after date. None means no after date filtering
        :param before_date: Only return entries before date. None means no after date filtering
        :return: all entries matching the given criteria
        """
        yaml_list = []
        files = self._get_files_matching_dates(before_date, after_date)
        num_found = 0
        for f in files:
            with open(f, 'r') as fp:
                y = yaml.safe_load(fp)
                if with_tags:
                    if not set(with_tags).intersection(y.tags):
                        continue
                if with_text:
                    if with_text not in y['body']:
                        continue
                num_found += 1

                if max_entries and num_found > max_entries:
                    return yaml_list

                yaml_list.append(y)
        return yaml_list

    def list_entries(self, max_entries=10, with_tags=None, with_text=None, after_date=None, before_date=None):
        """
        :param max_entries: max number of matches to return
        :param with_tags: filter on tags.  None means no tag filtering
        :param with_text: filter on text.  None means no text filtering
        :param after_date: Only return entries after date. None means no after date filtering
        :param before_date: Only return entries before date. None means no after date filtering
        :return: all entries matching the given criteria
        """
        entries = self._get_matches(max_entries, with_tags, with_text, after_date, before_date)

        def possible_decrypt(e):
            if self._is_encrypted(e):
                return self._decrypt(e['body'])
            else:
                return e['body']

        return [possible_decrypt(e) for e in entries]

    def list_tags(self):
        entries = self._get_matches()
        tags = []
        for e in entries:
            tags += e['tag_list']

        print("tags are {}".format(tags))
        return list(set(tags))

    def _decrypt(self, body):
        raise Exception("Encrypted data not yet supported")

    def _is_encrypted(self, y):
        if 'is_encrypted' in y:
            return y['is_encrypted']
        else:
            return False
