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

    # run only if parametrized, or None for special cases
    if hasattr(request, "param") and request.param is not None:

        # make necessary folders
        os.makedirs(tmp_path / "data" / "ts")
        os.makedirs(tmp_path / "data" / "cache")

        # if first element of param is string then tuple of strings
        if isinstance(request.param, dict):
            for folder in request.param:
                copy_tuple_elements_to_folder(request.param[folder], tmp_path, folder)
        else:
            print(request.param)
            raise NotImplementedError("params fixture not matches type")


def copy_tuple_elements_to_folder(tupleoftuples, tmp_path, folder_name):
    for filename in tupleoftuples:
        if os.path.isfile(TEST_DATA / filename):
            shutil.copy(
                TEST_DATA / filename,
                tmp_path / "data" / folder_name / filename,
            )
        else:
            raise AttributeError("Missing fixture data.")
        # handle_config_json(tmp_path, filename)


def handle_config_json(path, filename):
    """
    specifically handle fixture of config.json file for testing.
    """
    if filename != "config.json":
        pattern = re.compile("config((_[a-zA-Z0-9]*)*).json")
        if pattern.match(filename):
            # rename to requested format
            os.rename(
                path / "config" / filename,
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
