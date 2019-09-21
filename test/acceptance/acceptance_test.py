import os
import pytest
import shutil
import subprocess
from hamcrest import *
from pygit import PyGit

from daybook import Daybook

@pytest.fixture(scope="function")
def db() -> Daybook :
    test_repo_workspace = os.path.join("/tmp", "daybook", str(os.getpid()))
    print("Creating new project: {}".format(test_repo_workspace))
    yield Daybook("test_daybook", test_repo_workspace, "git@github.com:jlecount/daybook_content.git")
    print("Deleting project: {}".format(test_repo_workspace))
    shutil.rmtree(test_repo_workspace)

def test_create_new_entry(db:Daybook):
    e = """
        Line One
        Line Two
        Line Three
        """
    db.commit_entry(e)
    entries = db.list_entries(max_entries=10)
    assert_that(entries, has_length(1))

def test_list_tags_single_tag(db:Daybook):
    e = """
        Some title
        entry here
        has tag @@entry1
        """
    db.commit_entry(e)
    tags = db.list_tags()
    assert_that(tags, only_contains("entry1"))

def test_list_entries_with_text_and_tags(db:Daybook):
    e1 = """
        Some title
        has tags @@tag1 and @@tag2
        More words here.
        """
    e2 = """
        another title
        another entry here
        Again, this also has tags @@tag1 and @@tag2
        """

    db.commit_entry(e1)
    db.commit_entry(e2)
    entries = db.list_entries(with_text="another", with_tags="tag1,tag2")
    assert_that(entries, has_length(1))



def test_get_entries_with_max_num(db:Daybook):
    e1 = """
        Some title
        has tags @@tag1 and @@tag2
        More words here.
        """
    e2 = """
        another title
        another entry here
        """

    db.commit_entry(e1)
    db.commit_entry(e2)

    entries = db.list_entries(max_entries=1)
    assert_that(entries, has_length(1))


def test_list_tags_multiple_tags(db:Daybook):
    e1 = """
        Some title
        has tags @@tag1 and @@tag2
        More words here.
        """
    e2 = """
        another title
        another entry here
        Again, this has tags @@tag3 and @@tag4
        """

    db.commit_entry(e1)
    db.commit_entry(e2)

    tags = db.list_tags()
    assert_that(tags, contains_inanyorder("tag1", "tag2", "tag3", "tag4"))


