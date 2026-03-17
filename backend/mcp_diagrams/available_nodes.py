# ruff: noqa

from diagrams.c4 import (
    Person as C4Person,
    System as C4System,
    SystemBoundary as C4SystemBoundary,
    Container as C4Container,
    Database as C4Database,
    Relationship as C4Relationship,
)

from diagrams.aws.general import (
    InternetAlt2,
    OfficeBuilding,
    MobileClient,
)
from diagrams.elastic.elasticsearch import (
    Alerting,
    Beats,
    ElasticSearch,
    Kibana,
    LogStash,
)
from diagrams.elastic.saas import (
    Cloud,
    Elastic,
)
from diagrams.firebase.base import Firebase
from diagrams.generic.compute import Rack
from diagrams.generic.database import SQL
from diagrams.generic.device import (
    Mobile,
    Tablet,
)
from diagrams.generic.network import (
    VPN,
    Firewall,
    Router,
    Subnet,
    Switch,
)
from diagrams.generic.os import (
    IOS,
    Android,
    Centos,
    Debian,
    Raspbian,
    RedHat,
    Ubuntu,
    Windows,
)
from diagrams.generic.os import (
    LinuxGeneral as Linux,
)
from diagrams.generic.place import Datacenter

Office = Datacenter

from diagrams.gcp.analytics import (
    BigQuery,
    PubSub,
)
from diagrams.gcp.api import (
    APIGateway,
    Endpoints,
)
from diagrams.gcp.compute import (
    GCE,
    GKE,
    CloudRun,
    ComputeEngine,
)
from diagrams.gcp.compute import (
    Functions as GcpCloudFunctions,
)
from diagrams.gcp.devtools import (
    Build as CloudBuild,
)
from diagrams.gcp.devtools import (
    CloudShell,
    ContainerRegistry,
)
from diagrams.gcp.devtools import (
    Scheduler as GcpCloudScheduler,
)
from diagrams.gcp.devtools import (
    Tasks as GcpCloudHttpTasks,
)
from diagrams.gcp.management import (
    Billing as GcpCloudBilling,
)
from diagrams.gcp.management import (
    Project as GcpCloudProject,
)
from diagrams.gcp.ml import (
    TPU as GcpTPU,
)
from diagrams.gcp.ml import (
    AIPlatform as GcpAIPlatform,
)
from diagrams.gcp.ml import (
    InferenceAPI as GcpMlInferenceAPI,
)
from diagrams.gcp.ml import (
    SpeechToText as GcpSpeechToText,
)
from diagrams.gcp.ml import (
    TextToSpeech as GcpTextToSpeech,
)
from diagrams.gcp.ml import (
    TranslationAPI as GcpTranslationAPI,
)
from diagrams.gcp.ml import (
    VertexAI,
)
from diagrams.gcp.ml import (
    VideoIntelligenceAPI as GcpVideoIntelligenceAPI,
)
from diagrams.gcp.ml import (
    VisionAPI as GcpVisionAPI,
)
from diagrams.gcp.database import (
    SQL as GcpCloudSQL,
)
from diagrams.gcp.network import (
    CDN as GcpCDN,
)
from diagrams.gcp.network import (
    DNS as GcpDNS,
)
from diagrams.gcp.network import (
    VPC as GcpVPC,
)
from diagrams.gcp.network import (
    Armor as GcpCloudArmor,
)
from diagrams.gcp.network import (
    FirewallRules as GcpFirewallRules,
)
from diagrams.gcp.network import (
    LoadBalancing as GcpLoadBalancing,
)
from diagrams.gcp.network import (
    NAT as GcpNAT,
)
from diagrams.gcp.operations import (
    Logging as GcpLogging,
)
from diagrams.gcp.operations import (
    Monitoring as GcpMonitoring,
)
from diagrams.gcp.security import (
    IAP as GcpIAP,
)
from diagrams.gcp.security import (
    KMS as GcpKeyManagementService,
)
from diagrams.gcp.security import (
    Iam as GcpIAM,
)
from diagrams.gcp.security import (
    ResourceManager as GcpResourceManager,
)
from diagrams.gcp.security import (
    SecretManager as GcpSecretManager,
)
from diagrams.gcp.storage import (
    GCS,
)
from diagrams.gcp.storage import (
    Filestore as GcpFilestore,
)
from diagrams.gcp.storage import (
    PersistentDisk as GcpPersistentDisk,
)
from diagrams.generic.storage import Storage
from diagrams.generic.virtualization import (
    XEN,
    Qemu,
    Virtualbox,
    Vmware,
)
from diagrams.onprem.aggregator import Fluentd
from diagrams.onprem.analytics import (
    Beam,
    Databricks,
    Dbt,
    Hadoop,
    Hive,
    PowerBI,
    Spark,
    Tableau,
)
from diagrams.onprem.certificates import (
    CertManager,
    LetsEncrypt,
)
from diagrams.onprem.ci import (
    CircleCI,
    GithubActions,
    GitlabCI,
    Jenkins,
)
from diagrams.onprem.client import (
    Client,
    User,
    Users,
)
from diagrams.onprem.compute import (
    Nomad,
    Server,
)
from diagrams.onprem.container import (
    K3S,
    Containerd,
    Docker,
)
from diagrams.onprem.database import (
    MSSQL,
    Cassandra,
    CockroachDB,
    Duckdb,
    MariaDB,
    MongoDB,
    Neo4J,
    Oracle,
    PostgreSQL,
    Scylla,
)
from diagrams.onprem.gitops import ArgoCD
from diagrams.onprem.groupware import Nextcloud
from diagrams.onprem.iac import (
    Ansible,
    Pulumi,
    Terraform,
)
from diagrams.onprem.inmemory import (
    Memcached,
    Redis,
)
from diagrams.onprem.mlops import Mlflow
from diagrams.onprem.monitoring import (
    Datadog,
    Grafana,
    Prometheus,
    Sentry,
)
from diagrams.onprem.network import (
    Nginx,
    Traefik,
)
from diagrams.onprem.proxmox import ProxmoxVE
from diagrams.onprem.queue import (
    Celery,
    Kafka,
    RabbitMQ,
)
from diagrams.onprem.search import Solr
from diagrams.onprem.security import (
    Bitwarden,
    Trivy,
    Vault,
)
from diagrams.onprem.tracing import (
    Jaeger,
    Tempo,
)
from diagrams.onprem.vcs import (
    Git,
    Github,
    Gitlab,
)
from diagrams.onprem.workflow import (
    Airflow,
    Digdag,
    KubeFlow,
)
from diagrams.programming.framework import (
    Angular,
    Django,
    DotNet,
    FastAPI,
    Flask,
    Flutter,
    GraphQL,
    Laravel,
    NextJs,
    Phoenix,
    Rails,
    React,
    Spring,
    Svelte,
    Vue,
)
from diagrams.programming.language import (
    PHP,
    Bash,
    C,
    Cpp,
    Csharp,
    Dart,
    Elixir,
    Erlang,
    Go,
    Java,
    JavaScript,
    Kotlin,
    Latex,
    Matlab,
    Python,
    R,
    Ruby,
    Rust,
    Scala,
    Swift,
    TypeScript,
)
from diagrams.programming.language import (
    NodeJS as NodeJs,
)
from diagrams.saas.analytics import (
    Dataform,
    Snowflake,
    Stitch,
)
from diagrams.saas.automation import N8N
from diagrams.saas.cdn import (
    Cloudflare,
    Fastly,
)
from diagrams.saas.chat import (
    Discord,
    Messenger,
    Slack,
    Teams,
    Telegram,
)
from diagrams.saas.identity import (
    Auth0,
    Okta,
)
from diagrams.saas.payment import (
    AmazonPay,
    Paypal,
    Stripe,
)


