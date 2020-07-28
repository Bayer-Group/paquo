import pytest

from paquo.colors import QuPathColor


def test_color_roundtrip():
    c0 = (64, 64, 64)
    j0 = QuPathColor(*c0).to_java_rgb()
    c1 = QuPathColor.from_java_rgb(j0).to_rgb()
    assert c0 == c1


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


def test_hexcolor():
    c0 = "#ff00ff"
    qc = QuPathColor.from_hex(c0)
    assert qc.to_rgb() == (255, 0, 255)
    assert c0 == qc.to_hex()

    with pytest.raises(ValueError):
        QuPathColor.from_hex("abc")

    assert qc == QuPathColor.from_any(c0)
