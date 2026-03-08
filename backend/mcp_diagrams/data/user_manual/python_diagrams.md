# Python Diagrams Style Guide

## Overview

Generate Python code using the `diagrams` library to create cloud architecture and infrastructure diagrams. The code will be executed in a controlled environment with all necessary imports pre-configured.

## CRITICAL RULES

1. **NO import statements** - All imports are handled externally
1. **NO with statement** - The Diagram context manager is handled externally
1. Code will be inserted into this template:

```python
from diagrams import Diagram, Cluster, Node, Edge
from diagrams.gcp.compute import CloudRun
from diagrams.gcp.database import SQL
# ... Other nodes are imported

kwargs = {...}  # custom keyword arguments
with Diagram(**kwargs):
    exec(kwargs.get("code"))  # YOUR CODE RUNS HERE
```

4. Code is already properly indented - no need for extra indentation

## Node Labels

Label each node with:

1. Type of the node
1. Purpose of the node (in parentheses)
1. Separated by newline (`\\n`)

**Hard limit: 15 characters per line**

### Examples

- Weekly scheduler: `scheduler = GcpCloudScheduler("Scheduler\\n(Weekly)")`
- Cloud Function querying SQL: `fetch_function = GcpCloudFunctions("Cloud Func\\n(SQL data qry)")`
- FTP Server for audio files: `ftp_server = Server("FTP Server\\n(Audio Files)")`

**IMPORTANT:** Use `\\n` (double backslash) for newlines in code!

**When to skip purpose:**

- Self-explanatory services: message queues, generic databases, block storages
- BUT if a database/storage holds specific data types, label it (e.g., "(Videos)", "(User Data)")

## Edge Labels

**Always label edges** between nodes with 1-2 word phrases starting with a verb.

### Example

```python
Server("Server\\n(Data Source)") >> Edge(label="Saves audio") >> Storage("GCS Bucket\\n(Data Sink)")
```

## Clusters and Groups

### 1. Cluster (Solid Boundary)

Represents boundaries between:

- Regions
- Teams
- Cloud providers
- Networks
- Companies

#### Example: Cross-Team Architecture

```python
with Cluster("Source Team"):
    cloudrun_ingest = CloudRun("CloudRun Job\\n(Data Ingest)")

with Cluster("Team1"):
    storage_team1 = Storage("GCS Bucket\\n(Data Sink)")

with Cluster("Team2"):
    storage_team2 = Storage("GCS Bucket\\n(Data Sink)")

cloudrun_ingest >> Edge(label="Saves into") >> storage_team1
cloudrun_ingest >> Edge(label="Saves into") >> storage_team2
```

### 2. Enumerations (List Notation)

Represents N replicas of the same element serving the same purpose.

#### Example: Multiple Workers

```python
Nginx("lb") >> [Server("worker1"),
                Server("worker2"),
                Server("worker3"),
                Server("worker4"),
                Server("worker5")] >> PostgreSQL("events")
```

## Complete Examples

### Simple Example

**INPUT:** User uses a Browser to connect to our website. Main entrypoint is the cloud Load Balancer, which directs traffic to either GCS or CloudRun Service hosting Django server.

```python
user = User("User")
browser = Client("Browser")
with Cluster("Our VPC"):
    lb = Nginx("Load Balancer")
    lb >> [CloudRun("CloudRun Service\\n(Django server)"), Storage("GCS Bucket\\n(Static HTML)")]
user >> browser >> lb
```

### Complex Example

**INPUT:** Our CloudRun Job triggered once a week by the Scheduler, downloads video files from FTP server owned by different company, saves it into GCS bucket. Save to GCS bucket triggers EventArc that will start a Cloud Function that will conditionally copy to buckets owned by different teams. Our Company is called "inc.1", other is "inc.2", our team is "main team", label other teams as "Team 1" and "Team 2"

```python
with Cluster("inc.1"):
    with Cluster("main team"):
        cloudrun_import = CloudRun("CloudRun Job\\n(File Import)")
        raw_storage = Storage("GCS Bucket\\n(Raw Storage)")
        eventarc = PubSub("EventArc")
        cloudrun_import >> Edge(label="Saves into") >> raw_storage >> eventarc
        cloud_functions = [GcpCloudFunctions("Cloud Func\\n(Copy data)") for _ in range(2)]
        eventarc >> Edge(label="Triggers") >> cloud_functions
    for cf, team in zip(cloud_functions, ["Team1", "Team2"]):
        with Cluster(team):
            cf >> Edge(label="Copies into") >> Storage("GCS Bucket")

with Cluster("inc.2"):
    files = Server("FTP server\\n(Videos)")

cloudrun_import >> Edge(label="Requests") >> files
```
