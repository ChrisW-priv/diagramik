# Curated diagram icons with non-conflicting names
# This file provides explicit imports to avoid naming conflicts
# Usage: from available_nodes import *

# =============================================================================
# ONPREM ICONS
# =============================================================================

# Analytics/BI  # noqa
from diagrams.onprem.analytics import (  # noqa
    Spark,  # noqa
    Flink,  # noqa
    Hadoop,  # noqa
    Hive,  # noqa
    Presto,  # noqa
    Trino,  # noqa
    Metabase,  # noqa
    Superset,  # noqa
    Tableau,  # noqa
    Databricks,  # noqa
    Dbt,  # noqa
)  # noqa  # noqa
from diagrams.onprem.analytics import Powerbi as PowerBI  # noqa

# CI/CD  # noqa
from diagrams.onprem.ci import Jenkins, Teamcity  # noqa
from diagrams.onprem.ci import Gitlabci as GitlabCI  # noqa
from diagrams.onprem.ci import GithubActions  # noqa
from diagrams.onprem.ci import Circleci as CircleCI  # noqa
from diagrams.onprem.ci import Travisci as TravisCI  # noqa
from diagrams.onprem.ci import Droneci as DroneCI  # noqa

# GitOps  # noqa
from diagrams.onprem.gitops import Flux, Flagger  # noqa
from diagrams.onprem.gitops import Argocd as ArgoCD  # noqa

# IaC  # noqa
from diagrams.onprem.iac import Terraform, Ansible, Pulumi, Atlantis, Puppet, Awx  # noqa

# Clients/Users (PREFIXED - conflicts with K8s)  # noqa
from diagrams.onprem.client import Client  # noqa
from diagrams.onprem.client import User  # noqa
from diagrams.onprem.client import Users  # noqa

# Compute  # noqa
from diagrams.onprem.compute import Server, Nomad  # noqa

# Containers  # noqa
from diagrams.onprem.container import Docker, Containerd, K3S, Firecracker  # noqa
from diagrams.onprem.container import Lxc as LXC  # noqa

# ALL Databases (unique names - no conflicts)  # noqa
from diagrams.onprem.database import (  # noqa
    Cassandra,  # noqa
    Couchbase,  # noqa
    Dgraph,  # noqa
    Druid,  # noqa
    Scylla,  # noqa
    Neo4J,  # noqa
    Oracle,  # noqa
)  # noqa
from diagrams.onprem.database import Postgresql as PostgreSQL  # noqa
from diagrams.onprem.database import Mysql as MySQL  # noqa
from diagrams.onprem.database import Mariadb as MariaDB  # noqa
from diagrams.onprem.database import Mongodb as MongoDB  # noqa
from diagrams.onprem.database import Cockroachdb as CockroachDB  # noqa
from diagrams.onprem.database import Clickhouse as ClickHouse  # noqa
from diagrams.onprem.database import Influxdb as InfluxDB  # noqa
from diagrams.onprem.database import Mssql as MSSQL  # noqa
from diagrams.onprem.database import Duckdb as DuckDB  # noqa
from diagrams.onprem.database import Hbase as HBase  # noqa
from diagrams.onprem.database import Janusgraph as JanusGraph  # noqa
from diagrams.onprem.database import Qdrant  # noqa

# Caching/In-Memory  # noqa
from diagrams.onprem.inmemory import Redis, Memcached, Hazelcast, Aerospike  # noqa

# MLOps  # noqa
from diagrams.onprem.mlops import Mlflow, Polyaxon  # noqa

# Monitoring  # noqa
from diagrams.onprem.monitoring import (  # noqa
    Prometheus,  # noqa
    Grafana,  # noqa
    Datadog,  # noqa
    Splunk,  # noqa
    Nagios,  # noqa
    Zabbix,  # noqa
    Thanos,  # noqa
    Cortex,  # noqa
    Mimir,  # noqa
    PrometheusOperator,  # noqa
    Sentry,  # noqa
    Dynatrace,  # noqa
    Humio,  # noqa
    Newrelic,  # noqa
)  # noqa

