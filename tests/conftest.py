import pytest

from engine import search


@pytest.fixture(autouse=True)
def empty_table():
    search.TT.clear()
