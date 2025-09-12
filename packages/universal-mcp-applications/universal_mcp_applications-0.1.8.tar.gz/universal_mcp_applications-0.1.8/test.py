

import asyncio
from universal_mcp.agentr.registry import AgentrRegistry
from universal_mcp.tools import ToolFormat


async def main():
    registry = AgentrRegistry()
    tools = await registry.export_tools(["google_gemini__generate_image", "google_gemini__generate_audio"], format=ToolFormat.MCP)
    result = await registry.call_tool("google_gemini__generate_audio", {"prompt": "Hi there, how are you?"})
    print(result)

if __name__ == "__main__":
    asyncio.run(main())