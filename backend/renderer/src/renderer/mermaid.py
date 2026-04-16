"""
Mermaid diagram tool that renders Mermaid code to a local file using mmdc.

Uses the Mermaid CLI (mmdc) to both validate syntax and render diagrams.
The caller is responsible for uploading the output file to GCS.
"""

import subprocess
import tempfile
import uuid
from pathlib import Path


def draw_mermaid_diagram(code: str, output_format: str = "svg") -> dict:
    """
    Render a Mermaid diagram to a local file using mmdc.

    Args:
        code: Valid Mermaid diagram code (e.g., "flowchart TD\\n    A-->B")
        output_format: Output format - 'svg' (default) or 'png'

    Returns:
        Dictionary containing one of:
        - On success: {"path": "/tmp/<uuid>.<ext>", "format": output_format}
        - On failure: {"error": "<mmdc stderr>", "format": output_format}
    """
    code = code.strip()
    ext = "png" if output_format == "png" else "svg"
    out_path = Path(tempfile.gettempdir()) / f"{uuid.uuid4().hex}.{ext}"

    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as f:
        in_path = Path(f.name)
        f.write(code)

    try:
        cmd = ["mmdc", "-i", str(in_path), "-o", str(out_path)]
        puppeteer_config = Path("/app/puppeteer-config.json")
        if puppeteer_config.exists():
            cmd += ["-p", str(puppeteer_config)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode("utf-8", errors="replace").strip()
            out_path.unlink(missing_ok=True)
            return {"error": stderr[:300], "format": output_format}
    finally:
        in_path.unlink(missing_ok=True)

    return {"path": str(out_path), "format": output_format}
