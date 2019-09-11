import os
import pytest
import shutil
import subprocess
from hamcrest import *
from pygit import PyGit

from daybook.entry import Entry


@pytest.fixture(scope="module")
def db():
    test_repo_workspace = os.path.join("/tmp", "daybook", os.getpid())
    yield Daybook(test_repo_workspace)
    #zshutil.rmtree(test_repo_workspace)


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

def test_list_tags():
    pytest.fail("We have no tags")

