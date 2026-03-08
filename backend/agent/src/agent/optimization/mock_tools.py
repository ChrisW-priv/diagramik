"""Mock tool callables for isolated DSPy optimization testing.

These simulate MCP tools without requiring a running server.
"""

import ast
import json
import logging
import re
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from .metrics.node_validation import get_valid_node_names

logger = logging.getLogger(__name__)

# Names that appear as calls but are NOT node constructors
_NON_NODE_CALL_NAMES = {
    "Edge",
    "Cluster",
    "Diagram",
    "range",
    "zip",
    "print",
    "len",
    "str",
    "int",
    "list",
    "dict",
    "set",
    "enumerate",
    "sorted",
    "reversed",
    "map",
    "filter",
}

# Valid mermaid prefixes
_MERMAID_PREFIXES = (
    "flowchart",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram-v2",
    "stateDiagram",
    "erDiagram",
    "gantt",
    "pie",
    "gitGraph",
)


def create_mock_draw_technical_diagram() -> callable:
    """Create a mock draw_technical_diagram tool callable.

    Validates:
    1. title and code fields exist
    2. code is syntactically valid Python (ast.parse)
    3. Constructor calls use valid node names from available_nodes.py

    Returns:
        Callable that accepts title and code kwargs, returns JSON string.
    """

    def draw_technical_diagram(*, title: str = "", code: str = "") -> str:
        """Draw a technical architecture diagram using Python diagrams library.

        Args:
            title: The diagram title.
            code: Python code using the diagrams library to generate the diagram.

        Returns:
            JSON string with uri and title on success, or error message on failure.
        """
        errors = []

        if not title:
            errors.append("Missing required field: title")
        if not code:
            errors.append("Missing required field: code")

        if errors:
            return json.dumps({"error": "; ".join(errors)})

        # Validate Python syntax
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return json.dumps(
                {"error": f"Invalid Python syntax: {e.msg} (line {e.lineno})"}
            )

        # Validate node names
        valid_names = get_valid_node_names()
        invalid_nodes = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                call_name = node.func.id
                if call_name in _NON_NODE_CALL_NAMES:
                    continue
                if call_name not in valid_names:
                    invalid_nodes.append(call_name)

        if invalid_nodes:
            return json.dumps(
                {
                    "error": f"Invalid node names: {', '.join(invalid_nodes)}. "
                    f"These are not available in available_nodes.py."
                }
            )

        # Success
        mock_uri = f"gs://mock-bucket/diagrams/{uuid.uuid4().hex[:12]}.png"
        return json.dumps({"uri": mock_uri, "title": title})

    return draw_technical_diagram


def create_mock_draw_mermaid() -> callable:
    """Create a mock draw_mermaid tool callable.

    Validates:
    1. title and code fields exist
    2. Code starts with valid mermaid prefix
    3. Basic structural validation (balanced brackets/braces)
    4. Optional: mmdc CLI validation if available

    Returns:
        Callable that accepts title and code kwargs, returns JSON string.
    """

    def draw_mermaid(*, title: str = "", code: str = "") -> str:
        """Draw a diagram using Mermaid syntax.

        Args:
            title: The diagram title.
            code: Mermaid diagram code.

        Returns:
            JSON string with uri and title on success, or error message on failure.
        """
        errors = []

        if not title:
            errors.append("Missing required field: title")
        if not code:
            errors.append("Missing required field: code")

        if errors:
            return json.dumps({"error": "; ".join(errors)})

        code_stripped = code.strip()

        # Check valid prefix
        if not any(code_stripped.startswith(prefix) for prefix in _MERMAID_PREFIXES):
            return json.dumps(
                {
                    "error": f"Mermaid code must start with a valid diagram type: "
                    f"{', '.join(_MERMAID_PREFIXES)}"
                }
            )

        # Balanced brackets/braces check
        if not _check_balanced(code_stripped):
            return json.dumps(
                {"error": "Unbalanced brackets, parentheses, or braces in mermaid code"}
            )

        # Check subgraph blocks
        subgraph_count = len(re.findall(r"\bsubgraph\b", code_stripped))
        end_count = len(re.findall(r"\bend\b", code_stripped))
        if subgraph_count > end_count:
            return json.dumps(
                {
                    "error": f"Unclosed subgraph blocks: {subgraph_count} subgraphs "
                    f"but only {end_count} end statements"
                }
            )

        # Optional mmdc validation
        if shutil.which("mmdc"):
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".mmd", delete=False
                ) as f:
                    f.write(code_stripped)
                    f.flush()
                    result = subprocess.run(
                        ["mmdc", "-i", f.name, "-o", "/dev/null"],
                        capture_output=True,
                        timeout=10,
                    )
                    Path(f.name).unlink(missing_ok=True)
                    if result.returncode != 0:
                        stderr = result.stderr.decode("utf-8", errors="replace")
                        return json.dumps(
                            {
                                "error": f"Mermaid syntax validation failed: {stderr[:200]}"
                            }
                        )
            except (subprocess.TimeoutExpired, OSError):
                pass  # Skip mmdc check on error

        # Success
        mock_uri = f"https://mermaid.ink/img/{uuid.uuid4().hex[:12]}"
        return json.dumps({"uri": mock_uri, "title": title})

    return draw_mermaid


def _check_balanced(code: str) -> bool:
    """Check that brackets, parens, and braces are balanced."""
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    openers = set(pairs.values())
    closers = set(pairs.keys())

    for char in code:
        if char in openers:
            stack.append(char)
        elif char in closers:
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()

    return len(stack) == 0
