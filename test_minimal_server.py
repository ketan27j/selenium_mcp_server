#!/usr/bin/env python3
import asyncio
import logging
from typing import List
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent
import mcp.types as types

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test-server")

class MinimalMCPServer:
    def __init__(self):
        self.server = Server("test-server")
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            logger.info("list_tools called")
            return [
                Tool(
                    name="test_tool",
                    description="A test tool",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"}
                        }
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            logger.info(f"call_tool: {name} with {arguments}")
            return [types.TextContent(type="text", text=f"Called {name}")]

    async def run(self):
        from mcp.server.stdio import stdio_server
        
        logger.info("Starting minimal server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="test-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

def main():
    server = MinimalMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()
