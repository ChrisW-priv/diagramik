"""DSPy signature for the Python diagrams generator."""

import dspy


class PythonDiagramsSignature(dspy.Signature):
    """Generate Python code for cloud architecture diagrams using the diagrams library.

    The generated code must follow these rules:
    - NO imports (they are handled externally)
    - NO with statement for Diagram context manager
    - Use >> operator to connect nodes (e.g., node1 >> node2)
    - Variables must be defined before use
    - All nodes created with diagrams library classes
    """

    user_intent: str = dspy.InputField(
        desc="The user's request describing the cloud architecture to diagram"
    )

    style_guide: str = dspy.InputField(
        desc="Style guide and best practices for Python diagrams (library docs, patterns)"
    )

    conversation_context: str = dspy.InputField(
        desc="Previous conversation history, if this is a refinement (may be empty)"
    )

    # Output fields
    reasoning: str = dspy.OutputField(
        desc=(
            "Step-by-step reasoning about the architecture: "
            "1) What components are needed? "
            "2) How should they be organized (clusters, layers)? "
            "3) What connections represent the data/control flow? "
            "4) What cloud provider icons are most appropriate?"
        )
    )

    diagram_title: str = dspy.OutputField(
        desc="Clear, descriptive title for the diagram (e.g., 'Three-Tier Web Application Architecture')"
    )

    python_code: str = dspy.OutputField(
        desc=(
            "Python code to generate the diagram. "
            "CRITICAL RULES: "
            "- NO import statements "
            "- NO 'with Diagram(...):' context manager "
            "- Use >> operator for edges (e.g., web >> app >> db) "
            "- Define all variables before using them "
            "- Use proper diagrams library node classes "
            "Example format:\n"
            "# Create nodes\n"
            "web = ELB('Load Balancer')\n"
            "app = ECS('App Server')\n"
            "db = RDS('Database')\n"
            "# Connect them\n"
            "web >> app >> db"
        )
    )

    validation_notes: str = dspy.OutputField(
        desc=(
            "Self-check notes confirming the code follows rules: "
            "- No imports? "
            "- No with statement? "
            "- All nodes connected with >>? "
            "- All variables defined before use?"
        )
    )
