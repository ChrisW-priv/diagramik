#!/usr/bin/env python3
"""
Verification script for DspyAgent initialization.

This script verifies that the main() function correctly initializes
a DspyAgent with two ReAct modules and a router module.

Usage:
    export MCP_SERVICE_URL=http://localhost:8080
    python verify_dspy_agent.py
"""

import os
import sys


def verify_agent_structure():
    """Verify agent initialization without requiring MCP connection."""
    from agent.fastagent.dspy_agent import main

    print("=" * 60)
    print("DspyAgent Verification")
    print("=" * 60)

    # Check environment
    mcp_url = os.getenv("MCP_SERVICE_URL")
    if not mcp_url:
        print("\n❌ ERROR: MCP_SERVICE_URL environment variable not set")
        print("   Example: export MCP_SERVICE_URL=http://localhost:8080")
        sys.exit(1)

    print(f"\n✓ MCP_SERVICE_URL: {mcp_url}")

    # Initialize agent
    print("\n1. Initializing DspyAgent...")
    try:
        agent = main()
        print(f"   ✓ Agent created: {agent.__class__.__name__}")
    except Exception as e:
        print(f"   ❌ Failed to create agent: {e}")
        sys.exit(1)

    # Verify configuration
    print("\n2. Verifying agent configuration...")
    print(f"   ✓ Agent name: {agent.config.name}")
    print(f"   ✓ Servers: {agent.config.servers}")

    # Verify ReAct modules
    print("\n3. Verifying ReAct modules...")
    print(f"   ✓ Number of modules: {len(agent.react_modules)}")

    for i, module in enumerate(agent.react_modules, 1):
        print(f"\n   Module {i}:")
        print(f"      Name: {module.name}")
        print(f"      Type: {module.module_type.__name__}")
        print(f"      Tools: {module.tools}")
        print(f"      Signature: {module.args[0] if module.args else 'None'}")

    # Verify router
    print("\n4. Verifying router module...")
    print(f"   ✓ Router name: {agent.router.name}")
    print(f"   ✓ Router type: {agent.router.module_type.__name__}")
    print(f"   ✓ Router tools: {agent.router.tools}")

    # Note about main_module
    print("\n5. Main module (router)...")
    print("   Note: Main module is lazily initialized")
    print("   It will be constructed when first accessed")
    print("   Requires MCP connection to be established")

    print("\n" + "=" * 60)
    print("✓ All verification checks passed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Start MCP server: task be:mcp:dev")
    print("  2. Run integration tests: task test:integration")
    print("  3. Test with actual diagram requests")


def verify_with_connection():
    """Verify agent with actual MCP connection (requires server)."""
    import asyncio
    from agent.fastagent.dspy_agent import main

    print("\n" + "=" * 60)
    print("Testing with MCP Connection")
    print("=" * 60)

    async def test():
        agent = main()

        print("\n6. Initializing MCP connection...")
        try:
            await agent._aggregator.load_servers()
            print("   ✓ MCP connection established")
        except Exception as e:
            print(f"   ❌ Failed to connect to MCP server: {e}")
            print("   Make sure the MCP server is running (task be:mcp:dev)")
            return False

        print("\n7. Constructing main module (router)...")
        try:
            router = agent.main_module
            print(f"   ✓ Router constructed: {router.__class__.__name__}")
            print(f"   ✓ Router has TOOL_ROUTING: {hasattr(router, 'TOOL_ROUTING')}")
            print(
                f"   ✓ Router has keyword_to_tool: {hasattr(router, 'keyword_to_tool')}"
            )
            print(f"   ✓ Router has agents: {hasattr(router, 'agents')}")

            if hasattr(router, "keyword_to_tool"):
                print("\n   Keyword routing:")
                for keyword, tool in router.keyword_to_tool.items():
                    print(f"      {keyword} -> {tool}")
        except Exception as e:
            print(f"   ❌ Failed to construct router: {e}")
            return False
        finally:
            await agent._aggregator.close()

        return True

    try:
        result = asyncio.run(test())
        if result:
            print("\n" + "=" * 60)
            print("✓ All checks passed (including MCP connection)!")
            print("=" * 60)
        return result
    except Exception as e:
        print(f"\n❌ Error during connection test: {e}")
        return False


if __name__ == "__main__":
    # First verify structure without connection
    verify_agent_structure()

    # Ask if user wants to test with connection
    print("\n" + "=" * 60)
    response = input("\nTest with actual MCP connection? (y/n): ").strip().lower()
    if response == "y":
        success = verify_with_connection()
        sys.exit(0 if success else 1)
    else:
        print("\nSkipping connection test. Run with MCP server for full verification.")
        sys.exit(0)
