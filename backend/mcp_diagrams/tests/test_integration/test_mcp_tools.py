"""Integration tests for MCP tools."""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError


pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def setup_env_vars(monkeypatch):
    """Automatically set up environment variables for all integration tests."""
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project")


class TestDrawTechnicalDiagramTool:
    """Integration tests for draw_technical_diagram MCP tool."""

    @pytest.mark.asyncio
    async def test_draw_technical_diagram_returns_draw_result(
        self, mock_gcs_client, sample_diagram_code
    ):
        """Test that draw_technical_diagram returns a DrawResult."""
        # Arrange
        from server import draw_technical_diagram, TechnicalDiagramArgs

        args = TechnicalDiagramArgs(
            title="Test Architecture",
            code=sample_diagram_code,
            custom_graph_args=None,
            custom_node_args=None,
            custom_edge_args=None,
        )

        with (
            patch("server.draw_diagram_tool"),
            patch("server.move_file_to_gcs") as mock_move,
        ):
            # Mock the file creation
            mock_blob = MagicMock()
            mock_blob.bucket.name = "test-bucket"
            mock_blob.name = "test-diagram.png"
            mock_move.return_value = mock_blob

            # Act
            result = await draw_technical_diagram(args)

            # Assert
            assert result.title == "Test Architecture"
            assert result.uri.startswith("gs://")
            assert "test-bucket" in result.uri

    @pytest.mark.asyncio
    async def test_draw_technical_diagram_calls_draw_function(
        self, mock_gcs_client, sample_diagram_code
    ):
        """Test that draw_technical_diagram calls the diagram drawing function."""
        # Arrange
        from server import draw_technical_diagram, TechnicalDiagramArgs

        args = TechnicalDiagramArgs(
            title="Test Diagram",
            code=sample_diagram_code,
            custom_graph_args={"rankdir": "TB"},
            custom_node_args={"shape": "box"},
            custom_edge_args={"color": "blue"},
        )

        with (
            patch("server.draw_diagram_tool") as mock_draw,
            patch("server.move_file_to_gcs") as mock_move,
        ):
            mock_blob = MagicMock()
            mock_blob.bucket.name = "test-bucket"
            mock_blob.name = "diagram.png"
            mock_move.return_value = mock_blob

            # Act
            await draw_technical_diagram(args)

            # Assert
            mock_draw.assert_called_once()
            call_kwargs = mock_draw.call_args[1]
            assert call_kwargs["title"] == "Test Diagram"
            assert call_kwargs["code"] == sample_diagram_code
            assert call_kwargs["custom_graph_args"] == {"rankdir": "TB"}

    @pytest.mark.asyncio
    async def test_draw_technical_diagram_uploads_to_gcs(
        self, mock_gcs_client, sample_diagram_code
    ):
        """Test that draw_technical_diagram uploads file to GCS."""
        # Arrange
        from server import draw_technical_diagram, TechnicalDiagramArgs

        args = TechnicalDiagramArgs(
            title="Cloud Architecture",
            code=sample_diagram_code,
            custom_graph_args=None,
            custom_node_args=None,
            custom_edge_args=None,
        )

        with (
            patch("server.draw_diagram_tool"),
            patch("server.move_file_to_gcs") as mock_move,
        ):
            mock_blob = MagicMock()
            mock_blob.bucket.name = "diagrams-bucket"
            mock_blob.name = "cloud-arch.png"
            mock_move.return_value = mock_blob

            # Act
            await draw_technical_diagram(args)

            # Assert
            mock_move.assert_called_once()
            # Verify filename ends with .png
            call_args = mock_move.call_args
            assert call_args[0][0].endswith(".png")
            assert call_args[1]["bucket_name"] == "test-bucket"

    @pytest.mark.asyncio
    async def test_draw_technical_diagram_generates_unique_filenames(
        self, mock_gcs_client, sample_diagram_code
    ):
        """Test that each diagram gets a unique filename."""
        # Arrange
        from server import draw_technical_diagram, TechnicalDiagramArgs

        args = TechnicalDiagramArgs(
            title="Diagram",
            code=sample_diagram_code,
            custom_graph_args=None,
            custom_node_args=None,
            custom_edge_args=None,
        )

        filenames = []

        with (
            patch("server.draw_diagram_tool"),
            patch("server.move_file_to_gcs") as mock_move,
        ):
            mock_blob = MagicMock()
            mock_blob.bucket.name = "test-bucket"
            mock_blob.name = "diagram.png"
            mock_move.return_value = mock_blob

            # Act - create multiple diagrams
            for _ in range(3):
                await draw_technical_diagram(args)
                filename = mock_move.call_args[0][0]
                filenames.append(filename)

            # Assert - all filenames should be unique
            assert len(filenames) == 3
            assert len(set(filenames)) == 3  # All unique

    @pytest.mark.asyncio
    async def test_draw_technical_diagram_validation_error(self):
        """Test that invalid arguments raise validation error."""
        # Arrange
        from server import TechnicalDiagramArgs

        # Act & Assert
        with pytest.raises(ValidationError):
            TechnicalDiagramArgs(
                # Missing required fields
                code="test code"
            )

    @pytest.mark.asyncio
    async def test_draw_technical_diagram_with_all_custom_args(
        self, mock_gcs_client, sample_diagram_code
    ):
        """Test draw_technical_diagram with all custom arguments."""
        # Arrange
        from server import draw_technical_diagram, TechnicalDiagramArgs

        args = TechnicalDiagramArgs(
            title="Complete Test",
            code=sample_diagram_code,
            custom_graph_args={"bgcolor": "transparent"},
            custom_node_args={"fontsize": "12"},
            custom_edge_args={"penwidth": "2"},
        )

        with (
            patch("server.draw_diagram_tool") as mock_draw,
            patch("server.move_file_to_gcs") as mock_move,
        ):
            mock_blob = MagicMock()
            mock_blob.bucket.name = "test-bucket"
            mock_blob.name = "complete.png"
            mock_move.return_value = mock_blob

            # Act
            result = await draw_technical_diagram(args)

            # Assert
            assert result.title == "Complete Test"
            mock_draw.assert_called_once()


