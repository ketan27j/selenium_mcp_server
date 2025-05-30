from typing import Any, Dict, List
from mcp_client import SeleniumMCPClient

class LLMSeleniumIntegration:
    def __init__(self, llm_endpoint: str = "http://localhost:8000"):
        self.llm_endpoint = llm_endpoint
        self.mcp_client = SeleniumMCPClient()
        self.conversation_history = []
    
    async def initialize(self):
        """Initialize the integration"""
        success = await self.mcp_client.start_server()
        if not success:
            raise Exception("Failed to start MCP server")
        
        # Create system prompt with available tools
        tools_description = self._generate_tools_description()
        self.system_prompt = f"""
You are an AI assistant that can control web browsers through Selenium automation.
You have access to the following browser automation tools:

{tools_description}

When a user asks you to perform web automation tasks, use these tools to:
1. Start a browser session
2. Navigate to websites
3. Interact with web elements (click, type, etc.)
4. Extract information from pages
5. Take screenshots when needed

Always provide clear feedback about what actions you're taking and their results.
"""
    
    def _generate_tools_description(self) -> str:
        """Generate description of available tools for LLM"""
        descriptions = []
        for tool in self.mcp_client.available_tools:
            desc = f"- {tool['name']}: {tool['description']}"
            if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
                params = list(tool['inputSchema']['properties'].keys())
                desc += f" (Parameters: {', '.join(params)})"
            descriptions.append(desc)
        return "\n".join(descriptions)
    
    async def process_user_request(self, user_input: str) -> str:
        """Process user request through LLM and execute Selenium actions"""
        # Add user input to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Send to LLM (you'll need to implement this based on your LLM API)
        llm_response = await self._query_llm(user_input)
        
        # Parse LLM response for tool calls
        actions = self._parse_actions_from_response(llm_response)
        
        # Execute actions through MCP
        execution_results = []
        for action in actions:
            result = await self.mcp_client.call_tool(action['tool'], action['arguments'])
            execution_results.append(f"{action['tool']}: {result}")
        
        # Combine results
        final_response = llm_response
        if execution_results:
            final_response += "\n\nExecution Results:\n" + "\n".join(execution_results)
        
        self.conversation_history.append({"role": "assistant", "content": final_response})
        return final_response
    
    async def _query_llm(self, prompt: str) -> str:
        """Query your on-premises LLM"""
        # Implement this based on your LLM's API
        # This is a placeholder - adapt to your specific LLM
        import aiohttp
        
        payload = {
            "messages": [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history,
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.llm_endpoint}/v1/chat/completions", 
                                   json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Error querying LLM: {response.status}"
    
    def _parse_actions_from_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response"""
        # This is a simplified parser - you might want to use a more sophisticated
        # approach like structured output or function calling
        actions = []
        
        # Look for tool call patterns in the response
        import re
        tool_pattern = r"TOOL_CALL:\s*(\w+)\s*\((.*?)\)"
        matches = re.findall(tool_pattern, response)
        
        for tool_name, args_str in matches:
            try:
                # Parse arguments (this is simplified - adapt as needed)
                args = eval(f"dict({args_str})")  # Be careful with eval in production
                actions.append({"tool": tool_name, "arguments": args})
            except:
                print(f"Could not parse arguments for {tool_name}: {args_str}")
        
        return actions
    
    async def cleanup(self):
        """Clean up resources"""
        await self.mcp_client.stop_server()