import datetime
import os
import time

import yaml
from pygit import PyGit

from daybook.utils import get_current_date


class Daybook(object):

    def __init__(self, book_name, base_dir):
        self.book_name = book_name
        self.base_dir = os.path.join(base_dir, book_name)
        if os.path.exists(os.path.join(base_dir, '.git')):
            self.git = PyGit(base_dir, new_repo=False)
        else:
            print("Creating {}".format(base_dir))
            os.makedirs(base_dir, exist_ok=True)
            self.git = PyGit(base_dir, new_repo=True)

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
        return os.path.join(self.base_dir, get_current_date(), str(time.time()) + ".txt")

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
        return [os.path.join(os.path.dirname(self.base_dir), fn) for fn in filenames if fn]



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
        for f in files:
            with open(f, 'r') as fp:
                y = yaml.safe_load(fp)
                if with_tags:
                    if not set(with_tags).intersection(y.tags):
                        continue
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






