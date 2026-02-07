# Backend Taskfile Configuration

## Overview

The backend Taskfile has been configured to:

1. Include and use agent tasks from `agent/Taskfile.yml`
1. Enable running integration tests with a real MCP server
1. Provide helper scripts for automated server management

## Configuration

### Taskfile Includes

Added to `backend/Taskfile.yml`:

```yaml
includes:
  agent:
    taskfile: agent/Taskfile.yml
    dir: agent
```

This enables calling all agent tasks with the `agent:` prefix from the backend directory.

### Available Agent Tasks

**From agent/Taskfile.yml (via include):**

- `task agent:sync` - Install agent dependencies
- `task agent:fmt` - Format agent code with ruff
- `task agent:check` - Check agent code quality
- `task agent:test:unit` - Run unit tests (no MCP server required)
- `task agent:test:integration` - Run integration tests (expects MCP server)

**New backend tasks for MCP server integration:**

- `task agent:test:with-server` - Run integration tests with auto-managed MCP server
- `task agent:verify` - Run verification script (manual server)
- `task agent:verify:with-server` - Run verification with auto-managed MCP server

## Helper Scripts

Created in `backend/scripts/`:

### 1. `run-agent-integration-tests.sh`

Automatically:

1. Starts MCP server in background
1. Waits for server to be ready (3 seconds)
1. Runs agent integration tests
1. Cleans up MCP server process (even if tests fail)

**Features:**

- Proper trap handling for cleanup on exit/interrupt
- PID tracking for reliable server shutdown
- Error checking for server startup

### 2. `run-agent-verification.sh`

Similar to integration test script but runs the verification script instead:

1. Starts MCP server
1. Runs `verify_dspy_agent.py` with auto-answer "y"
1. Cleans up server

## Usage

### Running Unit Tests

From backend directory:

```bash
task agent:test:unit
```

No MCP server required. Tests agent structure and configuration.

### Running Integration Tests

#### Option 1: Automated (Recommended)

```bash
task agent:test:with-server
```

The script will:

- Start MCP server automatically
- Run integration tests
- Clean up server afterwards

#### Option 2: Manual

Terminal 1 (start MCP server):

```bash
task mcp:dev
```

Terminal 2 (run tests):

```bash
task agent:test:integration
```

### Running Verification

#### Automated with Server:

```bash
task agent:verify:with-server
```

#### Manual (no server connection test):

```bash
export MCP_SERVICE_URL=http://localhost:8080
task agent:verify
```

### Running All Tests

```bash
task test
```

This runs:

- Django monolith tests
- MCP service tests
- Agent unit tests (integration tests excluded)

## Environment Variables

The following environment variables are set automatically by tasks:

- `MCP_SERVICE_URL=http://localhost:8080` - For agent tests and verification
- `BUCKET_NAME={{.DIAGRAMS_BUCKET}}` - For MCP server (defaults to "diagramik-diagrams")

## Script Details

### Process Management

Both scripts use proper bash process management:

```bash
# Start server in background
.venv/bin/python mcp_diagrams/server.py &
MCP_PID=$!

# Cleanup trap
cleanup() {
    if [ ! -z "$MCP_PID" ] && kill -0 $MCP_PID 2>/dev/null; then
        echo "Stopping MCP server (PID: $MCP_PID)..."
        kill $MCP_PID 2>/dev/null || true
        wait $MCP_PID 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM
```

This ensures the MCP server is always cleaned up, even if:

- Tests fail
- Script is interrupted (Ctrl+C)
- Script terminates for any reason

### Wait Time

Scripts wait 3 seconds for MCP server startup. This can be adjusted in the scripts if needed:

```bash
# In scripts/run-agent-integration-tests.sh or scripts/run-agent-verification.sh
sleep 3  # Adjust this value if needed
```

## Integration Test Issues

**Current Status:** Integration tests run but fail due to connection setup issues.

**Known Issues:**

1. Test fixtures try to call `agent._aggregator.initialize()` which doesn't exist
   - Should be `agent._aggregator.load_servers()`
1. Persistent connection manager not initialized properly in test context

**Fix Required:** Update test fixtures in `agent/tests/test_dspy_agent.py` to properly initialize connections.

**Verification:** The MCP server itself works correctly (starts, accepts connections, shuts down cleanly).

## Next Steps

To fully enable integration tests:

1. Fix test fixtures to properly initialize MCP connections
1. Ensure connection manager is set up before calling `load_servers()`
1. Test with actual diagram generation requests

## Example Workflow

Typical development workflow:

```bash
# 1. Install dependencies
task agent:sync

# 2. Make changes to agent code

# 3. Format code
task agent:fmt

# 4. Run unit tests (fast, no server needed)
task agent:test:unit

# 5. Run integration tests when ready (automated server)
task agent:test:with-server

# 6. Run full verification (optional)
task agent:verify:with-server
```

## Troubleshooting

### Port 8080 Already in Use

If you get "address already in use" error:

```bash
# Kill any process on port 8080
lsof -ti:8080 | xargs kill -9

# Then run tests again
task agent:test:with-server
```

### Server Takes Too Long to Start

If tests fail because server isn't ready:

Edit `backend/scripts/run-agent-integration-tests.sh` and increase wait time:

```bash
sleep 5  # Increase from 3 to 5 seconds
```

### Manual Cleanup

If server process doesn't get cleaned up:

```bash
# Find and kill MCP server
pkill -f "mcp_diagrams/server.py"
```
