"""Unit tests for technical diagram generation."""

import pytest
from unittest.mock import MagicMock, patch
from draw_diagram import draw_diagram


pytestmark = pytest.mark.unit


class TestDrawDiagram:
    """Tests for the draw_diagram function."""

    def test_draw_diagram_creates_diagram_with_title(self, mock_diagram_library):
        """Test that draw_diagram creates a Diagram with the correct title."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            # Act
            draw_diagram(
                title="Test Diagram",
                code="pass",
                filename="test_output",
            )

            # Assert
            mock_diagram_class.assert_called_once()
            call_kwargs = mock_diagram_class.call_args[1]
            assert "Test Diagram" in call_kwargs["name"]
            assert call_kwargs["show"] is False
            assert call_kwargs["filename"] == "test_output"

    def test_draw_diagram_uses_default_direction(self):
        """Test that draw_diagram uses default direction LR."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            # Act
            draw_diagram(
                title="Test",
                code="pass",
                filename="test",
            )

            # Assert
            call_kwargs = mock_diagram_class.call_args[1]
            assert call_kwargs["direction"] == "LR"

    def test_draw_diagram_accepts_custom_direction(self):
        """Test that draw_diagram accepts custom direction."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            # Act
            draw_diagram(
                title="Test",
                code="pass",
                filename="test",
                direction="TB",
            )

            # Assert
            call_kwargs = mock_diagram_class.call_args[1]
            assert call_kwargs["direction"] == "TB"

    def test_draw_diagram_merges_graph_attributes(self):
        """Test that custom graph attributes are merged with defaults."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            custom_attrs = {"rankdir": "TB", "bgcolor": "white"}

            # Act
            draw_diagram(
                title="Test",
                code="pass",
                filename="test",
                graph_attr=custom_attrs,
            )

            # Assert
            call_kwargs = mock_diagram_class.call_args[1]
            graph_attr = call_kwargs["graph_attr"]

            # Should have default attributes
            assert "concentrate" in graph_attr
            assert "splines" in graph_attr

            # Should have custom attributes
            assert graph_attr["rankdir"] == "TB"
            assert graph_attr["bgcolor"] == "white"

    def test_draw_diagram_executes_code(self, sample_diagram_code):
        """Test that draw_diagram executes the provided code."""
        # Arrange
        with (
            patch("draw_diagram.Diagram") as mock_diagram_class,
            patch("builtins.exec") as mock_exec,
        ):
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            # Act
            draw_diagram(
                title="Test",
                code=sample_diagram_code,
                filename="test",
            )

            # Assert
            mock_exec.assert_called_once()
            # The code should be passed to exec
            assert mock_exec.call_args[0][0] == sample_diagram_code

    def test_draw_diagram_with_custom_node_attributes(self):
        """Test that custom node attributes are passed correctly."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            custom_node_attr = {"shape": "box", "style": "filled"}

            # Act
            draw_diagram(
                title="Test",
                code="pass",
                filename="test",
                node_attr=custom_node_attr,
            )

            # Assert
            call_kwargs = mock_diagram_class.call_args[1]
            assert call_kwargs["node_attr"]["shape"] == "box"
            assert call_kwargs["node_attr"]["style"] == "filled"

    def test_draw_diagram_with_custom_edge_attributes(self):
        """Test that custom edge attributes are passed correctly."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            custom_edge_attr = {"color": "blue", "style": "dashed"}

            # Act
            draw_diagram(
                title="Test",
                code="pass",
                filename="test",
                edge_attr=custom_edge_attr,
            )

            # Assert
            call_kwargs = mock_diagram_class.call_args[1]
            assert call_kwargs["edge_attr"]["color"] == "blue"
            assert call_kwargs["edge_attr"]["style"] == "dashed"

    def test_draw_diagram_show_is_false(self):
        """Test that show parameter is always False."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            # Act
            draw_diagram(
                title="Test",
                code="pass",
                filename="test",
            )

            # Assert
            call_kwargs = mock_diagram_class.call_args[1]
            assert call_kwargs["show"] is False

    def test_draw_diagram_creates_file(self):
        """Test that draw_diagram creates a file."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_context = MagicMock()
            mock_diagram_class.return_value.__enter__ = MagicMock(
                return_value=mock_context
            )
            mock_diagram_class.return_value.__exit__ = MagicMock()

            # Act
            draw_diagram(
                title="Test Diagram",
                code="pass",
                filename="my_test_file",
            )

            # Assert
            call_kwargs = mock_diagram_class.call_args[1]
            assert call_kwargs["filename"] == "my_test_file"


class TestDrawDiagramDefaults:
    """Tests for default attributes in draw_diagram."""

    def test_default_graph_attributes(self):
        """Test that default graph attributes are correct."""
        # Arrange
        from draw_diagram import default_graph_attr

        # Assert
        assert default_graph_attr["concentrate"] == "true"
        assert default_graph_attr["splines"] == "spline"

    def test_default_node_attributes_is_dict(self):
        """Test that default node attributes exist."""
        # Arrange
        from draw_diagram import default_node_attr

        # Assert
        assert isinstance(default_node_attr, dict)

    def test_default_edge_attributes_is_dict(self):
        """Test that default edge attributes exist."""
        # Arrange
        from draw_diagram import default_edge_attr

        # Assert
        assert isinstance(default_edge_attr, dict)


class TestDrawDiagramIntegration:
    """Integration-style tests for draw_diagram (still mocked but more realistic)."""

    @pytest.mark.slow
    def test_draw_diagram_with_realistic_code(self):
        """Test draw_diagram with realistic diagram code."""
        # Arrange
        with (
            patch("draw_diagram.Diagram") as mock_diagram_class,
            patch("builtins.exec") as mock_exec,
        ):
            mock_diagram_class.return_value.__enter__ = MagicMock()
            mock_diagram_class.return_value.__exit__ = MagicMock()

            realistic_code = """
from diagrams.aws.compute import EC2
from diagrams.aws.network import ELB

lb = ELB("Load Balancer")
web1 = EC2("Web Server 1")
web2 = EC2("Web Server 2")
lb >> [web1, web2]
"""

            # Act
            draw_diagram(
                title="AWS Architecture",
                code=realistic_code,
                filename="aws_diagram",
                direction="TB",
            )

            # Assert
            mock_exec.assert_called_once()
            # Check that the code was passed to exec
            call_args = mock_exec.call_args[0]
            assert realistic_code in call_args

    def test_draw_diagram_error_handling(self):
        """Test that draw_diagram handles code execution errors."""
        # Arrange
        with patch("draw_diagram.Diagram") as mock_diagram_class:
            mock_diagram_class.return_value.__enter__ = MagicMock()
            # __exit__ must return None/False to not suppress exceptions
            mock_diagram_class.return_value.__exit__ = MagicMock(return_value=None)

            # Code that will raise a NameError when exec'd (trying to use undefined variable)
            invalid_code = "x = undefined_variable_that_does_not_exist + 1"

            # Act & Assert
            with pytest.raises(NameError):
                draw_diagram(
                    title="Test",
                    code=invalid_code,
                    filename="test",
                )
