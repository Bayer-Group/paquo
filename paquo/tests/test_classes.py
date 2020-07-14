import pytest

from paquo.classes import QuPathPathClass


@pytest.fixture(scope='session')
def pathclass():
    yield QuPathPathClass.create("MyClass")


def test_pathclass_creation():
    pc = QuPathPathClass.create("MyClass", color=None)
    assert pc.parent is None
    assert pc.name == pc.id == "MyClass"


def test_pathclass_equality(pathclass):
    other = QuPathPathClass.create("MyClass2")
    same = QuPathPathClass.create("MyClass")
    assert pathclass == pathclass
    assert pathclass != other
    assert pathclass == same


def test_pathclass_creation_with_parent(pathclass):
    pc = QuPathPathClass.create("MyChild", parent=pathclass)
    assert pc.parent == pathclass
    assert pc.name == "MyChild"
    assert pc.id == "MyClass: MyChild"


def test_pathclass_colors():
    pc = QuPathPathClass.create("MyNew", color=None)
    my_class_color = (49, 139, 153)  # based on string MyNew
    assert pc.color.to_rgb() == my_class_color

    pc = QuPathPathClass.create("MyNew2", color=(1, 2, 3))
    assert pc.color.to_rgb() == (1, 2, 3)
