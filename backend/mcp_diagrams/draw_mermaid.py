"""
Mermaid diagram tool that encodes Mermaid code into a viewable URL.

Uses mermaid.ink service to render diagrams from base64-encoded code.
"""

import base64
import json
import zlib


def encode_mermaid(code: str) -> str:
    """
    Encode Mermaid diagram code into a format suitable for mermaid.ink URLs.

    The encoding process:
    1. Create a JSON object with the diagram code and config
    2. Encode to UTF-8 bytes
    3. Compress with zlib (pako compatible)
    4. Encode to base64
    5. Make URL-safe

    Args:
        code: Valid Mermaid diagram code

    Returns:
        Base64-encoded string for use in mermaid.ink URLs
    """
    # Create the state object that mermaid.ink expects
    state = {
        "code": code,
        "mermaid": {"theme": "default"},
        "autoSync": True,
        "updateDiagram": True,
    }

    # Convert to JSON string
    json_str = json.dumps(state)

    # Encode to bytes
    json_bytes = json_str.encode("utf-8")

    # Compress with zlib (equivalent to pako.deflate)
    compressed = zlib.compress(json_bytes, level=9)

    # Base64 encode and make URL-safe
    b64_encoded = base64.urlsafe_b64encode(compressed).decode("ascii")

    return b64_encoded


def get_mermaid_url(code: str, output_format: str = "svg") -> str:
    """
    Generate a mermaid.ink URL for the given Mermaid code.

    Args:
        code: Valid Mermaid diagram code
        output_format: Output format - 'svg' (default), 'png', or 'img'

    Returns:
        URL to view/download the rendered diagram
    """
    encoded = encode_mermaid(code)

    # mermaid.ink supports different endpoints
    if output_format == "png":
        return f"https://mermaid.ink/img/pako:{encoded}?type=png"
    elif output_format == "img":
        return f"https://mermaid.ink/img/pako:{encoded}"
    else:  # svg (default)
        return f"https://mermaid.ink/svg/pako:{encoded}"


def draw_mermaid_diagram(code: str, output_format: str = "svg") -> dict:
    """
    Main tool function to create a Mermaid diagram URL.

    Args:
        code: Valid Mermaid diagram code (e.g., "flowchart TD\\n    A-->B")
        output_format: Output format - 'svg' (default), 'png'

    Returns:
        Dictionary containing:
        - url: URL to view the rendered diagram
        - edit_url: URL to edit the diagram on mermaid.live
        - format: The output format used
    """
    # Clean up the code - normalize line endings
    code = code.strip()

    # Generate URLs
    view_url = get_mermaid_url(code, output_format)

    return {
        "url": view_url,
        "format": output_format,
    }


# For testing
if __name__ == "__main__":
    test_code = """flowchart TD
    A[Start] --> B{Decision?}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E"""

    result = draw_mermaid_diagram(test_code)
    print(f"{result['url']}")