class TestDrawMermaidTool:
    """Integration tests for draw_mermaid MCP tool."""

    @pytest.mark.asyncio
    async def test_draw_mermaid_returns_draw_result(self, sample_mermaid_code):
        """Test that draw_mermaid returns a DrawResult."""
        # Arrange
        from server import draw_mermaid, MermaidArgs

        args = MermaidArgs(
            code=sample_mermaid_code,
            title="Test Flowchart",
            output_format="svg",
        )

        # Act
        result = await draw_mermaid(args)

        # Assert
        assert result.title == "Test Flowchart"
        assert result.uri is not None
        assert "mermaid.ink" in result.uri

    @pytest.mark.asyncio
    async def test_draw_mermaid_svg_format(self, sample_mermaid_code):
        """Test draw_mermaid with SVG format."""
        # Arrange
        from server import draw_mermaid, MermaidArgs

        args = MermaidArgs(
            code=sample_mermaid_code,
            title="SVG Diagram",
            output_format="svg",
        )

        # Act
        result = await draw_mermaid(args)

        # Assert
        assert "svg" in result.uri

    @pytest.mark.asyncio
    async def test_draw_mermaid_png_format(self, sample_mermaid_code):
        """Test draw_mermaid with PNG format."""
        # Arrange
        from server import draw_mermaid, MermaidArgs

        args = MermaidArgs(
            code=sample_mermaid_code,
            title="PNG Diagram",
            output_format="png",
        )

        # Act
        result = await draw_mermaid(args)

        # Assert
        assert "png" in result.uri

    @pytest.mark.asyncio
    async def test_draw_mermaid_default_format(self, sample_mermaid_code):
        """Test draw_mermaid with default format."""
        # Arrange
        from server import draw_mermaid, MermaidArgs

        args = MermaidArgs(
            code=sample_mermaid_code,
            title="Default Format",
        )

        # Act
        result = await draw_mermaid(args)

        # Assert
        assert "svg" in result.uri

    @pytest.mark.asyncio
    async def test_draw_mermaid_validation_error(self):
        """Test that invalid arguments raise validation error."""
        # Arrange
        from server import MermaidArgs

        # Act & Assert
        with pytest.raises(ValidationError):
            MermaidArgs(
                # Missing required fields
                output_format="svg"
            )

    @pytest.mark.asyncio
    async def test_draw_mermaid_with_sequence_diagram(self):
        """Test draw_mermaid with sequence diagram code."""
        # Arrange
        from server import draw_mermaid, MermaidArgs

        sequence_code = """sequenceDiagram
    Alice->>Bob: Hello Bob!
    Bob-->>Alice: Hi Alice!"""

        args = MermaidArgs(
            code=sequence_code,
            title="Sequence Diagram",
            output_format="svg",
        )

        # Act
        result = await draw_mermaid(args)

        # Assert
        assert result.title == "Sequence Diagram"
        assert "mermaid.ink" in result.uri

    @pytest.mark.asyncio
    async def test_draw_mermaid_url_format(self, sample_mermaid_code):
        """Test that draw_mermaid returns properly formatted URL."""
        # Arrange
        from server import draw_mermaid, MermaidArgs

        args = MermaidArgs(
            code=sample_mermaid_code,
            title="URL Test",
            output_format="svg",
        )

        # Act
        result = await draw_mermaid(args)

        # Assert
        assert result.uri.startswith("https://")
        assert "pako:" in result.uri