# Network (including CISCO)  # noqa
from diagrams.onprem.network import (  # noqa
    Nginx,  # noqa
    Apache,  # noqa
    Traefik,  # noqa
    Envoy,  # noqa
    Istio,  # noqa
    Linkerd,  # noqa
    Kong,  # noqa
    Consul,  # noqa
    Etcd,  # noqa
    Zookeeper,  # noqa
    Internet,  # noqa
    Ambassador,  # noqa
    Caddy,  # noqa
    Tomcat,  # noqa
    Gunicorn,  # noqa
    Jetty,  # noqa
    Pomerium,  # noqa
    Tyk,  # noqa
    Yarp,  # noqa
)  # noqa
from diagrams.onprem.network import Haproxy as HAProxy  # noqa
from diagrams.onprem.network import Vyos as VyOS  # noqa
from diagrams.onprem.network import Pfsense as PFSense  # noqa
from diagrams.onprem.network import Opnsense as OPNSense  # noqa
from diagrams.onprem.network import CiscoRouter, CiscoSwitchL2, CiscoSwitchL3, Mikrotik  # noqa

# Proxmox  # noqa
from diagrams.onprem.proxmox import Pve as ProxmoxVE  # noqa

# Queues  # noqa
from diagrams.onprem.queue import Kafka, Celery, Nats  # noqa
from diagrams.onprem.queue import Rabbitmq as RabbitMQ  # noqa
from diagrams.onprem.queue import Activemq as ActiveMQ  # noqa
from diagrams.onprem.queue import Zeromq as ZeroMQ  # noqa
from diagrams.onprem.queue import Emqx as EMQX  # noqa

# Tracing  # noqa
from diagrams.onprem.tracing import Jaeger, Tempo  # noqa

# VCS  # noqa
from diagrams.onprem.vcs import Git, Github, Gitlab, Gitea, Svn  # noqa

# Workflow  # noqa
from diagrams.onprem.workflow import Airflow, Kubeflow, Digdag  # noqa
from diagrams.onprem.workflow import Nifi as NiFi  # noqa

# Logging/Aggregator  # noqa
from diagrams.onprem.logging import Loki, Graylog  # noqa
from diagrams.onprem.logging import Fluentbit as FluentBit  # noqa
from diagrams.onprem.logging import Rsyslog as RSyslog  # noqa
from diagrams.onprem.logging import SyslogNg  # noqa
from diagrams.onprem.aggregator import Fluentd, Vector  # noqa

# Certificates  # noqa
from diagrams.onprem.certificates import CertManager, LetsEncrypt  # noqa

# Security  # noqa
from diagrams.onprem.security import Vault, Trivy, Bitwarden  # noqa

# =============================================================================  # noqa
# AWS ICONS  # noqa
# =============================================================================  # noqa

# Compute  # noqa
from diagrams.aws.compute import EC2, Lambda, ECS, EKS, Fargate, Batch, Lightsail  # noqa

# Storage - DUAL EXPORT: Specific names + generic aliases  # noqa
from diagrams.aws.storage import (  # noqa
    Backup as AwsBackup,  # noqa
    Snowball,  # noqa
    SnowballEdge,  # noqa
    Snowmobile,  # noqa
)  # noqa
from diagrams.aws.storage import SimpleStorageServiceS3Bucket as S3Bucket  # noqa
from diagrams.aws.storage import SimpleStorageServiceS3 as S3  # noqa
from diagrams.aws.storage import ElasticBlockStoreEBS as EBS  # noqa
from diagrams.aws.storage import ElasticFileSystemEFS as EFS  # noqa
from diagrams.aws.storage import Fsx as FSx  # noqa
from diagrams.aws.storage import Storage as AwsStorage  # Generic alias  # noqa

# Database  # noqa
from diagrams.aws.database import (  # noqa
    RDS,  # noqa
    Aurora,  # noqa
    Dynamodb,  # noqa
    ElastiCache,  # noqa
    Redshift,  # noqa
    Neptune,  # noqa
    DocumentDB,  # noqa
    Timestream,  # noqa
    QLDB,  # noqa
)  # noqa

DynamoDB = Dynamodb  # CamelCase alias  # noqa

