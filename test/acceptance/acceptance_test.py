import os
import pytest
import shutil
import subprocess
from hamcrest import *
from pygit import PyGit

@pytest.fixture(scope="session")
def git_repo():
    test_repo_workspace = "/tmp/tests"
    this_dir=os.path.join(os.path.dirname(__file__), "..", "..")
    shutil.copytree(this_dir, test_repo_workspace)
    yield PyGit(test_repo_workspace)
    shutil.rmtree(test_repo_workspace)

def test_setup_test_workspace(git_repo):
    print(git_repo("log -n1"))

def test_list_tags():
    pytest.fail("We have no tags")

