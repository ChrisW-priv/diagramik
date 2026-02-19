"""Mermaid diagram examples for DSPy optimization.

3 examples per diagram type (8 types = 24 total).
"""

import dspy


def get_mermaid_examples() -> list[dspy.Example]:
    """Get 24 mermaid diagram examples (3 per diagram type).

    Returns:
        List of dspy.Example with conversation_history, user_request, expected_mermaid_type.
    """
    examples_data = [
        # --- Flowchart (3) ---
        {
            "user_request": "Create a flowchart for user login with email/password and OAuth paths",
            "expected_mermaid_type": "flowchart",
        },
        {
            "user_request": "Database selection decision tree: relational vs document vs key-value based on requirements",
            "expected_mermaid_type": "flowchart",
        },
        {
            "user_request": "Customer support ticket routing flowchart with escalation paths",
            "expected_mermaid_type": "flowchart",
        },
        # --- Sequence Diagram (3) ---
        {
            "user_request": "Draw a sequence diagram for OAuth2 authorization code flow between browser, auth server, and resource server",
            "expected_mermaid_type": "sequenceDiagram",
        },
        {
            "user_request": "Sequence diagram showing form submission: browser sends to API, API queries DB, returns response",
            "expected_mermaid_type": "sequenceDiagram",
        },
        {
            "user_request": "Sequence diagram for webhook delivery with retries and acknowledgment between sender and receiver",
            "expected_mermaid_type": "sequenceDiagram",
        },
        # --- State Diagram (3) ---
        {
            "user_request": "State diagram for e-commerce order lifecycle: created, paid, shipped, delivered, cancelled",
            "expected_mermaid_type": "stateDiagram-v2",
        },
        {
            "user_request": "Traffic light state machine showing transitions between green, yellow, and red",
            "expected_mermaid_type": "stateDiagram-v2",
        },
        {
            "user_request": "State diagram for video upload processing: uploading, processing, transcoding, ready, failed",
            "expected_mermaid_type": "stateDiagram-v2",
        },
        # --- ER Diagram (3) ---
        {
            "user_request": "ER diagram for a blog system with users, posts, comments, and tags",
            "expected_mermaid_type": "erDiagram",
        },
        {
            "user_request": "Entity relationship diagram for e-commerce: customers, orders, products, and categories",
            "expected_mermaid_type": "erDiagram",
        },
        {
            "user_request": "ER diagram for project management: users, projects, tasks, and labels",
            "expected_mermaid_type": "erDiagram",
        },
        # --- Class Diagram (3) ---
        {
            "user_request": "Class diagram for e-commerce domain with User, Order, and Product classes",
            "expected_mermaid_type": "classDiagram",
        },
        {
            "user_request": "Class diagram for payment processing: PaymentProcessor, CreditCard, and BankTransfer",
            "expected_mermaid_type": "classDiagram",
        },
        {
            "user_request": "Class hierarchy diagram for animals: Animal base class with Mammal, Bird, and Fish subclasses",
            "expected_mermaid_type": "classDiagram",
        },
        # --- Gantt Chart (3) ---
        {
            "user_request": "Gantt chart for a 3-phase project: design phase, development phase, testing phase",
            "expected_mermaid_type": "gantt",
        },
        {
            "user_request": "Product launch timeline gantt chart: research, design, build, and launch phases",
            "expected_mermaid_type": "gantt",
        },
        {
            "user_request": "Sprint planning gantt chart for a 2-week sprint with multiple tasks",
            "expected_mermaid_type": "gantt",
        },
        # --- Pie Chart (3) ---
        {
            "user_request": "Pie chart showing programming language popularity: Python, JavaScript, Java, C++, others",
            "expected_mermaid_type": "pie",
        },
        {
            "user_request": "Create a pie chart showing budget allocation by department: Engineering, Marketing, Sales, Operations",
            "expected_mermaid_type": "pie",
        },
        {
            "user_request": "Browser market share pie chart: Chrome, Firefox, Safari, Edge, others",
            "expected_mermaid_type": "pie",
        },
        # --- Git Graph (3) ---
        {
            "user_request": "Git graph showing feature branch workflow with main, develop, and feature branches",
            "expected_mermaid_type": "gitGraph",
        },
        {
            "user_request": "Git graph for release branching strategy: main, release, and hotfix branches",
            "expected_mermaid_type": "gitGraph",
        },
        {
            "user_request": "Git graph showing trunk-based development with short-lived feature branches",
            "expected_mermaid_type": "gitGraph",
        },
    ]

    examples = []
    for data in examples_data:
        examples.append(
            dspy.Example(
                conversation_history="",
                user_request=data["user_request"],
                expected_mermaid_type=data["expected_mermaid_type"],
            ).with_inputs("conversation_history", "user_request")
        )

    return examples