# Network  # noqa
from diagrams.aws.network import (  # noqa
    VPC,  # noqa
    CloudFront,  # noqa
    Route53,  # noqa
    APIGateway,  # noqa
    DirectConnect,  # noqa
    TransitGateway,  # noqa
    NATGateway,  # noqa
    InternetGateway,  # noqa
    PrivateSubnet,  # noqa
    PublicSubnet,  # noqa
    Nacl,  # noqa
    NetworkFirewall,  # noqa
)  # noqa
from diagrams.aws.network import ElasticLoadBalancing as ELB  # noqa
from diagrams.aws.network import ElbApplicationLoadBalancer as ALB  # noqa
from diagrams.aws.network import ElbNetworkLoadBalancer as NLB  # noqa
from diagrams.aws.network import ElbClassicLoadBalancer as CLB  # noqa
from diagrams.aws.network import Endpoint as AwsEndpoint  # noqa
from diagrams.aws.network import GlobalAccelerator as GAX  # noqa

# Analytics  # noqa
from diagrams.aws.analytics import Athena, EMR, Kinesis, Glue, Quicksight, LakeFormation  # noqa

# ML  # noqa
from diagrams.aws.ml import Sagemaker, Rekognition, Comprehend, Lex, Polly, Textract  # noqa

# Security  # noqa
from diagrams.aws.security import IAM, Cognito, KMS, WAF, Shield, SecretsManager  # noqa

# =============================================================================  # noqa
# GCP ICONS  # noqa
# =============================================================================  # noqa

# Compute  # noqa
from diagrams.gcp.compute import ComputeEngine, GKE, Functions, Run, AppEngine  # noqa

# Storage - DUAL EXPORT: Specific names + generic aliases  # noqa
from diagrams.gcp.storage import Filestore, PersistentDisk  # noqa
from diagrams.gcp.storage import Storage as GCS  # Primary specific name  # noqa

GcsBucket = GCS  # Alias for bucket-style naming  # noqa
GcpStorage = GCS  # Generic alias for discoverability  # noqa

# Database  # noqa
from diagrams.gcp.database import Spanner, Bigtable, Memorystore, Datastore  # noqa
from diagrams.gcp.database import SQL as CloudSQL  # Specific GCP name  # noqa

# Network  # noqa
from diagrams.gcp.network import (  # noqa
    LoadBalancing as GcpLoadBalancing,  # noqa
    CDN as GcpCDN,  # noqa
    Armor as CloudArmor,  # noqa
    NAT as GcpNAT,  # noqa
    DedicatedInterconnect,  # noqa
    FirewallRules,  # noqa
    TrafficDirector,  # noqa
    VirtualPrivateCloud,  # noqa
)  # noqa
from diagrams.gcp.network import DNS as CloudDNS  # noqa
from diagrams.gcp.network import Router as GcpRouter  # noqa
from diagrams.gcp.network import VPN as GcpVPN  # noqa

GcpVPC = VirtualPrivateCloud  # Alias  # noqa

# Analytics  # noqa
from diagrams.gcp.analytics import BigQuery, Dataflow, Dataproc, PubSub, Composer  # noqa

# ML  # noqa
from diagrams.gcp.ml import AIPlatform, AutoML  # noqa
from diagrams.gcp.ml import NaturalLanguageAPI, VisionAPI, SpeechToText  # noqa

# =============================================================================  # noqa
# FIREBASE ICONS  # noqa
# =============================================================================  # noqa

from diagrams.firebase.base import Firebase  # noqa

# Develop  # noqa
from diagrams.firebase.develop import Authentication as FirebaseAuth  # noqa
from diagrams.firebase.develop import Firestore as FirebaseFirestore  # noqa
from diagrams.firebase.develop import Functions as FirebaseFunctions  # noqa
from diagrams.firebase.develop import Hosting as FirebaseHosting  # noqa
from diagrams.firebase.develop import MLKit as FirebaseMLKit  # noqa
from diagrams.firebase.develop import RealtimeDatabase as FirebaseRealtimeDB  # noqa
from diagrams.firebase.develop import Storage as FirebaseStorage  # noqa

# Grow  # noqa
from diagrams.firebase.grow import Messaging as FCM  # noqa
from diagrams.firebase.grow import RemoteConfig as FirebaseRemoteConfig  # noqa
from diagrams.firebase.grow import ABTesting as FirebaseABTesting  # noqa
from diagrams.firebase.grow import DynamicLinks as FirebaseDynamicLinks  # noqa

