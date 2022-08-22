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

    yield tmp_path

def populate_test_env(request, tmp_path):
    if hasattr(request,"param"):
        # if first element is string then...
        if isinstance(request.param[0],tuple) and len(request.param[0])==1:
            for p in request.param[0]:
                print("###########################")
                if os.path.isfile(TEST_DATA / p):
                    if os.path.isfile(tmp_path/ "data" / "ts" / p):
                        shutil.copy(TEST_DATA / p, tmp_path/ "data" / "ts" / p)
                    else:
                        print(tmp_path/ "data" / "ts" / p)
                        raise AttributeError
                else:
                    print(TEST_DATA / p)
                    raise AttributeError
                # handle_config_json(tmp_path, p)
        else:
            # print(request.param[0])
            # print(type(request.param[0]))
            raise AttributeError("params fixture error")


# @pytest.fixture
# def populate_test_env_old(request):
#     """
#     populate with fixture files the requestend test environment.
#     """
#     # param: empty tuple, do nothing
#     # if not hasattr(request,"param"):
#     #     pass
#     # param: x-tuple of string names of files to be copied in config folder
#     if len(request.param) == 1:
#         # all are config files
#         for p in request.param:
#             shutil.copy(TEST_DATA / p, request.params[0][0] / "data" / "ts" / p)
#             # rename test config file to correct format
#             handle_config_json(tmp_path, p)
#     # param:c 2-tuple of x-tuples of files to be copied in config,data/ts folders
#     # elif isinstance(request.param[0], tuple) and len(request.param) == 2:
#         # config files
#         # for c in request.param[0]:
#         #     shutil.copy(TEST_DATA / c, tmp_path / "config" / c)
#         #     # rename test config file to correct format
#         #     handle_config_json(tmp_path, c)
#         # # data/ts files
#         # for d in request.param[1]:
#         #     os.makedirs(tmp_path / "data" / "ts")
#         #     shutil.copy(TEST_DATA / d, tmp_path / "data" / "ts" / d)
#     else:
#         print(isinstance(request.param,tuple))
#         print(len(request.param))
#         raise ValueError("Incorrect format. Pass a 1-tuple.")


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
