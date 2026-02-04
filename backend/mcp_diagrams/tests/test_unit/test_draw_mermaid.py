"""Unit tests for Mermaid diagram generation."""

import pytest
import base64
import json
import zlib
from draw_mermaid import encode_mermaid, get_mermaid_url, draw_mermaid_diagram


pytestmark = pytest.mark.unit


class TestEncodeMermaid:
    """Tests for Mermaid code encoding."""

    def test_encode_mermaid_produces_base64_string(self, sample_mermaid_code):
        """Test that encode_mermaid returns a base64-encoded string."""
        # Act
        result = encode_mermaid(sample_mermaid_code)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify it's valid base64 (should not raise)
        try:
            base64.urlsafe_b64decode(result)
        except Exception as e:
            pytest.fail(f"Result is not valid base64: {e}")

    def test_encode_mermaid_is_decodable(self, sample_mermaid_code):
        """Test that encoded Mermaid can be decoded back to original."""
        # Arrange
        encoded = encode_mermaid(sample_mermaid_code)

        # Act - decode back
        decoded_bytes = base64.urlsafe_b64decode(encoded)
        decompressed = zlib.decompress(decoded_bytes)
        state = json.loads(decompressed.decode("utf-8"))

        # Assert
        assert state["code"] == sample_mermaid_code
        assert state["mermaid"]["theme"] == "default"
        assert state["autoSync"] is True

    def test_encode_mermaid_with_simple_code(self):
        """Test encoding of simple Mermaid code."""
        # Arrange
        simple_code = "flowchart TD\\n    A-->B"

        # Act
        result = encode_mermaid(simple_code)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encode_mermaid_with_complex_diagram(self):
        """Test encoding of complex Mermaid diagram."""
        # Arrange
        complex_code = """graph TB
    subgraph "Authentication"
        A[User] --> B{Login?}
        B -->|Yes| C[Dashboard]
        B -->|No| D[Register]
    end
    subgraph "Dashboard"
        C --> E[View Data]
        C --> F[Settings]
    end"""

        # Act
        result = encode_mermaid(complex_code)

        # Assert
        assert isinstance(result, str)
        # Complex diagrams should produce longer encoded strings
        assert len(result) > 50


class TestGetMermaidUrl:
    """Tests for Mermaid URL generation."""

    def test_get_mermaid_url_svg_format(self, sample_mermaid_code):
        """Test URL generation with SVG format (default)."""
        # Act
        result = get_mermaid_url(sample_mermaid_code, "svg")

        # Assert
        assert result.startswith("https://mermaid.ink/svg/pako:")
        assert "pako:" in result

    def test_get_mermaid_url_png_format(self, sample_mermaid_code):
        """Test URL generation with PNG format."""
        # Act
        result = get_mermaid_url(sample_mermaid_code, "png")

        # Assert
        assert result.startswith("https://mermaid.ink/img/pako:")
        assert "type=png" in result

    def test_get_mermaid_url_img_format(self, sample_mermaid_code):
        """Test URL generation with IMG format."""
        # Act
        result = get_mermaid_url(sample_mermaid_code, "img")

        # Assert
        assert result.startswith("https://mermaid.ink/img/pako:")
        assert "type=png" not in result

    def test_get_mermaid_url_default_format(self, sample_mermaid_code):
        """Test URL generation with default format."""
        # Act
        result = get_mermaid_url(sample_mermaid_code)

        # Assert - should default to SVG
        assert result.startswith("https://mermaid.ink/svg/pako:")


class TestDrawMermaidDiagram:
    """Tests for the main draw_mermaid_diagram function."""

    def test_draw_mermaid_diagram_returns_dict(self, sample_mermaid_code):
        """Test that draw_mermaid_diagram returns a dictionary."""
        # Act
        result = draw_mermaid_diagram(sample_mermaid_code)

        # Assert
        assert isinstance(result, dict)
        assert "url" in result
        assert "format" in result

    def test_draw_mermaid_diagram_svg_format(self, sample_mermaid_code):
        """Test diagram creation with SVG format."""
        # Act
        result = draw_mermaid_diagram(sample_mermaid_code, "svg")

        # Assert
        assert result["format"] == "svg"
        assert "mermaid.ink/svg/" in result["url"]

    def test_draw_mermaid_diagram_png_format(self, sample_mermaid_code):
        """Test diagram creation with PNG format."""
        # Act
        result = draw_mermaid_diagram(sample_mermaid_code, "png")

        # Assert
        assert result["format"] == "png"
        assert "mermaid.ink/img/" in result["url"]
        assert "type=png" in result["url"]

    def test_draw_mermaid_diagram_default_format(self, sample_mermaid_code):
        """Test diagram creation with default format."""
        # Act
        result = draw_mermaid_diagram(sample_mermaid_code)

        # Assert
        assert result["format"] == "svg"

    def test_draw_mermaid_diagram_strips_whitespace(self):
        """Test that the function strips leading/trailing whitespace."""
        # Arrange
        code_with_whitespace = """

        flowchart TD
            A-->B

        """

        # Act
        result = draw_mermaid_diagram(code_with_whitespace)

        # Assert
        assert "url" in result
        # URL should be generated successfully despite whitespace

    def test_draw_mermaid_diagram_url_is_valid(self, sample_mermaid_code):
        """Test that the generated URL is properly formatted."""
        # Act
        result = draw_mermaid_diagram(sample_mermaid_code)

        # Assert
        url = result["url"]
        assert url.startswith("https://")
        assert "mermaid.ink" in url
        assert "pako:" in url

    def test_draw_mermaid_diagram_with_sequence_diagram(self):
        """Test with a sequence diagram."""
        # Arrange
        sequence_code = """sequenceDiagram
    Alice->>John: Hello John, how are you?
    John-->>Alice: Great!
    Alice-)John: See you later!"""

        # Act
        result = draw_mermaid_diagram(sequence_code)

        # Assert
        assert "url" in result
        assert isinstance(result["url"], str)

    def test_draw_mermaid_diagram_with_class_diagram(self):
        """Test with a class diagram."""
        # Arrange
        class_code = """classDiagram
    Animal <|-- Duck
    Animal <|-- Fish
    Animal : +int age
    Animal : +String gender
    Animal: +isMammal()"""

        # Act
        result = draw_mermaid_diagram(class_code)

        # Assert
        assert "url" in result
        assert "mermaid.ink" in result["url"]


class TestMermaidEdgeCases:
    """Tests for edge cases and error handling."""

    def test_encode_empty_string(self):
        """Test encoding an empty string."""
        # Act
        result = encode_mermaid("")

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0

    def test_encode_with_special_characters(self):
        """Test encoding Mermaid code with special characters."""
        # Arrange
        code_with_special = """flowchart TD
    A["Node with 'quotes'"] --> B["Node with \\"double quotes\\""]
    B --> C{Decision with \\n newline?}"""

        # Act
        result = encode_mermaid(code_with_special)

        # Assert
        assert isinstance(result, str)
        # Should handle special characters without errors

    def test_draw_mermaid_diagram_consistency(self, sample_mermaid_code):
        """Test that multiple calls with same input produce same output."""
        # Act
        result1 = draw_mermaid_diagram(sample_mermaid_code)
        result2 = draw_mermaid_diagram(sample_mermaid_code)

        # Assert
        assert result1["url"] == result2["url"]
        assert result1["format"] == result2["format"]
