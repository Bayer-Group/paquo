from collections import ChainMap
from functools import partial
from io import StringIO
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import ElementTree

__all__ = ["br", "div", "h3", "h4", "img", "p", "span", "css", "repr_html", "repr_svg", "rawhtml"]


def repr_html(obj, *args, **kwargs):
    try:
        # noinspection PyProtectedMember
        return obj._repr_html_(*args, **kwargs)
    except AttributeError:
        return repr(obj)


def repr_svg(obj, *args, **kwargs):
    try:
        # noinspection PyProtectedMember
        return obj._repr_svg_(*args, **kwargs)
    except AttributeError:
        return repr(obj)


def css(style_dict):
    return ";".join(f"{k}:{v}" for k, v in style_dict.items())


class _Tag(str):
    """convenience helper class for building html"""
    __slots__ = ('tag',)

    def __new__(cls, name, *tags, default_style=None, **attrs):
        # convert args
        text = attrs.pop("text", None)
        default_style = default_style or {}
        if 'style' in attrs or default_style:
            attrs['style'] = css(ChainMap(attrs.pop('style'), default_style))
        # create the xml tag
        tag = Element(name, attrib=attrs)
        if text is not None:
            tag.text = text
        for t in tags:
            tag.append(t.tag)
        # write the tag to str
        with StringIO() as out:
            ElementTree(tag).write(out, encoding='unicode', method='html')
            tag_str = out.getvalue()
        # initialize str and attach the xml tag
        str_obj = super().__new__(cls, tag_str)
        str_obj.tag = tag
        return str_obj


class _NonEscapingString(str):
    # prevent raw html being escaped by:
    # https://github.com/python/cpython/blob/0be7c216/Lib/xml/etree/ElementTree.py#L1033-L1047
    def __contains__(self, item):
        if item in "&<>":
            return False
        return super().__contains__(item)  # pragma: no cover


# noinspection PyPep8Naming
def rawhtml(text: str):
    """hacky way to prevent escaping the provided string"""
    raw_text = _NonEscapingString(text)
    return _Tag(None, text=raw_text)


br = partial(_Tag, "br")
div = partial(_Tag, "div")
h3 = partial(_Tag, "h3")
h4 = partial(_Tag, "h4", default_style={"margin-bottom": "0.5em"})
img = partial(_Tag, "img")
p = partial(_Tag, "p")
span = partial(_Tag, "span")
