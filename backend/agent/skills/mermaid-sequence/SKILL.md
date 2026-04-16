---
name: mermaid-sequence
description: Create Mermaid sequence diagrams showing interactions between actors over time. Use this skill when the user wants to visualize API calls, message flows, authentication flows, protocols, service-to-service communication, or any scenario where the order of interactions between components matters. Triggers on "sequence diagram", "show the API calls", "diagram the auth flow", "how do these services talk", "draw the message flow", or whenever the user describes a back-and-forth interaction between systems or people.
---

# Mermaid Sequence Diagram Skill

Use this skill to write Mermaid `sequenceDiagram` diagrams — the best way to show ordered interactions between actors or systems.

## Basic structure

```mermaid
---
title: Login Flow
config:
  theme: base
---
sequenceDiagram
    participant User
    participant API
    participant DB

    User->>API: POST /login
    API->>DB: SELECT user WHERE email=?
    DB-->>API: user row
    API-->>User: 200 OK + JWT
```

Always wrap in a fenced code block with `mermaid` language tag.

## Config options

Always include a YAML frontmatter block to set the title and theme:

```
---
title: My Sequence Diagram
config:
  theme: base
---
```

Always set:
- `title` — descriptive name shown above the diagram
- `theme: base` — clean, customizable styling that works across renderers

Sequence-specific options under `sequence:`:

```
---
title: My Sequence Diagram
config:
  theme: base
  sequence:
    actorMargin: 50
    useMaxWidth: false
---
```

| Option | Default | Effect |
|--------|---------|--------|
| `actorMargin` | `50` | Horizontal space between participant boxes |
| `boxMargin` | `10` | Margin inside actor boxes |
| `useMaxWidth` | `true` | Constrain diagram to container width |
| `diagramMarginX` | `50` | Left/right outer margin |
| `diagramMarginY` | `10` | Top/bottom outer margin |

## Participant types

Declare participants explicitly at the top to control ordering and shape:

| Keyword | Shape | Use for |
|---------|-------|---------|
| `participant Name` | Rectangle | Generic component |
| `actor Name` | Stick figure | Human user |
| `participant Name as Alias` | Rectangle | Long name, short alias |

Undeclared participants appear in the order they're first used.

## Arrow types

| Syntax | Appearance | Use for |
|--------|------------|---------|
| `A->>B: msg` | Solid + arrowhead | Synchronous call/request |
| `A-->>B: msg` | Dotted + arrowhead | Response/return |
| `A->B: msg` | Solid, no head | Fire and forget |
| `A-->B: msg` | Dotted, no head | Async notification |
| `A-xB: msg` | Solid + cross | Message lost/rejected |
| `A-)B: msg` | Solid + open head | Async (non-blocking) |

Use `-->>` for responses — the dotted line visually signals "this is the reply".

## Activation (lifelines)

Show when an actor is actively processing:

```mermaid
sequenceDiagram
    Client->>+Server: Request
    Server->>+DB: Query
    DB-->>-Server: Results
    Server-->>-Client: Response
```

`+` activates, `-` deactivates. Or use explicit `activate`/`deactivate` keywords.

## Grouping blocks

```mermaid
sequenceDiagram
    loop Every 30s
        Agent->>Server: Heartbeat
        Server-->>Agent: ACK
    end

    alt Happy path
        Client->>API: Request
        API-->>Client: 200 OK
    else Error
        Client->>API: Request
        API-->>Client: 500 Error
    end

    opt Only if logged in
        Client->>API: GET /profile
    end

    par Parallel actions
        Client->>ServiceA: Call
    and
        Client->>ServiceB: Call
    end
```

## Notes

```
Note right of Actor: text here
Note left of Actor: text here
Note over Actor1,Actor2: spans both
```

## Grouping actors with boxes

```mermaid
sequenceDiagram
    box Frontend
        participant Browser
        participant PWA
    end
    box rgb(200,220,255) Backend
        participant API
        participant Worker
    end
```

## Sequence numbers

Add `autonumber` at the top to automatically number each message — useful for documentation references:

```mermaid
sequenceDiagram
    autonumber
    Client->>Server: Connect
    Server-->>Client: ACK
```

## Tips for good sequence diagrams

- List participants top-to-bottom in the order they first appear in the flow
- Keep message labels short — use technical names (`POST /auth`, `SELECT`, `ACK`)
- Use `alt/else` for error paths rather than drawing two full flows
- Use `loop` for polling or retry logic
- Activate/deactivate when showing database transactions or processing windows helps readability
- Use `box` to group microservices or layers (frontend/backend/storage)

## Common patterns

**REST API call with auth:**
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Auth

    Client->>API: GET /resource + Bearer token
    API->>Auth: Validate token
    Auth-->>API: Valid, user_id=42
    API-->>Client: 200 + data
```

**OAuth2 flow:**
```mermaid
sequenceDiagram
    actor User
    participant App
    participant AuthServer
    participant ResourceServer

    User->>App: Click "Login with Google"
    App->>AuthServer: Redirect + client_id
    AuthServer-->>User: Login page
    User->>AuthServer: Credentials
    AuthServer-->>App: code=xyz
    App->>AuthServer: code + client_secret
    AuthServer-->>App: access_token
    App->>ResourceServer: GET /profile + access_token
    ResourceServer-->>App: User data
```
