import os
import pytest
import shutil
import subprocess
from hamcrest import *
from pygit import PyGit

from daybook import Daybook
from daybook.entry import Entry

@pytest.fixture(scope="function")
def db() -> Daybook :
    test_repo_workspace = os.path.join("/tmp", "daybook", str(os.getpid()))
    print("Creating new project: {}".format(test_repo_workspace))
    yield Daybook("test_daybook", test_repo_workspace)
    print("Deleting project: {}".format(test_repo_workspace))
    shutil.rmtree(test_repo_workspace)

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
    db.commit_entry(e)
    entries = db.list_entries(max_entries=10)
    assert_that(entries, has_length(1))

def test_list_tags_single_tag(db:Daybook):
    e = Entry(
        "Some title",
        "entry here",
        tag_list=["entry1"]
    )
    db.commit_entry(e)
    tags = db.list_tags()
    assert_that(tags, only_contains("entry1"))

def test_list_tags_multiple_tags(db:Daybook):
    e1 = Entry(
        "Some title",
        "entry here",
        tag_list=["tag1", "tag2"]
    )
    e2 = Entry(
        "Another title",
        "entry here",
        tag_list=["tag3", "tag4"]
    )

    db.commit_entry(e1)
    db.commit_entry(e2)

    tags = db.list_tags()
    assert_that(tags, contains_inanyorder("tag1", "tag2", "tag3", "tag4"))


