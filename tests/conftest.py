import pytest
from pathlib import Path
import shutil
import os
import re

##### MARKS #############################


def pytest_configure(config):
    config.addinivalue_line("markers", "wip: WORK IN PROGRESS")


##### TEST_ENVIRONMENT

CWD = Path(__file__).resolve()
TEST_DATA = CWD.parent / "fixtures"

@pytest.fixture
def temp_test_env(request, tmp_path):
    """
    set up environment for testing.
    creating config, copying the required files

    Arguments:
        request (pytest.fixture): x-tuple of strings, or 2-tuple (config-data) of x-tuple of
            files to copy in the config and data folder 
    """
    config_folder = tmp_path / "config"
    config_folder.mkdir()
    # param: empty tuple, do nothing
    if not request.param:
        pass
    # param: x-tuple of string names of files to be copied in config folder
    elif isinstance(request.param[0], str):
        for p in request.param:
            shutil.copy(TEST_DATA / p, tmp_path / "config" / p)
            #rename test config file to correct format
            rename_config(tmp_path, p)
    # param:c 2-tuple of x-tuples of files to be copied in config,data/ts folders
    elif isinstance(request.param[0], tuple) and len(request.param) == 2:
        for c in request.param[0]:
            shutil.copy(TEST_DATA / c, tmp_path / "config" / c)
            #rename test config file to correct format
            rename_config(tmp_path, c)
        for d in request.param[1]:
            os.makedirs(tmp_path / "data" / "ts")
            shutil.copy(TEST_DATA / d, tmp_path / "data" / "ts" / d)
    else:
        raise ValueError("Incorrect format. Pass x-tuple or 2-tuple of x-uple.")

    yield tmp_path

    def clean():
        shutil.rmtree(tmp_path)

    request.addfinalizer(clean)

def rename_config(path, p):
    """
    rename fixtures of config.json so that can be found by config module.
    """
    if p!="config.json":
        pattern = re.compile("config((_[a-zA-Z0-9]*)*).json")
        if pattern.match(p):
            os.rename(
                        path / "config" / p,
                        path / "config" / "config.json",
                        )

