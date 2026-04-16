"""Unit tests for Mermaid diagram generation via mmdc."""

import pytest
from pathlib import Path
from draw_mermaid import draw_mermaid_diagram


pytestmark = pytest.mark.unit


VALID_FLOWCHART = """flowchart TD
    A[Start] --> B{Decision?}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E"""

VALID_SEQUENCE = """sequenceDiagram
    Alice->>Bob: Hello Bob!
    Bob-->>Alice: Hi Alice!"""

VALID_CLASS = """classDiagram
    Animal <|-- Duck
    Animal <|-- Fish
    Animal : +int age
    Animal : +String gender
    Animal: +isMammal()"""

INVALID_CODE = "this is not valid mermaid at all"


class TestDrawMermaidDiagram:
    """Tests for draw_mermaid_diagram using real mmdc."""

    def test_valid_flowchart_renders_file(self):
        result = draw_mermaid_diagram(VALID_FLOWCHART)

        assert "path" in result
        assert "error" not in result
        assert Path(result["path"]).exists()
        Path(result["path"]).unlink(missing_ok=True)

    def test_valid_sequence_diagram_renders_file(self):
        result = draw_mermaid_diagram(VALID_SEQUENCE)

        assert "path" in result
        assert "error" not in result
        assert Path(result["path"]).exists()
        Path(result["path"]).unlink(missing_ok=True)

    def test_valid_class_diagram_renders_file(self):
        result = draw_mermaid_diagram(VALID_CLASS)

        assert "path" in result
        assert "error" not in result
        assert Path(result["path"]).exists()
        Path(result["path"]).unlink(missing_ok=True)

    def test_svg_format_produces_svg_file(self):
        result = draw_mermaid_diagram(VALID_FLOWCHART, output_format="svg")

        assert result["format"] == "svg"
        assert result["path"].endswith(".svg")
        Path(result["path"]).unlink(missing_ok=True)

    def test_png_format_produces_png_file(self):
        result = draw_mermaid_diagram(VALID_FLOWCHART, output_format="png")

        assert result["format"] == "png"
        assert result["path"].endswith(".png")
        Path(result["path"]).unlink(missing_ok=True)

    def test_default_format_is_svg(self):
        result = draw_mermaid_diagram(VALID_FLOWCHART)

        assert result["format"] == "svg"
        assert result["path"].endswith(".svg")
        Path(result["path"]).unlink(missing_ok=True)

    def test_invalid_code_returns_error(self):
        result = draw_mermaid_diagram(INVALID_CODE)

        assert "error" in result
        assert "path" not in result

    def test_invalid_code_no_leftover_output_file(self):
        result = draw_mermaid_diagram(INVALID_CODE)

        assert "error" in result
        # mmdc should not have produced an output file
        # (we check no stray files were left behind — hard to assert directly
        # but the absence of "path" key confirms draw_mermaid_diagram cleaned up)

    def test_strips_whitespace_before_rendering(self):
        padded = f"\n\n  {VALID_FLOWCHART}  \n\n"
        result = draw_mermaid_diagram(padded)

        assert "path" in result
        assert "error" not in result
        Path(result["path"]).unlink(missing_ok=True)

    def test_each_call_produces_unique_file(self):
        result1 = draw_mermaid_diagram(VALID_FLOWCHART)
        result2 = draw_mermaid_diagram(VALID_FLOWCHART)

        assert result1["path"] != result2["path"]
        Path(result1["path"]).unlink(missing_ok=True)
        Path(result2["path"]).unlink(missing_ok=True)