NODE_CATALOG: dict[str, tuple[str, str]] = {
    # C4 Model
    "C4Person": ("C4 Model", "A person (user) of the system"),
    "C4System": ("C4 Model", "A software system — the highest level of abstraction"),
    "C4SystemBoundary": (
        "C4 Model",
        "Context manager: groups elements inside a system boundary — use with `with C4SystemBoundary('name'):`",
    ),
    "C4Container": (
        "C4 Model",
        "A container: application, microservice, serverless function, database, etc.",
    ),
    "C4Database": ("C4 Model", "A database node in C4 style"),
    "C4Relationship": (
        "C4 Model",
        "Labeled relationship/edge between C4 elements — use like `element1 >> C4Relationship('label') >> element2`",
    ),
    # AWS General
    "InternetAlt2": ("AWS General", "Internet or external network endpoint"),
    "OfficeBuilding": ("AWS General", "Office or corporate building"),
    "MobileClient": ("AWS General", "Mobile client device"),
    # Elastic
    "Alerting": ("Elastic", "Elasticsearch alerting and notifications"),
    "Beats": ("Elastic", "Lightweight data shippers for Elasticsearch"),
    "ElasticSearch": ("Elastic", "Distributed search and analytics engine"),
    "Kibana": ("Elastic", "Visualization dashboard for Elasticsearch data"),
    "LogStash": ("Elastic", "Server-side data processing pipeline"),
    "Cloud": ("Elastic SaaS", "Elastic Cloud managed service"),
    "Elastic": ("Elastic SaaS", "Elastic platform or generic Elastic node"),
    # Firebase
    "Firebase": ("Firebase", "Firebase platform or generic Firebase service"),
    # Generic Compute
    "Rack": ("Generic Compute", "Server rack or compute hardware"),
    # Generic Database
    "SQL": ("Generic Database", "Generic SQL database"),
    # Generic Device
    "Mobile": ("Generic Device", "Generic mobile phone"),
    "Tablet": ("Generic Device", "Generic tablet device"),
    # Generic Network
    "VPN": ("Generic Network", "Virtual private network"),
    "Firewall": ("Generic Network", "Network firewall"),
    "Router": ("Generic Network", "Network router"),
    "Subnet": ("Generic Network", "Network subnet"),
    "Switch": ("Generic Network", "Network switch"),
    # Generic OS
    "IOS": ("Generic OS", "Apple iOS operating system"),
    "Android": ("Generic OS", "Android operating system"),
    "Centos": ("Generic OS", "CentOS Linux distribution"),
    "Debian": ("Generic OS", "Debian Linux distribution"),
    "Raspbian": ("Generic OS", "Raspbian OS for Raspberry Pi"),
    "RedHat": ("Generic OS", "Red Hat Enterprise Linux"),
    "Ubuntu": ("Generic OS", "Ubuntu Linux distribution"),
    "Windows": ("Generic OS", "Microsoft Windows operating system"),
    "Linux": ("Generic OS", "Generic Linux operating system"),
    # Generic Place
    "Datacenter": ("Generic Place", "Data center or server facility"),
    "Office": ("Generic Place", "Office building (alias for Datacenter)"),
    # Generic Storage
    "Storage": ("Generic Storage", "Generic storage service or bucket"),
    # Generic Virtualization
    "XEN": ("Generic Virtualization", "Xen hypervisor"),
    "Qemu": ("Generic Virtualization", "QEMU machine emulator"),
    "Virtualbox": ("Generic Virtualization", "Oracle VirtualBox VM"),
    "Vmware": ("Generic Virtualization", "VMware virtualization platform"),
    # GCP Analytics
    "BigQuery": ("GCP Analytics", "Data warehouse for large-scale SQL analytics"),
    "PubSub": ("GCP Analytics", "Asynchronous messaging and event streaming"),
    # GCP API
    "APIGateway": ("GCP API", "Managed API gateway for backend services"),
    "Endpoints": ("GCP API", "API management and deployment platform"),
    # GCP Compute
    "GCE": ("GCP Compute", "Google Compute Engine virtual machine"),
    "GKE": ("GCP Compute", "Google Kubernetes Engine managed cluster"),
    "CloudRun": ("GCP Compute", "Serverless container platform"),
    "ComputeEngine": ("GCP Compute", "Google Compute Engine (full name)"),
    "GcpCloudFunctions": ("GCP Compute", "Serverless functions triggered by events"),
    # GCP DevTools
    "CloudBuild": ("GCP DevTools", "CI/CD build service"),
    "CloudShell": ("GCP DevTools", "Browser-based shell for GCP management"),
    "ContainerRegistry": ("GCP DevTools", "Docker container image registry"),
    "GcpCloudScheduler": ("GCP DevTools", "Managed cron job scheduler"),
    "GcpCloudHttpTasks": ("GCP DevTools", "Asynchronous HTTP task queue"),
    # GCP Management
    "GcpCloudBilling": ("GCP Management", "Billing and cost management"),
    "GcpCloudProject": ("GCP Management", "GCP project resource container"),
    # GCP ML/AI
    "GcpTPU": ("GCP ML/AI", "Tensor Processing Unit for ML workloads"),
    "GcpAIPlatform": ("GCP ML/AI", "Managed ML training and serving platform"),
    "GcpMlInferenceAPI": ("GCP ML/AI", "ML model inference API"),
    "GcpSpeechToText": ("GCP ML/AI", "Speech recognition and transcription"),
    "GcpTextToSpeech": ("GCP ML/AI", "Text-to-speech synthesis"),
    "GcpTranslationAPI": ("GCP ML/AI", "Language translation API"),
    "VertexAI": ("GCP ML/AI", "Unified ML platform for training and deployment"),
    "GcpVideoIntelligenceAPI": ("GCP ML/AI", "Video content analysis and annotation"),
    "GcpVisionAPI": ("GCP ML/AI", "Image analysis and recognition"),
    # GCP Database
    "GcpCloudSQL": (
        "GCP Database",
        "Managed relational database service (MySQL, PostgreSQL, SQL Server)",
    ),
    # GCP Network
    "GcpCDN": ("GCP Network", "Content delivery network"),
    "GcpDNS": ("GCP Network", "Managed DNS service"),
    "GcpVPC": ("GCP Network", "Virtual private cloud network"),
    "GcpCloudArmor": ("GCP Network", "DDoS protection and WAF"),
    "GcpFirewallRules": ("GCP Network", "VPC firewall rules"),
    "GcpLoadBalancing": (
        "GCP Network",
        "Cloud load balancing for distributing traffic",
    ),
    "GcpNAT": (
        "GCP Network",
        "Cloud NAT for outbound internet access from private instances",
    ),
    # GCP Operations
    "GcpLogging": ("GCP Operations", "Centralized log management"),
    "GcpMonitoring": ("GCP Operations", "Infrastructure and application monitoring"),
    # GCP Security
    "GcpIAP": ("GCP Security", "Identity-Aware Proxy for app access control"),
    "GcpKeyManagementService": ("GCP Security", "Cryptographic key management"),
    "GcpIAM": ("GCP Security", "Identity and access management"),
    "GcpResourceManager": ("GCP Security", "Resource hierarchy and policy management"),
    "GcpSecretManager": ("GCP Security", "Secret storage and management"),
    # GCP Storage
    "GCS": ("GCP Storage", "Google Cloud Storage bucket"),
    "GcpFilestore": ("GCP Storage", "Managed NFS file storage"),
    "GcpPersistentDisk": ("GCP Storage", "Block storage for VM instances"),
    # On-Prem Aggregator
    "Fluentd": ("On-Prem Aggregator", "Log collector and unified logging layer"),
    # On-Prem Analytics
    "Beam": ("On-Prem Analytics", "Apache Beam unified batch/stream processing"),
    "Databricks": (
        "On-Prem Analytics",
        "Unified analytics and data lakehouse platform",
    ),
    "Dbt": ("On-Prem Analytics", "Data transformation tool for analytics"),
    "Hadoop": ("On-Prem Analytics", "Distributed big data processing framework"),
    "Hive": ("On-Prem Analytics", "Data warehouse on Hadoop for SQL queries"),
    "PowerBI": ("On-Prem Analytics", "Microsoft business intelligence and reporting"),
    "Spark": ("On-Prem Analytics", "Fast distributed data processing engine"),
    "Tableau": ("On-Prem Analytics", "Data visualization and BI platform"),
    # On-Prem Certificates
    "CertManager": ("On-Prem Certificates", "Kubernetes certificate management"),
    "LetsEncrypt": ("On-Prem Certificates", "Free automated SSL/TLS certificates"),
    # On-Prem CI/CD
    "CircleCI": ("On-Prem CI/CD", "Cloud-native CI/CD platform"),
    "GithubActions": ("On-Prem CI/CD", "GitHub-integrated CI/CD workflows"),
    "GitlabCI": ("On-Prem CI/CD", "GitLab-integrated CI/CD pipelines"),
    "Jenkins": ("On-Prem CI/CD", "Open-source automation server"),
    # Client
    "Client": ("Client", "Client application such as a web browser"),
    "User": ("Client", "End user or person interacting with the system"),
    "Users": ("Client", "Group of end users"),
    # On-Prem Compute
    "Nomad": ("On-Prem Compute", "HashiCorp workload orchestrator"),
    "Server": ("On-Prem Compute", "Generic server or compute instance"),
    # On-Prem Container
    "K3S": ("On-Prem Container", "Lightweight Kubernetes distribution"),
    "Containerd": ("On-Prem Container", "Container runtime"),
    "Docker": ("On-Prem Container", "Docker container runtime"),
    # On-Prem Database
    "MSSQL": ("On-Prem Database", "Microsoft SQL Server"),
    "Cassandra": ("On-Prem Database", "Distributed wide-column NoSQL database"),
    "CockroachDB": ("On-Prem Database", "Distributed SQL database"),
    "Duckdb": ("On-Prem Database", "In-process analytical SQL database"),
    "MariaDB": ("On-Prem Database", "MySQL-compatible relational database"),
    "MongoDB": ("On-Prem Database", "Document-oriented NoSQL database"),
    "Neo4J": ("On-Prem Database", "Graph database for connected data"),
    "Oracle": ("On-Prem Database", "Oracle relational database"),
    "PostgreSQL": ("On-Prem Database", "Open-source relational database"),
    "Scylla": ("On-Prem Database", "High-performance Cassandra-compatible database"),
    # On-Prem GitOps
    "ArgoCD": ("On-Prem GitOps", "Declarative GitOps CD for Kubernetes"),
    # On-Prem Groupware
    "Nextcloud": ("On-Prem Groupware", "Self-hosted file sync and collaboration"),
    # On-Prem IaC
    "Ansible": ("On-Prem IaC", "Agentless configuration management and automation"),
    "Pulumi": ("On-Prem IaC", "Infrastructure as code using general-purpose languages"),
    "Terraform": ("On-Prem IaC", "Infrastructure as code provisioning tool"),
    # On-Prem In-Memory
    "Memcached": ("On-Prem In-Memory", "Distributed memory object caching system"),
    "Redis": ("On-Prem In-Memory", "In-memory cache and key-value data store"),
    # On-Prem MLOps
    "Mlflow": ("On-Prem MLOps", "ML experiment tracking and model management"),
    # On-Prem Monitoring
    "Datadog": ("On-Prem Monitoring", "Cloud-scale monitoring and analytics"),
    "Grafana": ("On-Prem Monitoring", "Metrics visualization and dashboarding"),
    "Prometheus": ("On-Prem Monitoring", "Time-series monitoring and alerting"),
    "Sentry": ("On-Prem Monitoring", "Application error tracking and performance"),
    # On-Prem Network
    "Nginx": ("On-Prem Network", "Web server, reverse proxy, and load balancer"),
    "Traefik": ("On-Prem Network", "Cloud-native reverse proxy and load balancer"),
    # On-Prem Proxmox
    "ProxmoxVE": (
        "On-Prem Virtualization",
        "Open-source virtualization management platform",
    ),
    # On-Prem Queue
    "Celery": ("On-Prem Queue", "Distributed Python task queue"),
    "Kafka": ("On-Prem Queue", "Distributed event streaming platform"),
    "RabbitMQ": ("On-Prem Queue", "Open-source message broker"),
    # On-Prem Search
    "Solr": ("On-Prem Search", "Enterprise search platform"),
    # On-Prem Security
    "Bitwarden": ("On-Prem Security", "Open-source password manager"),
    "Trivy": ("On-Prem Security", "Container vulnerability scanner"),
    "Vault": ("On-Prem Security", "HashiCorp secrets management"),
    # On-Prem Tracing
    "Jaeger": ("On-Prem Tracing", "Distributed tracing for microservices"),
    "Tempo": ("On-Prem Tracing", "Grafana-compatible distributed tracing backend"),
    # On-Prem VCS
    "Git": ("On-Prem VCS", "Distributed version control system"),
    "Github": ("On-Prem VCS", "GitHub code hosting platform"),
    "Gitlab": ("On-Prem VCS", "GitLab DevOps platform"),
    # On-Prem Workflow
    "Airflow": ("On-Prem Workflow", "Workflow orchestration and scheduling"),
    "Digdag": ("On-Prem Workflow", "Workflow automation engine"),
    "KubeFlow": ("On-Prem Workflow", "ML workflow orchestration on Kubernetes"),
    # Programming Framework
    "Angular": ("Programming Framework", "Angular frontend framework"),
    "Django": ("Programming Framework", "Python web framework"),
    "DotNet": ("Programming Framework", ".NET application framework"),
    "FastAPI": ("Programming Framework", "Modern Python async web framework"),
    "Flask": ("Programming Framework", "Lightweight Python web framework"),
    "Flutter": ("Programming Framework", "Cross-platform mobile UI framework"),
    "GraphQL": ("Programming Framework", "API query language and runtime"),
    "Laravel": ("Programming Framework", "PHP web framework"),
    "NextJs": ("Programming Framework", "React-based full-stack framework"),
    "Phoenix": ("Programming Framework", "Elixir web framework"),
    "Rails": ("Programming Framework", "Ruby web framework"),
    "React": ("Programming Framework", "React frontend UI library"),
    "Spring": ("Programming Framework", "Java enterprise application framework"),
    "Svelte": ("Programming Framework", "Svelte frontend compiler framework"),
    "Vue": ("Programming Framework", "Vue.js frontend framework"),
    # Programming Language
    "PHP": ("Programming Language", "PHP scripting language"),
    "Bash": ("Programming Language", "Bash shell scripting"),
    "C": ("Programming Language", "C programming language"),
    "Cpp": ("Programming Language", "C++ programming language"),
    "Csharp": ("Programming Language", "C# programming language"),
    "Dart": ("Programming Language", "Dart programming language"),
    "Elixir": ("Programming Language", "Elixir functional language"),
    "Erlang": ("Programming Language", "Erlang concurrent language"),
    "Go": ("Programming Language", "Go programming language"),
    "Java": ("Programming Language", "Java programming language"),
    "JavaScript": ("Programming Language", "JavaScript programming language"),
    "Kotlin": ("Programming Language", "Kotlin programming language"),
    "Latex": ("Programming Language", "LaTeX typesetting system"),
    "Matlab": ("Programming Language", "MATLAB numerical computing"),
    "Python": ("Programming Language", "Python programming language"),
    "R": ("Programming Language", "R statistical programming language"),
    "Ruby": ("Programming Language", "Ruby programming language"),
    "Rust": ("Programming Language", "Rust systems programming language"),
    "Scala": ("Programming Language", "Scala JVM language"),
    "Swift": ("Programming Language", "Swift programming language"),
    "TypeScript": ("Programming Language", "TypeScript typed JavaScript"),
    "NodeJs": ("Programming Language", "Node.js JavaScript runtime"),
    # SaaS Analytics
    "Dataform": ("SaaS Analytics", "SQL-based data transformation in BigQuery"),
    "Snowflake": ("SaaS Analytics", "Cloud data warehouse platform"),
    "Stitch": ("SaaS Analytics", "ETL data pipeline service"),
    # SaaS Automation
    "N8N": ("SaaS Automation", "Workflow automation platform"),
    # SaaS CDN
    "Cloudflare": ("SaaS CDN", "CDN, DNS, and web security platform"),
    "Fastly": ("SaaS CDN", "Edge cloud and CDN platform"),
    # SaaS Chat
    "Discord": ("SaaS Chat", "Discord messaging platform"),
    "Messenger": ("SaaS Chat", "Facebook Messenger"),
    "Slack": ("SaaS Chat", "Slack team communication"),
    "Teams": ("SaaS Chat", "Microsoft Teams collaboration"),
    "Telegram": ("SaaS Chat", "Telegram messaging platform"),
    # SaaS Identity
    "Auth0": ("SaaS Identity", "Identity and authentication platform"),
    "Okta": ("SaaS Identity", "Enterprise identity management"),
    # SaaS Payment
    "AmazonPay": ("SaaS Payment", "Amazon payment processing"),
    "Paypal": ("SaaS Payment", "PayPal payment gateway"),
    "Stripe": ("SaaS Payment", "Stripe payment processing platform"),
}


def get_node_reference() -> str:
    """Format NODE_CATALOG into categorized markdown for the tool description."""
    by_category: dict[str, list[tuple[str, str]]] = {}
    for name, (category, description) in NODE_CATALOG.items():
        by_category.setdefault(category, []).append((name, description))

    lines = [
        "## Available Diagram Nodes",
        "",
        "**ONLY use node names listed below. These are the only names available.**",
        "",
    ]
    for category, nodes in by_category.items():
        lines.append(f"### {category}")
        for name, description in nodes:
            lines.append(f"- **{name}** - {description}")
        lines.append("")

    return "\n".join(lines)
