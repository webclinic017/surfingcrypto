import pytest
from pathlib import Path
import shutil
import os

##### MARKS #############################

def pytest_configure(config):
    config.addinivalue_line("markers", "wip: WORK IN PROGRESS")

##### TEST_ENVIRONMENT 

CWD = Path(__file__).resolve()
TEST_DATA=CWD.parent / "fixtures"

@pytest.fixture
def temp_test_env(request,tmp_path):
    config_folder=tmp_path/"config"
    config_folder.mkdir()
    for p in request.param:
        shutil.copy(
            TEST_DATA/p,
            tmp_path/"config"/p)
    yield tmp_path
    def clean():
        shutil.rmtree(tmp_path)
    request.addfinalizer(clean)

@pytest.fixture
def temp_test_env2(request,tmp_path):
    """
    set up environment for testing.
    creating config, copying the required files

    Arguments:
        request (pytest.fixture): x-tuple of strings, or 2-tuple (config-data) of x-tuple of
            files to copy in the config and data folder 
    """
    config_folder=tmp_path/"config"
    config_folder.mkdir()
    if isinstance(request.param[0] ,str):
        for p in request.param:
            shutil.copy(
                TEST_DATA/p,
                tmp_path/"config"/p)
    elif isinstance(request.param[0] ,tuple) and len(request.param)==2:
        for c in request.param[0]:
            shutil.copy(
                TEST_DATA/c,
                tmp_path/"config"/c)
        for d in request.param[1]:
            os.makedirs(tmp_path/"data"/"ts")
            shutil.copy(
                TEST_DATA/d,
                tmp_path/"data"/"ts"/d)

    yield tmp_path
    def clean():
        shutil.rmtree(tmp_path)
    request.addfinalizer(clean)



