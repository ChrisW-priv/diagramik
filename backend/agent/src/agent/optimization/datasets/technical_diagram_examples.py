"""Technical diagram examples for DSPy optimization.

All examples use ONLY node names available in available_nodes.py.
No AWS nodes (EC2, Lambda, S3, RDS) -- only GCP, on-prem, generic,
programming, SaaS, and Elastic nodes.
"""

import dspy


def get_technical_diagram_examples() -> list[dspy.Example]:
    """Get 15 technical diagram examples.

    Returns:
        List of dspy.Example with conversation_history, user_request, expected_node_names.
    """
    examples_data = [
        # 1. Simple web app
        {
            "user_request": "Create a simple web application diagram with a user connecting to Nginx, then Django, then PostgreSQL",
            "expected_node_names": {"User", "Nginx", "Django", "PostgreSQL"},
        },
        # 2. GCP CloudRun API
        {
            "user_request": "Show a GCP CloudRun API service that reads from BigQuery and stores files in GCS",
            "expected_node_names": {"CloudRun", "BigQuery", "GCS"},
        },
        # 3. GCP VPC with clusters
        {
            "user_request": "Design a GCP VPC containing CloudRun, GCS, and PubSub services in a cluster",
            "expected_node_names": {"CloudRun", "GCS", "PubSub"},
        },
        # 4. Data pipeline
        {
            "user_request": "Data pipeline: Mobile app sends data to Kafka, processed by Spark, stored in PostgreSQL with Redis cache",
            "expected_node_names": {"Mobile", "Kafka", "Spark", "PostgreSQL", "Redis"},
        },
        # 5. Monitoring stack
        {
            "user_request": "Monitoring setup: Server sends metrics to Prometheus and Grafana, with Sentry for error tracking",
            "expected_node_names": {"Server", "Prometheus", "Grafana", "Sentry"},
        },
        # 6. CI/CD pipeline
        {
            "user_request": "CI/CD pipeline: Github triggers GithubActions, builds Docker image, scans with Trivy, deploys to GKE via Terraform",
            "expected_node_names": {
                "Github",
                "GithubActions",
                "Docker",
                "Trivy",
                "GKE",
                "Terraform",
            },
        },
        # 7. Cross-team data sharing
        {
            "user_request": "CloudRun job that processes data and writes to multiple GCS buckets in different groups",
            "expected_node_names": {"CloudRun", "GCS"},
        },
        # 8. Microservices
        {
            "user_request": "Microservices: Client connects to multiple FastAPI services communicating via RabbitMQ with MongoDB databases",
            "expected_node_names": {"Client", "FastAPI", "RabbitMQ", "MongoDB"},
        },
        # 9. Serverless GCP
        {
            "user_request": "Serverless GCP: APIGateway routes to GcpCloudFunctions which query BigQuery and store results in GCS",
            "expected_node_names": {
                "APIGateway",
                "GcpCloudFunctions",
                "BigQuery",
                "GCS",
            },
        },
        # 10. ML pipeline
        {
            "user_request": "ML pipeline: BigQuery data feeds into VertexAI for training, model served via CloudRun",
            "expected_node_names": {"BigQuery", "VertexAI", "CloudRun"},
        },
        # 11. Kubernetes deployment
        {
            "user_request": "Kubernetes deployment: Users connect through Nginx to Django pods backed by Redis and PostgreSQL",
            "expected_node_names": {"Users", "Nginx", "Django", "Redis", "PostgreSQL"},
        },
        # 12. Event-driven
        {
            "user_request": "Event-driven: GCS file upload triggers PubSub event, processed by GcpCloudFunctions, results in BigQuery",
            "expected_node_names": {"GCS", "PubSub", "GcpCloudFunctions", "BigQuery"},
        },
        # 13. Multi-region
        {
            "user_request": "Multi-region setup: CloudRun services in two clusters behind GcpCDN, shared PostgreSQL database",
            "expected_node_names": {"CloudRun", "GcpCDN", "PostgreSQL"},
        },
        # 14. Message broker
        {
            "user_request": "Message broker pattern: Client sends to Django, queued via Celery with Redis broker, results in MongoDB",
            "expected_node_names": {"Client", "Django", "Celery", "Redis", "MongoDB"},
        },
        # 15. GitOps
        {
            "user_request": "GitOps: Github repo triggers ArgoCD which deploys to GKE, monitored by GcpMonitoring and GcpLogging",
            "expected_node_names": {
                "Github",
                "ArgoCD",
                "GKE",
                "GcpMonitoring",
                "GcpLogging",
            },
        },
    ]

    examples = []
    for data in examples_data:
        examples.append(
            dspy.Example(
                conversation_history="",
                user_request=data["user_request"],
                expected_node_names=data["expected_node_names"],
            ).with_inputs("conversation_history", "user_request")
        )

    return examples
