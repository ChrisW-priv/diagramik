"""Parse available_nodes.py to extract valid diagram node class names."""

import ast
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to the canonical available_nodes.py
_AVAILABLE_NODES_PATH = (
    Path(__file__).parent.parent.parent.parent.parent.parent
    / "mcp_diagrams"
    / "available_nodes.py"
)

# Hardcoded fallback set in case the file can't be parsed
_FALLBACK_NODE_NAMES: set[str] = {
    # Elastic
    "Alerting",
    "Beats",
    "ElasticSearch",
    "Kibana",
    "LogStash",
    "Cloud",
    "Elastic",
    # Firebase
    "Firebase",
    # Generic
    "Rack",
    "SQL",
    "Mobile",
    "Tablet",
    "VPN",
    "Firewall",
    "Router",
    "Subnet",
    "Switch",
    "IOS",
    "Android",
    "Centos",
    "Debian",
    "Raspbian",
    "RedHat",
    "Ubuntu",
    "Windows",
    "Linux",
    "Datacenter",
    "Office",
    "Storage",
    "XEN",
    "Qemu",
    "Virtualbox",
    "Vmware",
    # GCP
    "BigQuery",
    "PubSub",
    "APIGateway",
    "Endpoints",
    "GCE",
    "GKE",
    "CloudRun",
    "ComputeEngine",
    "GcpCloudFunctions",
    "CloudBuild",
    "CloudShell",
    "ContainerRegistry",
    "GcpCloudScheduler",
    "GcpCloudHttpTasks",
    "GcpCloudBilling",
    "GcpCloudProject",
    "GcpTPU",
    "GcpAIPlatform",
    "GcpMlInferenceAPI",
    "GcpSpeechToText",
    "GcpTextToSpeech",
    "GcpTranslationAPI",
    "VertexAI",
    "GcpVideoIntelligenceAPI",
    "GcpVisionAPI",
    "GcpCDN",
    "GcpDNS",
    "GcpVPC",
    "GcpCloudArmor",
    "GcpFirewallRules",
    "GcpLogging",
    "GcpMonitoring",
    "GcpIAP",
    "GcpKeyManagementService",
    "GcpIAM",
    "GcpResourceManager",
    "GcpSecretManager",
    "GCS",
    "GcpFilestore",
    "GcpPersistentDisk",
    # On-prem
    "Fluentd",
    "Beam",
    "Databricks",
    "Dbt",
    "Hadoop",
    "Hive",
    "PowerBI",
    "Spark",
    "Tableau",
    "CertManager",
    "LetsEncrypt",
    "CircleCI",
    "GithubActions",
    "GitlabCI",
    "Jenkins",
    "Client",
    "User",
    "Users",
    "Nomad",
    "Server",
    "K3S",
    "Containerd",
    "Docker",
    "MSSQL",
    "Cassandra",
    "CockroachDB",
    "Duckdb",
    "MariaDB",
    "MongoDB",
    "Neo4J",
    "Oracle",
    "PostgreSQL",
    "Scylla",
    "ArgoCD",
    "Nextcloud",
    "Ansible",
    "Pulumi",
    "Terraform",
    "Memcached",
    "Redis",
    "Mlflow",
    "Datadog",
    "Grafana",
    "Prometheus",
    "Sentry",
    "Nginx",
    "Traefik",
    "ProxmoxVE",
    "Celery",
    "Kafka",
    "RabbitMQ",
    "Solr",
    "Bitwarden",
    "Trivy",
    "Vault",
    "Jaeger",
    "Tempo",
    "Git",
    "Github",
    "Gitlab",
    "Airflow",
    "Digdag",
    "KubeFlow",
    # Programming
    "Angular",
    "Django",
    "DotNet",
    "FastAPI",
    "Flask",
    "Flutter",
    "GraphQL",
    "Laravel",
    "NextJs",
    "Phoenix",
    "Rails",
    "React",
    "Spring",
    "Svelte",
    "Vue",
    "PHP",
    "Bash",
    "C",
    "Cpp",
    "Csharp",
    "Dart",
    "Elixir",
    "Erlang",
    "Go",
    "Java",
    "JavaScript",
    "Kotlin",
    "Latex",
    "Matlab",
    "Python",
    "R",
    "Ruby",
    "Rust",
    "Scala",
    "Swift",
    "TypeScript",
    "NodeJs",
    # SaaS
    "Dataform",
    "Snowflake",
    "Stitch",
    "N8N",
    "Cloudflare",
    "Fastly",
    "Discord",
    "Messenger",
    "Slack",
    "Teams",
    "Telegram",
    "Auth0",
    "Okta",
    "AmazonPay",
    "Paypal",
    "Stripe",
}

_cached_names: set[str] | None = None


def get_valid_node_names() -> set[str]:
    """Get the set of valid node class names from available_nodes.py.

    Parses the file using AST to extract imported names and aliases.
    Falls back to a hardcoded set if the file can't be found or parsed.

    Returns:
        Set of valid node class name strings.
    """
    global _cached_names
    if _cached_names is not None:
        return _cached_names

    _cached_names = _parse_available_nodes()
    return _cached_names


def _parse_available_nodes() -> set[str]:
    """Parse available_nodes.py using AST to extract all imported names."""
    if not _AVAILABLE_NODES_PATH.exists():
        logger.warning(
            "available_nodes.py not found at %s, using fallback set",
            _AVAILABLE_NODES_PATH,
        )
        return _FALLBACK_NODE_NAMES.copy()

    try:
        source = _AVAILABLE_NODES_PATH.read_text()
        tree = ast.parse(source)
    except (SyntaxError, OSError) as e:
        logger.warning("Failed to parse available_nodes.py: %s, using fallback set", e)
        return _FALLBACK_NODE_NAMES.copy()

    names: set[str] = set()

    for node in ast.walk(tree):
        # Handle: from diagrams.x.y import Foo, Bar
        # Handle: from diagrams.x.y import Foo as Bar
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                # Use the alias (asname) if present, otherwise the original name
                imported_name = alias.asname if alias.asname else alias.name
                names.add(imported_name)

        # Handle: Office = Datacenter (top-level assignments)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)

    if not names:
        logger.warning("No names extracted from available_nodes.py, using fallback set")
        return _FALLBACK_NODE_NAMES.copy()

    logger.debug("Extracted %d valid node names from available_nodes.py", len(names))
    return names
