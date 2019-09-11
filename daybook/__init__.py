import datetime
import os
import time

from pygit import PyGit

from daybook.utils import get_current_date


class Daybook(object):

    def __init__(self, base_dir):
        self.base_dir = base_dir
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


