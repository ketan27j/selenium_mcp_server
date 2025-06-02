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
            # Start server process with additional error checking
            self.server_process = subprocess.Popen(
                ["python3", "selenium_mcp_server.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Check if process started successfully
            if self.server_process.poll() is not None:
                stderr = self.server_process.stderr.read()
                logger.error(f"Server failed to start: {stderr}")
                return False
                
            # Initialize connection with timeout
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
            response = await self._receive_message(timeout=10.0)  # 10 second timeout
            
            if response and "result" in response:
                logger.info("MCP Server initialized successfully")
                await self._list_tools()
                return True
            else:
                logger.error(f"Failed to initialize server: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            if self.server_process:
                self.server_process.terminate()
                self.server_process = None
            return False
    
    async def _send_message(self, message: Dict[str, Any]):
        """Send message to MCP server"""
        if self.server_process and self.server_process.stdin:
            message_str = json.dumps(message) + "\n"
            self.server_process.stdin.write(message_str)
            self.server_process.stdin.flush()
    
    async def _receive_message(self, timeout: float = 5.0) -> Optional[Dict[str, Any]]:
        """Receive message from MCP server with timeout"""
        if self.server_process and self.server_process.stdout:
            try:
                # Create an async task for reading
                loop = asyncio.get_event_loop()
                read_task = loop.run_in_executor(
                    None, 
                    self.server_process.stdout.readline
                )
                
                # Wait for response with timeout
                line = await asyncio.wait_for(read_task, timeout=timeout)
                line = line.strip()
                
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}, raw line: {line}")
                        return None
                
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for server response")
                return None
            except Exception as e:
                logger.error(f"Error reading from server: {e}")
                return None
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


