from __future__ import annotations

import re
import shlex
from typing import Any
from typing import Match
from typing import NamedTuple
from typing import cast

from marko import block
from marko.block import BlockElement
from marko.helpers import MarkoExtension
from marko.source import Source


class FencedDiv(BlockElement):
    """
    Fenced div block: (:::className\nhello\n:::\n)

    Provides support for fenced divs as seen in Pandoc:
    https://pandoc.org/demo/example33/8.18-divs-and-spans.html

    Examples:

        :::hello
            This text is a paragraph, wrapped in a div
            with class "hello".
        :::

        :::{#major .alt <section> something="else"}
            This text is a paragraph, wrapped in a section
            with class "alt", id "major" and attribute
            "something" with value "else".
        :::
    """

    priority = 2
    pattern = re.compile(r"(:{3,})[^\n\S]*(.*?)$", re.M)

    class ParseInfo(NamedTuple):
        leading: str
        attributes: str

    def __init__(self, match: tuple[list, dict, str]) -> None:
        self.children = match[0]
        self.attributes = match[1]
        self.element_name = match[2]

    @classmethod
    def match(cls, source: Source) -> Match[str] | None:
        m = source.expect_re(cls.pattern)
        if not m:
            return None
        leading, info = m.groups()
        if leading[0] == ":" and ":" in info:
            return None
        attributes = info.lstrip("{").rstrip("}")
        source.context.div_info = cls.ParseInfo(leading, attributes)
        return m

    @classmethod
    def parse(cls, source: Source) -> tuple[list, dict, str]:
        source.next_line()
        source.consume()
        lines = []
        parse_info: FencedDiv.ParseInfo = source.context.div_info
        element, attributes = parse_attributes(parse_info.attributes)
        depth = 1
        while not source.exhausted:
            line = source.next_line()
            if line is None:
                break
            source.consume()
            m = re.match(r"(:{3,})[\n\s]*$", line, flags=re.M)
            if m and parse_info.leading in m.group(1):
                depth -= 1
            elif re.match(cls.pattern, line):
                depth += 1
            if depth <= 0:
                break
            lines.append(line)
        nested = "".join(lines)
        sub_source = Source(text=nested)
        sub_source.parser = source.parser
        doc = cast(block.Document, source.parser.block_elements["Document"]())
        with sub_source.under_state(doc):
            children = sub_source.parser.parse_source(sub_source)
        return children, attributes, element


class FencedDivRendererMixin:
    def render_fenced_div(self, element):
        # Render content
        parts = []
        for c in element.children:
            parts.append(self.render(c))
        content_html = "".join(parts)
        attributes = element.attributes
        attrs = {self.escape_html(k): self.escape_html(v) for k, v in attributes.items()}
        attr_list = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f"<{element.element_name} {attr_list}>\n{content_html}</{element.element_name}>\n"


# Create extension
FencedDivExtension = MarkoExtension(
    elements=[FencedDiv], renderer_mixins=[FencedDivRendererMixin]
)


def parse_attributes(attributes_str: str) -> tuple[str, dict[str, Any]]:
    tokens = shlex.split(attributes_str)
    ret = {}
    element = "div"
    for token in tokens:
        if token.startswith("#"):
            ret["id"] = token[1:]
        elif token.startswith("."):
            c = ret.get("class")
            if c:
                c = f"{c} {token[1:]}"
            else:
                c = token[1:]
            ret["class"] = c
        elif "=" in token:
            k, v = token.split("=")
            ret[k] = v.strip('"')
        elif token[0] == "<" and token[-1] == ">" and len(token) > 2:
            element = token[1:-1]
        else:
            ret[token] = None
    # If there's just one attribute without a value, interpret that as a class.
    if len(ret) == 1:
        k = list(ret.keys())[0]
        v = ret.pop(k)
        if v is None:
            ret["class"] = k
        else:
            ret[k] = v
    return element, ret


def make_extension():
    return FencedDivExtension
