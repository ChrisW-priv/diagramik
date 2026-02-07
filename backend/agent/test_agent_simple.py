"""Simple test script for the agent with debug output."""

import asyncio
from agent.agent import agent
from agent.exceptions import ClarificationNeeded


async def test():
    try:
        print("1. Starting test...", flush=True)
        result = await agent("Create a technical diagram with EC2 and RDS")
        print("2. Got result!", flush=True)
        print(f"Title: {result.diagram_title}", flush=True)
        print(f"URI: {result.media_uri}", flush=True)
        print("SUCCESS", flush=True)
    except ClarificationNeeded as e:
        print("Clarification needed", flush=True)
        print(str(e)[:500], flush=True)
    except Exception as e:
        print(f"Error: {type(e).__name__}", flush=True)
        print(str(e)[:500], flush=True)
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
