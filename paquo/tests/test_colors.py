import pytest

from paquo.colors import QuPathColor


def test_incorrect_color():
    # NOTE THIS DOESNT CRASH BY DESIGN CURRENTLY!
    c = QuPathColor(300, 300, 300)
    assert not c.is_valid()
    c = QuPathColor(30, 30, 30)
    assert c.is_valid()


def test_color_roundtrip():
    c0 = (64, 64, 64)
    j0 = QuPathColor(*c0).to_java_rgb()
    c1 = QuPathColor.from_java_rgb(j0).to_rgb()
    assert c0 == c1


def test_color_mpl_rgba():
    assert QuPathColor(255, 255, 255).to_mpl_rgba() == (1, 1, 1, 1)


def test_repr():
    repr(QuPathColor(0, 0, 0, 255))
    repr(QuPathColor(0, 0, 0, 0))


def test_color_from_color():
    c = QuPathColor(0, 0, 0, 0)
    assert QuPathColor.from_any(c) == c


def test_from_any_error():
    with pytest.raises(TypeError):
        # noinspection PyTypeChecker
        QuPathColor.from_any(object())


def test_alpha_roundtrip():
    c0 = QuPathColor(1, 2, 3, 255)
    j0 = c0.to_java_rgba()
    c1 = QuPathColor.from_java_rgba(j0)

    assert c0 == c1
    assert c1.alpha == 255 == c0.alpha


def test_rgba_via_java_rgb():
    c0 = QuPathColor(1, 2, 3, 4)  # alpha will be lost
    j0 = c0.to_java_rgb()
    c1 = QuPathColor.from_java_rgba(j0)

    assert c0.red == c1.red
    assert c0.green == c1.green
    assert c0.blue == c1.blue
    assert c0.alpha == 4 and c1.alpha == 255


def test_rgb_via_java_rgba():
    c0 = QuPathColor(1, 2, 3, 4)
    j0 = c0.to_java_rgba()
    c1 = QuPathColor.from_java_rgb(j0)

    assert c0.red == c1.red
    assert c0.green == c1.green
    assert c0.blue == c1.blue
    assert c0.alpha == 4 and c1.alpha == 255


def test_from_java_typecheck():
    QuPathColor.from_java_rgb(0)
    QuPathColor.from_java_rgba(0)
    with pytest.raises(TypeError):
        QuPathColor.from_java_rgb(None)
    with pytest.raises(TypeError):
        QuPathColor.from_java_rgba(None)


def test_hexcolor():
    c0 = "#ff00ff"
    qc = QuPathColor.from_hex(c0)
    assert qc.to_rgb() == (255, 0, 255)
    assert c0 == qc.to_hex()

    with pytest.raises(ValueError):
        QuPathColor.from_hex("abc")

    assert qc == QuPathColor.from_any(c0)
