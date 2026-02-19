# Mermaid Diagram Style Guide

## Overview

Generate valid Mermaid diagram syntax. Choose the most appropriate diagram type based on user intent.

## Supported Diagram Types

### 1. Flowchart (Most Common)

**Use for:** Process flows, decision trees, workflows, system flows

**Direction options:** `TD` (top-down), `LR` (left-right), `BT` (bottom-top), `RL` (right-left)

#### Node Shapes

- `[text]` - Rectangle
- `(text)` - Rounded rectangle
- `{text}` - Diamond (decision)
- `([text])` - Stadium/pill shape
- `[[text]]` - Subroutine
- `[(text)]` - Cylinder (database)
- `((text))` - Circle
- `>text]` - Flag/asymmetric

#### Edge Styles

- `-->` - Arrow
- `---` - Line
- `-.->` - Dotted arrow
- `==>` - Thick arrow
- `--text-->` - Arrow with label
- `-->|text|` - Arrow with label (alternative)

#### Example

```mermaid
flowchart TD
    A[Start] --> B{Decision?}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
```

### 2. Sequence Diagram

**Use for:** API calls, message passing, interactions between services/actors

#### Arrow Types

- `->>` - Solid line with arrowhead
- `-->>` - Dotted line with arrowhead
- `-x` - Solid line with cross
- `--x` - Dotted line with cross

#### Example

```mermaid
sequenceDiagram
    participant U as User
    participant S as Server
    participant D as Database

    U->>S: HTTP Request
    activate S
    S->>D: Query
    D-->>S: Results
    S-->>U: Response
    deactivate S
```

### 3. Class Diagram

**Use for:** Object-oriented design, data models, entity relationships

#### Example

```mermaid
classDiagram
    class User {
        +String name
        +String email
        +login()
        +logout()
    }
    class Order {
        +int id
        +Date created
        +submit()
    }
    User "1" --> "*" Order : places
```

### 4. State Diagram

**Use for:** State machines, lifecycle diagrams, status transitions

#### Example

```mermaid
stateDiagram-v2
    [*] --> Pending
    Pending --> Processing : start
    Processing --> Completed : finish
    Processing --> Failed : error
    Failed --> Pending : retry
    Completed --> [*]
```

### 5. Entity Relationship Diagram

**Use for:** Database schemas, data modeling

#### Relationship Types

- `||--||` - One to one
- `||--o{` - One to many
- `o{--o{` - Many to many

#### Example

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
    PRODUCT ||--o{ LINE_ITEM : "ordered in"

    USER {
        int id PK
        string name
        string email
    }
    ORDER {
        int id PK
        int user_id FK
        date created
    }
```

### 6. Gantt Chart

**Use for:** Project timelines, scheduling

#### Example

```mermaid
gantt
    title Project Timeline
    dateFormat YYYY-MM-DD
    section Phase 1
        Task 1: a1, 2024-01-01, 30d
        Task 2: a2, after a1, 20d
    section Phase 2
        Task 3: a3, after a2, 15d
```

### 7. Pie Chart

**Use for:** Distribution, percentages, proportions

#### Example

```mermaid
pie title Distribution
    "Category A": 40
    "Category B": 30
    "Category C": 20
    "Category D": 10
```

### 8. Git Graph

**Use for:** Git branching strategies, version control flows

#### Example

```mermaid
gitGraph
    commit
    branch develop
    checkout develop
    commit
    commit
    checkout main
    merge develop
    commit
```

## Style Guide

### Labels

- Keep labels concise (1-3 words when possible)
- Use descriptive action verbs for edges (e.g., "sends", "queries", "returns")
- For nodes, describe what it IS, not what it does

### Subgraphs (Grouping)

Use subgraphs to group related components:

```mermaid
flowchart TD
    subgraph Cloud["AWS Cloud"]
        subgraph VPC["VPC"]
            EC2[EC2 Instance]
            RDS[(Database)]
        end
    end
    User --> EC2
    EC2 --> RDS
```

### Styling

You can add custom styles when needed:

```mermaid
flowchart TD
    A[Start]:::green --> B[Process]:::blue
    classDef green fill:#9f6,stroke:#333
    classDef blue fill:#69f,stroke:#333
```

## Complete Examples

### Simple API Flow

**INPUT:** User sends request to API Gateway, which forwards to Lambda, which queries DynamoDB

```mermaid
flowchart LR
    U[User] -->|HTTP Request| AG[API Gateway]
    AG -->|Invoke| L[Lambda]
    L -->|Query| DB[(DynamoDB)]
    DB -->|Results| L
    L -->|Response| AG
    AG -->|HTTP Response| U
```

### Microservices Architecture

**INPUT:** Show a microservices architecture with an API gateway routing to user service, order service, and payment service. Each service has its own database.

```mermaid
flowchart TD
    Client[Client App] --> GW[API Gateway]

    subgraph Services
        GW --> US[User Service]
        GW --> OS[Order Service]
        GW --> PS[Payment Service]
    end

    subgraph Databases
        US --> UDB[(User DB)]
        OS --> ODB[(Order DB)]
        PS --> PDB[(Payment DB)]
    end

    OS -->|Validate| US
    PS -->|Verify| OS
```

### CI/CD Pipeline

**INPUT:** Show a CI/CD pipeline from code commit through testing to deployment

```mermaid
flowchart LR
    subgraph Development
        A[Code Commit] --> B[Build]
    end

    subgraph Testing
        B --> C[Unit Tests]
        C --> D[Integration Tests]
        D --> E{Tests Pass?}
    end

    subgraph Deployment
        E -->|Yes| F[Deploy to Staging]
        F --> G[Deploy to Production]
    end

    E -->|No| A
```
