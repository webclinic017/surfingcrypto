import pytest
from pathlib import Path
import shutil
import os

##### MARKS #############################

def pytest_configure(config):
    config.addinivalue_line("markers", "wip: WORK IN PROGRESS")
    config.addinivalue_line("markers", "exp: EXPERIMENTAL")

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
    return tmp_path
