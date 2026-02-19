"""Format validation metrics for DSPy optimization.

Validates that generated code is syntactically correct:
- Technical diagrams: valid Python (ast.parse) + valid node names
- Mermaid diagrams: valid prefix + structural checks
"""

import ast
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .node_validation import get_valid_node_names

logger = logging.getLogger(__name__)

# Names that appear as calls in diagram code but are NOT node constructors
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

# Valid mermaid diagram type prefixes
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


def _extract_code_from_trajectory(prediction) -> str | None:
    """Extract the code argument from the tool call in a ReAct prediction trajectory.

    Looks for tool_args entries in the trajectory that contain a 'code' field.
    """
    trajectory = getattr(prediction, "trajectory", None)
    if not trajectory:
        return None

    # Look through trajectory for tool args containing code
    for key, value in trajectory.items():
        if not isinstance(key, str):
            continue
        # DSPy ReAct stores tool arguments as tool_args_N
        if key.startswith("tool_args_"):
            if isinstance(value, dict) and "code" in value:
                return value["code"]
            # Sometimes the value is a string representation
            if isinstance(value, str) and "code" in value:
                try:
                    import json

                    parsed = json.loads(value)
                    if "code" in parsed:
                        return parsed["code"]
                except (json.JSONDecodeError, TypeError):
                    pass

    # Fallback: check prediction outputs directly
    code = getattr(prediction, "diagram_code", None)
    if code:
        return code

    return None


def technical_format_metric(example, prediction, trace=None) -> float:
    """Validate technical diagram code format.

    1. Extract code from prediction trajectory
    2. ast.parse to verify syntactic validity
    3. Walk AST to extract constructor calls
    4. Check each constructor against valid node names

    Args:
        example: dspy.Example (unused for format check).
        prediction: ReAct prediction with trajectory.
        trace: Optional trace (unused).

    Returns:
        1.0 if code parses AND all constructors valid, 0.0 otherwise.
    """
    code = _extract_code_from_trajectory(prediction)
    if not code:
        return 0.0

    # Step 1: Parse with ast
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return 0.0

    # Step 2: Extract constructor calls and validate node names
    valid_names = get_valid_node_names()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            call_name = node.func.id
            if call_name in _NON_NODE_CALL_NAMES:
                continue
            if call_name not in valid_names:
                return 0.0

    return 1.0


def mermaid_format_metric(example, prediction, trace=None) -> float:
    """Validate mermaid diagram code format.

    1. Check code starts with valid prefix
    2. Structural validation (balanced brackets, arrow syntax)
    3. Optional: mmdc CLI validation if available

    Args:
        example: dspy.Example (unused for format check).
        prediction: ReAct prediction with trajectory.
        trace: Optional trace (unused).

    Returns:
        1.0 if valid, 0.0 otherwise.
    """
    code = _extract_code_from_trajectory(prediction)
    if not code:
        return 0.0

    code_stripped = code.strip()

    # Step 1: Check valid prefix
    if not any(code_stripped.startswith(prefix) for prefix in _MERMAID_PREFIXES):
        return 0.0

    # Step 2: Structural checks
    if not _check_balanced(code_stripped):
        return 0.0

    # Check subgraph blocks are closed
    subgraph_count = len(re.findall(r"\bsubgraph\b", code_stripped))
    end_count = len(re.findall(r"\bend\b", code_stripped))
    if subgraph_count > end_count:
        return 0.0

    # Step 3: Optional mmdc validation
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
                    return 0.0
        except (subprocess.TimeoutExpired, OSError):
            pass  # Skip mmdc check on error

    return 1.0


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
