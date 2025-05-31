import asyncio
import json
import subprocess
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from monitoring.logger_config import logger

class SeleniumMCPClient:
    def __init__(self):
        self.server_process: Optional[subprocess.Popen] = None
        self.available_tools: List[Dict[str, Any]] = []
    
    async def start_server(self):
        """Start the Selenium MCP server"""
        try:
            self.server_process = subprocess.Popen(
                ["python", "selenium_mcp_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Initialize connection
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "selenium-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            await self._send_message(init_message)
            response = await self._receive_message()
            
            if response and "result" in response:
                print("MCP Server initialized successfully")
                logger.info("MCP Server initialized successfully")
                await self._list_tools()
                return True
            else:
                print(f"Failed to initialize server: {response}")
                return False
                
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send message to MCP server"""
        if self.server_process and self.server_process.stdin:
            message_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(message_str)
            self.server_process.stdin.flush()
    
    async def _receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from MCP server"""
        if self.server_process and self.server_process.stdout:
            try:
                line = self.server_process.stdout.readline().strip()
                if line:
                    return json.loads(line)
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {e}")
        return None
    
    async def _list_tools(self):
        """List available tools from the server"""
        message = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        await self._send_message(message)
        response = await self._receive_message()
        
        if response and "result" in response:
            self.available_tools = response["result"]["tools"]
            print(f"Available tools: {[tool['name'] for tool in self.available_tools]}")
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server"""
        message = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self._send_message(message)
        response = await self._receive_message()
        
        if response and "result" in response:
            return response["result"]
        else:
            return {"error": f"Tool call failed: {response}"}
    
    async def stop_server(self):
        """Stop the MCP server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None