# Quality  # noqa
from diagrams.firebase.quality import Crashlytics as FirebaseCrashlytics  # noqa
from diagrams.firebase.quality import TestLab as FirebaseTestLab  # noqa
from diagrams.firebase.quality import PerformanceMonitoring as FirebasePerformance  # noqa

# =============================================================================  # noqa
# ELASTIC/ELK ICONS  # noqa
# =============================================================================  # noqa

# Core ELK Stack  # noqa
from diagrams.elastic.elasticsearch import (  # noqa
    Elasticsearch,  # noqa
    Kibana,  # noqa
    Logstash,  # noqa
    Beats,  # noqa
    Stack,  # noqa
)  # noqa
from diagrams.elastic.elasticsearch import MachineLearning as ElasticML  # noqa
from diagrams.elastic.elasticsearch import SQL as ElasticSQL  # noqa
from diagrams.elastic.elasticsearch import Monitoring as ElasticMonitoring  # noqa

# All Beats  # noqa
from diagrams.elastic.beats import (  # noqa
    Filebeat,  # noqa
    Metricbeat,  # noqa
    Packetbeat,  # noqa
    Heartbeat,  # noqa
    Auditbeat,  # noqa
    Winlogbeat,  # noqa
    Functionbeat,  # noqa
)  # noqa
from diagrams.elastic.beats import APM as ElasticAPMBeat  # noqa

# Agent  # noqa
from diagrams.elastic.agent import Agent as ElasticAgent  # noqa
from diagrams.elastic.agent import Fleet as ElasticFleet  # noqa
from diagrams.elastic.agent import Integrations as ElasticIntegrations  # noqa
from diagrams.elastic.agent import Endpoint as ElasticAgentEndpoint  # noqa

# Security  # noqa
from diagrams.elastic.security import SIEM as ElasticSIEM  # noqa
from diagrams.elastic.security import Xdr as ElasticXDR  # noqa
from diagrams.elastic.security import Endpoint as ElasticSecurityEndpoint  # noqa
from diagrams.elastic.security import Security as ElasticSecurity  # noqa

# Cloud/SaaS  # noqa
from diagrams.elastic.saas import Elastic as ElasticSaas  # noqa
from diagrams.elastic.saas import Cloud as ElasticCloud  # noqa

# Observability  # noqa
from diagrams.elastic.observability import Observability as ElasticObservability  # noqa
from diagrams.elastic.observability import Logs as ElasticLogs  # noqa
from diagrams.elastic.observability import Metrics as ElasticMetrics  # noqa
from diagrams.elastic.observability import Uptime as ElasticUptime  # noqa
from diagrams.elastic.observability import APM as ElasticAPM  # noqa

# Orchestration  # noqa
from diagrams.elastic.orchestration import ECE, ECK  # noqa

# =============================================================================  # noqa
# KUBERNETES ICONS  # noqa
# =============================================================================  # noqa

# Compute  # noqa
from diagrams.k8s.compute import Pod, Job  # noqa
from diagrams.k8s.compute import Deploy as Deployment  # noqa
from diagrams.k8s.compute import STS as StatefulSet  # noqa
from diagrams.k8s.compute import DS as DaemonSet  # noqa
from diagrams.k8s.compute import RS as ReplicaSet  # noqa
from diagrams.k8s.compute import Cronjob as CronJob  # noqa

# Control Plane  # noqa
from diagrams.k8s.controlplane import Kubelet  # noqa
from diagrams.k8s.controlplane import API as K8sAPIServer  # noqa
from diagrams.k8s.controlplane import CM as K8sControllerManager  # noqa
from diagrams.k8s.controlplane import Sched as K8sScheduler  # noqa
from diagrams.k8s.controlplane import KProxy as KubeProxy  # noqa

# Network  # noqa
from diagrams.k8s.network import SVC as K8sService  # noqa
from diagrams.k8s.network import Ing as K8sIngress  # noqa
from diagrams.k8s.network import Netpol as K8sNetworkPolicy  # noqa
from diagrams.k8s.network import Ep as K8sEndpoint  # noqa

