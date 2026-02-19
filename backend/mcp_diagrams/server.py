import os
from pathlib import Path

from uuid_utils import uuid7
from mcp.server.fastmcp import FastMCP
from draw_diagram import draw_diagram as draw_diagram_tool
from draw_mermaid import draw_mermaid_diagram
from move_file_to_gcs import move_file_to_gcs
from pydantic import BaseModel, Field


_USER_MANUAL_DIR = Path(__file__).parent / "data" / "user_manual"
_PYTHON_DIAGRAMS_GUIDE = (_USER_MANUAL_DIR / "python_diagrams.md").read_text()
_MERMAID_GUIDE = (_USER_MANUAL_DIR / "mermaid.md").read_text()


# Environment configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "playground-449613")
BUCKET_NAME = os.getenv("BUCKET_NAME")
if not BUCKET_NAME:
    raise EnvironmentError("BUCKET_NAME environment variable is not set!")


mcp = FastMCP(
    name="Diagram generator",
    host="0.0.0.0",
    port=8080,
)


class DrawResult(BaseModel):
    """
    Return URI of the diagram
    """

    uri: str = Field(..., description="URI to the result diagram")
    title: str = Field(..., description="Chosen Title for the diagram")


class TechnicalDiagramArgs(BaseModel):
    """
    Arguments passed to draw_technical_diagram tool
    """

    title: str = Field(
        ...,
        description="Title of the new diagram displayed to the reader. Make it clear what the diagram is about",
    )
    code: str = Field(..., description="Code used to generate the Diagram")
    custom_graph_args: dict | None = Field(
        ..., description="Custom arguments to modify the rendering of main graph"
    )
    custom_node_args: dict | None = Field(
        ..., description="Custom arguments to modify the rendering of each node"
    )
    custom_edge_args: dict | None = Field(
        ..., description="Custom arguments to modify the rendering of each edge"
    )


@mcp.tool(description=_PYTHON_DIAGRAMS_GUIDE)
async def draw_technical_diagram(args: TechnicalDiagramArgs) -> DrawResult:
    filename = str(uuid7())
    kwargs = args.model_dump()

    # Should save the filename under "{filename}.png" path
    draw_diagram_tool(filename=filename, **kwargs)
    # Saves the file to GCS and removes it from local FS
    filename += ".png"
    new_blob = move_file_to_gcs(
        filename, bucket_name=BUCKET_NAME, project_id=GCP_PROJECT_ID
    )

    gsutil_uri = f"gs://{new_blob.bucket.name}/{new_blob.name}"
    return DrawResult(uri=gsutil_uri, title=args.title)


class MermaidArgs(BaseModel):
    """
    Arguments passed to mermaid diagram tool
    """

    code: str = Field(
        ..., description="Valid Mermaid diagram code (e.g., 'flowchart TD\\n    A-->B')"
    )
    title: str = Field(..., description="Chosen Title for the diagram")
    output_format: str = Field(
        default="svg", description="Output format: 'svg' (default) or 'png'"
    )


@mcp.tool(description=_MERMAID_GUIDE)
async def draw_mermaid(args: MermaidArgs) -> DrawResult:
    result = draw_mermaid_diagram(args.code, args.output_format)
    return DrawResult(uri=result.get("url"), title=args.title)


def main():
    mcp.run("streamable-http")


if __name__ == "__main__":
    main()
