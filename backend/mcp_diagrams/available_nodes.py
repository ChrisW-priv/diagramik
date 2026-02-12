# ruff: noqa

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
