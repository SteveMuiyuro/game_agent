
import asyncio
import json
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams

MCP_URL = "https://frontiers-mcp.vercel.app/mcp"


async def inspect_tools():

    async with MCPServerStreamableHttp(
        name="frontiers",
        params=MCPServerStreamableHttpParams(url=MCP_URL),
    ) as mcp_server:

        tools = await mcp_server.list_tools()

        print("\n===== MCP TOOLS DISCOVERY =====\n")

        for tool in tools:

            print(f"Tool Name: {tool.name}")
            print(f"Description: {tool.description}\n")

            schema = tool.inputSchema or {}

            properties = schema.get("properties", {})
            required = schema.get("required", [])

            if not properties:
                print("Parameters: None\n")
            else:
                print("Parameters:")

                for param, details in properties.items():
                    param_type = details.get("type", "unknown")
                    param_desc = details.get("description", "")

                    required_flag = " (REQUIRED)" if param in required else ""

                    print(f"  - {param}: {param_type}{required_flag}")

                    if param_desc:
                        print(f"      description: {param_desc}")

                print()

            print("-" * 50)


if __name__ == "__main__":
    asyncio.run(inspect_tools())

