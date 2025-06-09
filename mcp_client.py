import os
import asyncio
import json
import subprocess
from typing import List, Dict, Any, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from monitoring.logger_config import logger

class SeleniumMCPClient:
    def __init__(self, server_path: Optional[str] = "./selenium_mcp_server.py"):
        self.server_process: Optional[subprocess.Popen] = None
        self.session: Optional[ClientSession] = None
        self.available_tools: List[Dict[str, Any]] = []
        self._stdio_context = None
        self.exit_stack = None
        self.server_path = server_path
        self.stdio = None
        self.write = None
        self._initialized = False
    
    async def start_server(self):
        """Start the Selenium MCP server"""
        try:
            if self._initialized:
                logger.warning("Server already initialized")
                return True
                
            # Create a new exit stack for this session
            self.exit_stack = AsyncExitStack()
            
            server_params = StdioServerParameters(
                command="python3",
                args=[self.server_path],
            )
            
            logger.info("Creating stdio client...")
            
            # Create and enter the stdio context
            self._stdio_context = stdio_client(server_params)
            stdio_transport = await self.exit_stack.enter_async_context(self._stdio_context)
            self.stdio, self.write = stdio_transport

            logger.info("Initializing session...")
            
            # Create and initialize the session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            
            # Initialize with timeout
            try:
                await asyncio.wait_for(self.session.initialize(), timeout=10.0)
                logger.info("Session initialized successfully")
            except asyncio.TimeoutError:
                logger.error("Session initialization timed out")
                await self.cleanup()
                return False
            
            # List available tools
            try:
                response = await self.session.list_tools()
                self.available_tools = [
                    {
                        'name': tool.name,
                        'description': tool.description,
                        'inputSchema': tool.inputSchema
                    }
                    for tool in response.tools
                ]
                
                tool_names = [tool['name'] for tool in self.available_tools]
                logger.info(f"Connected to server with tools: {tool_names}")
                
                self._initialized = True
                return True
                
            except Exception as e:
                logger.error(f"Failed to list tools: {e}")
                await self.cleanup()
                return False

        except Exception as e:
            logger.error(f"Error starting server: {e}")
            await self.cleanup()
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        if not self.session or not self._initialized:
            return {"error": "MCP server not initialized"}
        
        try:
            response = await self.session.call_tool(tool_name, arguments)
            return {
                "content": [
                    {"text": content.text if hasattr(content, 'text') else str(content)}
                    for content in response.content
                ]
            }
        except Exception as e:
            logger.error(f"Tool call failed for {tool_name}: {e}")
            return {"error": f"Tool call failed: {str(e)}"}
    
    async def cleanup(self):
        """Properly cleanup all resources"""
        if not self._initialized and not self.exit_stack:
            return
            
        try:
            logger.info("Starting cleanup...")
            
            # Mark as not initialized to prevent further operations
            self._initialized = False
            
            # Clean up session first
            if self.session:
                try:
                    await self.session.shutdown()
                except Exception as e:
                    logger.warning(f"Error shutting down session: {e}")
                finally:
                    self.session = None
            
            # Clean up exit stack (this will close stdio connections)
            if self.exit_stack:
                try:
                    await self.exit_stack.aclose()
                except Exception as e:
                    logger.warning(f"Error closing exit stack: {e}")
                finally:
                    self.exit_stack = None
            
            # Reset other attributes
            self.stdio = None
            self.write = None
            self._stdio_context = None
            self.available_tools = []
            
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            # Force reset everything even if cleanup fails
            self._initialized = False
            self.session = None
            self.exit_stack = None
            self.stdio = None
            self.write = None
            self._stdio_context = None
            self.available_tools = []

    async def __aenter__(self):
        """Async context manager entry"""
        success = await self.start_server()
        if not success:
            raise Exception("Failed to start MCP server")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

    def __del__(self):
        """Destructor to ensure cleanup"""
        if self._initialized or self.exit_stack:
            logger.warning("SeleniumMCPClient was not properly cleaned up")