# Storage  # noqa
from diagrams.k8s.storage import PV as K8sPersistentVolume  # noqa
from diagrams.k8s.storage import PVC as K8sPersistentVolumeClaim  # noqa
from diagrams.k8s.storage import SC as K8sStorageClass  # noqa
from diagrams.k8s.storage import Vol as K8sVolume  # noqa

# Pod Config  # noqa
from diagrams.k8s.podconfig import CM as K8sConfigMap  # noqa
from diagrams.k8s.podconfig import Secret as K8sSecret  # noqa

# Cluster Config  # noqa
from diagrams.k8s.clusterconfig import HPA  # noqa
from diagrams.k8s.clusterconfig import Limits as K8sLimitRange  # noqa
from diagrams.k8s.clusterconfig import Quota as K8sQuota  # noqa

# RBAC  # noqa
from diagrams.k8s.rbac import CRole as K8sClusterRole  # noqa
from diagrams.k8s.rbac import CRB as K8sClusterRoleBinding  # noqa
from diagrams.k8s.rbac import Role as K8sRole  # noqa
from diagrams.k8s.rbac import RB as K8sRoleBinding  # noqa
from diagrams.k8s.rbac import SA as K8sServiceAccount  # noqa
from diagrams.k8s.rbac import Group as K8sGroup  # noqa
from diagrams.k8s.rbac import User as K8sUser  # noqa

# Ecosystem  # noqa
from diagrams.k8s.ecosystem import Helm, Kustomize, ExternalDns, Krew  # noqa

# Infrastructure  # noqa
from diagrams.k8s.infra import ETCD as K8sETCD  # noqa
from diagrams.k8s.infra import Master as K8sMaster  # noqa
from diagrams.k8s.infra import Node as K8sNode  # noqa

# Group  # noqa
from diagrams.k8s.group import NS as K8sNamespace  # noqa

# Others  # noqa
from diagrams.k8s.others import CRD as K8sCRD  # noqa
from diagrams.k8s.others import PSP as K8sPSP  # noqa

# Chaos  # noqa
from diagrams.k8s.chaos import ChaosMesh, LitmusChaos  # noqa

# =============================================================================  # noqa
# GENERIC ICONS (ALL PREFIXED with Generic)  # noqa
# =============================================================================  # noqa

# Devices  # noqa
from diagrams.generic.device import Mobile as GenericMobile  # noqa
from diagrams.generic.device import Tablet as GenericTablet  # noqa

# Compute  # noqa
from diagrams.generic.compute import Rack as GenericRack  # noqa

# Place  # noqa
from diagrams.generic.place import Datacenter as GenericDatacenter  # noqa

# Storage  # noqa
from diagrams.generic.storage import Storage as GenericStorage  # noqa

# OS (ALL)  # noqa
from diagrams.generic.os import Ubuntu as GenericUbuntu  # noqa
from diagrams.generic.os import Debian as GenericDebian  # noqa
from diagrams.generic.os import Centos as GenericCentos  # noqa
from diagrams.generic.os import RedHat as GenericRedHat  # noqa
from diagrams.generic.os import Suse as GenericSuse  # noqa
from diagrams.generic.os import Windows as GenericWindows  # noqa
from diagrams.generic.os import LinuxGeneral as GenericLinux  # noqa
from diagrams.generic.os import Android as GenericAndroid  # noqa
from diagrams.generic.os import IOS as GenericIOS  # noqa
from diagrams.generic.os import Raspbian as GenericRaspbian  # noqa

# Virtualization  # noqa
from diagrams.generic.virtualization import Vmware as GenericVmware  # noqa
from diagrams.generic.virtualization import Virtualbox as GenericVirtualbox  # noqa
from diagrams.generic.virtualization import Qemu as GenericQemu  # noqa
from diagrams.generic.virtualization import XEN as GenericXEN  # noqa

# Network  # noqa
from diagrams.generic.network import Switch as GenericSwitch  # noqa
from diagrams.generic.network import Router as GenericRouter  # noqa
from diagrams.generic.network import Subnet as GenericSubnet  # noqa
from diagrams.generic.network import VPN as GenericVPN  # noqa
from diagrams.generic.network import Firewall as GenericFirewall  # noqa
