import pytest
from pathlib import Path
import shutil
import os
import re
import json
import decouple

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
    populate_test_env(request, tmp_path)
    tmp_path
    yield tmp_path

    def clean():
        shutil.rmtree(tmp_path)

    request.addfinalizer(clean)



def populate_test_env(request, tmp_path):
    if hasattr(request,"param"):
        # make necessary folders
        os.makedirs(tmp_path / "data" / "ts")
        # if first element is string then...
        if isinstance(request.param[0],tuple) and len(request.param[0])==1:
            for p in request.param[0]:
                print("###########################")
                if os.path.isfile(TEST_DATA / p):
                    shutil.copy(TEST_DATA / p, tmp_path/ "data" / "ts" / p)
                else:
                    raise AttributeError("Missing fixture data.")
                # handle_config_json(tmp_path, p)
        else:
            raise AttributeError("params fixture not matches type")


def handle_config_json(path, p):
    """
    specifically handle fixture of config.json file for testing.
    """
    if p != "config.json":
        pattern = re.compile("config((_[a-zA-Z0-9]*)*).json")
        if pattern.match(p):
            # rename to requested format
            os.rename(
                path / "config" / p,
                path / "config" / "config.json",
            )
            # set private api keys for testing
            # reading from testing environment variable
            with open(path / "config" / "config.json", "rb") as f:
                j = json.load(f)
            if "telegram" in j.keys():
                if j["telegram"]["token"] == "fixture":
                    j["telegram"]["token"] = decouple.config("TELEGRAM_TOKEN")
                with open(path / "config" / "config.json", "w") as f:
                    json.dump(j, f)