class TestMCPServerConfiguration:
    """Tests for MCP server configuration."""

    def test_mcp_server_requires_bucket_name(self, monkeypatch):
        """Test that MCP server raises error without BUCKET_NAME."""
        # Arrange
        monkeypatch.delenv("BUCKET_NAME", raising=False)

        # Act & Assert
        with pytest.raises(EnvironmentError, match="BUCKET_NAME"):
            # This will trigger the import and environment check
            import importlib
            import server

            importlib.reload(server)

    def test_mcp_server_uses_env_vars(self, monkeypatch):
        """Test that MCP server uses environment variables."""
        # Arrange
        monkeypatch.setenv("BUCKET_NAME", "env-test-bucket")
        monkeypatch.setenv("GCP_PROJECT_ID", "env-test-project")

        # Act
        import importlib
        import server

        importlib.reload(server)

        # Assert
        assert server.BUCKET_NAME == "env-test-bucket"
        assert server.GCP_PROJECT_ID == "env-test-project"


class TestMCPToolsEndToEnd:
    """End-to-end tests for MCP tools (still with mocked external services)."""

    @pytest.mark.asyncio
    async def test_complete_technical_diagram_workflow(
        self, mock_gcs_client, sample_diagram_code
    ):
        """Test complete workflow for technical diagram creation."""
        # Arrange
        from server import draw_technical_diagram, TechnicalDiagramArgs

        args = TechnicalDiagramArgs(
            title="Complete Workflow Test",
            code=sample_diagram_code,
            custom_graph_args={"splines": "ortho"},
            custom_node_args={"style": "rounded"},
            custom_edge_args={"arrowsize": "0.5"},
        )

        with (
            patch("server.draw_diagram_tool") as mock_draw,
            patch("server.move_file_to_gcs") as mock_move,
            patch("os.remove"),
        ):
            # Mock successful upload
            mock_blob = MagicMock()
            mock_blob.bucket.name = "production-bucket"
            mock_blob.name = "architecture-v1.png"
            mock_move.return_value = mock_blob

            # Act
            result = await draw_technical_diagram(args)

            # Assert - verify complete flow
            # 1. Draw function was called
            mock_draw.assert_called_once()

            # 2. File was uploaded to GCS
            mock_move.assert_called_once()

            # 3. Result contains proper GCS URI
            assert result.uri == "gs://production-bucket/architecture-v1.png"
            assert result.title == "Complete Workflow Test"

    @pytest.mark.asyncio
    async def test_complete_mermaid_workflow(self, sample_mermaid_code):
        """Test complete workflow for Mermaid diagram creation."""
        # Arrange
        from server import draw_mermaid, MermaidArgs

        args = MermaidArgs(
            code=sample_mermaid_code,
            title="Complete Mermaid Test",
            output_format="png",
        )

        # Act
        result = await draw_mermaid(args)

        # Assert - verify complete flow
        # 1. URL was generated
        assert result.uri is not None
        assert isinstance(result.uri, str)

        # 2. URL points to mermaid.ink
        assert "mermaid.ink" in result.uri

        # 3. Title is preserved
        assert result.title == "Complete Mermaid Test"

        # 4. Format is correct
        assert "png" in result.uri
