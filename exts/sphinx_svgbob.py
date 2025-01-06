"""Svgbob extension for Sphinx"""

from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective, nodes
from typing import Any, List, Dict
import subprocess


class SvgbobDirective(SphinxDirective):
    """Sphinx directive to convert ASCII diagrams SVGs with svgbob."""

    has_content = True
    required_arguments = 0
    optional_arguments = 3
    final_argument_whitespace = False

    option_spec = {}

    # if I make this extension public add this function
    # def is_available(self) -> bool:

    def run(self) -> List[nodes.Node]:
        source: str = "\n".join(self.content)

        proc = subprocess.run(
            [
                "svgbob",
                # fmt: off
                "--stroke-color", "currentColor",
                "--fill-color", "currentColor",
                "--background", "transparent",
                # fmt: on
            ],
            input=source,
            stdout=subprocess.PIPE,
            encoding="utf-8",
            check=True,
        )

        svg: str = proc.stdout

        # use inline SVGs to inherit theme colors
        raw_node = nodes.raw("", f"<div>{svg}</div>", format="html")

        return [raw_node]


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_directive("svgbob", SvgbobDirective)
    return {
        "version": "1.0.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
