import pytest
import os


@pytest.fixture(scope="function")
def dirtest():
    """provide the name of the test directory to the test functions"""
    yield os.path.dirname(os.path.realpath(__file__))

