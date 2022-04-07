import string
from typing import NamedTuple
from typing import Tuple
from typing import Union

from paquo.java import ColorTools
from paquo.java import Integer

ColorTypeRGB = Tuple[int, int, int]
ColorTypeRGBA = Tuple[int, int, int, int]
ColorType = Union[ColorTypeRGB, ColorTypeRGBA, 'QuPathColor', str]


class QuPathColor(NamedTuple):
    """color representation in paquo

    >>> c = QuPathColor(128, 128, 160, alpha=240)
    """
    red: int
    green: int
    blue: int
    alpha: int = 255

    def is_valid(self) -> bool:
        """tests if a QuPathColor is valid

        (there are currently no validation checks performed on __init__)
        """
        for value in self.to_rgba():
            if not (0 <= value <= 255):
                # raise ValueError("val not an integer 0 <= val <= 255")
                return False
        return True

    def to_rgb(self) -> ColorTypeRGB:
        """convert to 3 * uint8 rgb tuple"""
        return self.red, self.green, self.blue

    def to_rgba(self) -> ColorTypeRGBA:
        """convert to 4 * uint8 rgba tuple"""
        return self.red, self.green, self.blue, self.alpha

    def to_mpl_rgba(self) -> Tuple[float, float, float, float]:
        """convert to 4 * float rgba tuple (mpl compatible)"""
        r, g, b, a = self.to_rgba()
        return r / 255.0, g / 255.0, b / 255.0, a / 255.0

    def to_hex(self) -> str:
        """convert to hex color. loses alpha."""
        r, g, b = self.to_rgb()
        return f"#{r:02x}{g:02x}{b:02x}"

    @classmethod
    def from_hex(cls, hex_color: str) -> 'QuPathColor':
        """convert from hex_color"""
        if (
            not isinstance(hex_color, str)
            or len(hex_color) != 7
            or hex_color[0] != "#"
            or any(c not in string.hexdigits for c in hex_color[1:])
        ):
            raise ValueError("requires a hexcolor #000000 - #ffffff")
        return cls(*(int(hex_color[i:i+2], 16) for i in (1, 3, 5)))

    def to_java_rgb(self) -> Integer:
        """"convert to the java rgb integer representation used by qupath"""
        return ColorTools.makeRGB(*self.to_rgb())

    @classmethod
    def from_java_rgb(cls, java_rgb: int) -> 'QuPathColor':
        """convert from java but ignore the alpha value in java_rgb"""
        if not isinstance(java_rgb, int):
            raise TypeError("requires an integer")
        r = int(ColorTools.red(java_rgb))
        g = int(ColorTools.green(java_rgb))
        b = int(ColorTools.blue(java_rgb))
        # noinspection PyArgumentList
        return cls(r, g, b)

    def to_java_rgba(self) -> Integer:
        """"convert to the java argb integer representation used by qupath"""
        return ColorTools.makeRGBA(*self.to_rgba())

    @classmethod
    def from_java_rgba(cls, java_rgba: int) -> 'QuPathColor':
        """converts a java integer color into a QuPathColor instance"""
        if not isinstance(java_rgba, int):
            raise TypeError("requires an integer")
        r = int(ColorTools.red(java_rgba))
        g = int(ColorTools.green(java_rgba))
        b = int(ColorTools.blue(java_rgba))
        a = int(ColorTools.alpha(java_rgba))
        # noinspection PyArgumentList
        return cls(r, g, b, a)

    def __repr__(self) -> str:
        if self.alpha != 255:
            return f"Color{self.to_rgba()}"
        return f"Color{self.to_rgb()}"

    def _repr_html_(self):
        from paquo._repr import div
        from paquo._repr import span
        a = self.alpha / 255.
        alpha = f"alpha={a:0.3f}" if self.alpha != 255 else ""
        return div(
            span(text=f"{self.__class__.__name__}: ", style={"font-weight": "bold"}),
            div(style={
                "display": "inline-block",
                "vertical-align": "text-top",
                "margin-right": "0.2em",
                "width": "1em",
                "height": "1em",
                "border": "1px solid black",
                "opacity": str(a),
                "background": self.to_hex()
            }),
            span(text=f"{self.to_hex()} {alpha}"),
        )

    @classmethod
    def from_any(cls, value: ColorType) -> 'QuPathColor':
        """try creating a QuPathColor from all supported types"""
        if isinstance(value, QuPathColor):
            return cls(*value.to_rgba())
        elif isinstance(value, (tuple, list)):
            return cls(*value)
        elif isinstance(value, str):
            return cls.from_hex(value)
        else:
            raise TypeError("can't convert to QuPathColor")
