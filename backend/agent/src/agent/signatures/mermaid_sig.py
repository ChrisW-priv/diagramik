"""DSPy signature for the Mermaid diagram generator."""

import dspy


class MermaidSignature(dspy.Signature):
    """Generate Mermaid diagram syntax for flowcharts, sequences, ER diagrams, etc.

    The generated code must be valid Mermaid syntax with proper diagram type declaration.
    """

    user_intent: str = dspy.InputField(desc="The user's request describing the diagram to create")

    style_guide: str = dspy.InputField(
        desc="Mermaid syntax guide and examples for different diagram types"
    )

    conversation_context: str = dspy.InputField(
        desc="Previous conversation history, if this is a refinement (may be empty)"
    )

    # Output fields
    reasoning: str = dspy.OutputField(
        desc=(
            "Step-by-step reasoning about the diagram: "
            "1) What Mermaid diagram type is most appropriate (flowchart, sequence, ER, etc.)? "
            "2) What are the key entities/nodes/steps? "
            "3) What relationships/flows need to be shown? "
            "4) Should it be vertical (TD/TB) or horizontal (LR)?"
        )
    )

    diagram_type: str = dspy.OutputField(
        desc=(
            "The Mermaid diagram type to use: "
            "'flowchart' for process flows, "
            "'sequenceDiagram' for interactions over time, "
            "'erDiagram' for entity relationships, "
            "'stateDiagram' for state machines, "
            "'classDiagram' for class structures, "
            "'gantt' for timelines"
        )
    )

    diagram_title: str = dspy.OutputField(desc="Clear, descriptive title for the diagram")

    mermaid_code: str = dspy.OutputField(
        desc=(
            "Complete Mermaid diagram syntax. "
            "Must start with diagram type declaration (e.g., 'flowchart TD', 'sequenceDiagram'). "
            "Use proper Mermaid syntax for the chosen diagram type. "
            "Example flowchart:\n"
            "flowchart TD\n"
            "    A[Start] --> B{Decision}\n"
            "    B -->|Yes| C[Action 1]\n"
            "    B -->|No| D[Action 2]\n"
            "    C --> E[End]\n"
            "    D --> E"
        )
    )

    validation_notes: str = dspy.OutputField(
        desc=(
            "Self-check notes confirming valid Mermaid syntax: "
            "- Diagram type declared at the top? "
            "- Proper syntax for the chosen type? "
            "- All nodes/entities defined? "
            "- Connections use correct arrow syntax?"
        )
    )
