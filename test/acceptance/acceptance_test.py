import os
import pytest
import shutil
import subprocess
from hamcrest import *
from pygit import PyGit

from daybook import Daybook
from daybook.entry import Entry

@pytest.fixture(scope="module")
def db() -> Daybook :
    test_repo_workspace = os.path.join("/tmp", "daybook", str(os.getpid()))
    print("workspace is " + test_repo_workspace)
    yield Daybook("test_daybook", test_repo_workspace)
    #shutil.rmtree(test_repo_workspace)

def test_create_new_entry(db:Daybook):
    e = Entry(
        "Some title",
        """
        Line One
        Line Two
        Line Three""",
        tag_list=None,
        is_encrypted=None
        )
    print(db.commit_entry(e))

def test_list_all_entries(db:Daybook):
    entries = db.list_entries(max_entries=10)
    print(entries)

def test_list_tags():
    pytest.fail("We have no tags")

