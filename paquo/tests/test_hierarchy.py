import pytest

from paquo.hierarchy import QuPathPathObjectHierarchy


@pytest.fixture(scope="function")
def empty_hierarchy():
    yield QuPathPathObjectHierarchy()


def test_initial_state(empty_hierarchy: QuPathPathObjectHierarchy):
    h = empty_hierarchy
    assert h.is_empty
    assert h.root is not None  # root is auto populated
    assert len(h) == 0
