"""Router classification examples for DSPy optimization."""

import dspy


def get_router_examples() -> list[dspy.Example]:
    """Get 30 router classification examples.

    Returns:
        List of dspy.Example with conversation_history, user_request, expected_route.
    """
    examples = []

    # --- draw_technical_diagram (12) ---
    technical_requests = [
        "Create a 3-tier web application on GCP with CloudRun, PostgreSQL, and GCS",
        "Show a GCP infrastructure with Cloud Run, PubSub, and BigQuery",
        "Design a monitoring stack with Prometheus, Grafana, and Sentry",
        "Draw a Kubernetes deployment with Nginx ingress and Redis cache",
        "CI/CD pipeline architecture using Jenkins, Docker, and Terraform",
        "Data pipeline with Kafka, Spark, and PostgreSQL",
        "System diagram showing Redis cache in front of a Django server",
        "Microservices architecture with Docker containers and RabbitMQ",
        "Show the cloud infrastructure for our ML training platform",
        "Create a network diagram with load balancer, web servers, and database cluster",
        "Architecture diagram for a real-time analytics platform",
        "Design a containerized deployment with Docker and Kubernetes",
    ]
    for req in technical_requests:
        examples.append(
            dspy.Example(
                conversation_history="",
                user_request=req,
                expected_route="draw_technical_diagram",
            ).with_inputs("conversation_history", "user_request")
        )

    # --- draw_mermaid (12) ---
    mermaid_requests = [
        "Create a flowchart showing the user login process with password reset",
        "Draw a sequence diagram for OAuth2 authorization code flow",
        "Show a state diagram for an e-commerce order lifecycle",
        "Create an ER diagram for a blog system with users, posts, and comments",
        "Make a class diagram for a payment system",
        "Gantt chart for Q1 product roadmap",
        "Decision tree flowchart for customer support ticket routing",
        "Create a process flow for CI/CD from commit to deployment",
        "Show me a sequence diagram of how webhooks are delivered",
        "Draw a state machine for a video upload processing pipeline",
        "Create a pie chart showing budget allocation by department",
        "Make a git graph showing our release branching strategy",
    ]
    for req in mermaid_requests:
        examples.append(
            dspy.Example(
                conversation_history="",
                user_request=req,
                expected_route="draw_mermaid",
            ).with_inputs("conversation_history", "user_request")
        )

    # --- fallback (6) ---
    fallback_requests = [
        "What is the capital of France?",
        "Write me a Python function to sort a list",
        "Explain the theory of relativity",
        "What's the weather like today?",
        "How do I cook pasta?",
        "Tell me a joke about programmers",
    ]
    for req in fallback_requests:
        examples.append(
            dspy.Example(
                conversation_history="",
                user_request=req,
                expected_route="fallback",
            ).with_inputs("conversation_history", "user_request")
        )

    return examples
