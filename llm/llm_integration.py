from typing import Any, Dict, List
from mcp_client import SeleniumMCPClient
from llm.ollama_integration import OllamaIntegration
from monitoring.metrics import log_execution_time
from monitoring.logger_config import logger
import asyncio

class LLMSeleniumIntegration:
    def __init__(self, llm_endpoint: str = "http://localhost:11434", model: str = "qwen2.5-coder:latest"):
        self.llm_endpoint = llm_endpoint
        self.model = model
        self.mcp_client = SeleniumMCPClient()
        self.ollama = OllamaIntegration(base_url=llm_endpoint, model=model)
        self.conversation_history = []
        self.system_prompt = ""
        self._initialized = False
    
    async def initialize(self):
        """Initialize the integration"""
        if self._initialized:
            logger.warning("Integration already initialized")
            return
            
        try:
            logger.info("Initializing LLM Selenium Integration...")
            
            # Start MCP server
            logger.info("Starting MCP server...")
            success = await self.mcp_client.start_server()
            if not success:
                raise Exception("Failed to start MCP server")
            
            # Check Ollama connection
            logger.info("Checking Ollama connection...")
            ollama_ready = await self.ollama.check_ollama_connection()
            logger.info(f"Ollama connection status: {ollama_ready}")
            
            if not ollama_ready:
                logger.warning("Ollama model not available, attempting to pull...")
                await self.ollama.pull_model_if_needed()
                ollama_ready = await self.ollama.check_ollama_connection()
                if not ollama_ready:
                    raise Exception("Failed to connect to Ollama or model not available")
            
            # Create system prompt with available tools
            tools_description = self._generate_tools_description()
            logger.info(f"Available tools:\n{tools_description}")
            
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

Format your tool calls exactly like this:
TOOL_CALL: tool_name(param1="value1", param2="value2")

Example:
TOOL_CALL: start_browser(browser="chrome", headless=False)
TOOL_CALL: navigate_to(url="https://www.google.com")
"""
            
            self._initialized = True
            logger.info("LLM Selenium Integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize integration: {e}")
            await self.cleanup()
            raise
    
    def _generate_tools_description(self) -> str:
        """Generate description of available tools for LLM"""
        if not self.mcp_client.available_tools:
            return "No tools available"
            
        descriptions = []
        for tool in self.mcp_client.available_tools:
            desc = f"- {tool['name']}: {tool['description']}"
            if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
                params = list(tool['inputSchema']['properties'].keys())
                desc += f" (Parameters: {', '.join(params)})"
            descriptions.append(desc)
        return "\n".join(descriptions)
    
    async def process_user_request(self, user_input: str) -> str:
        """Process user request through Ollama LLM and execute Selenium actions"""
        if not self._initialized:
            return "Error: Integration not initialized. Please call initialize() first."
            
        try:
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Create context from conversation history
            context = self._build_context()
            
            # Generate response using Ollama
            llm_response = await self.ollama.generate_response(user_input, context)
            
            # Parse tool calls from LLM response
            tool_calls = self.ollama.parse_tool_calls(llm_response)
            
            # Execute tool calls through MCP
            execution_results = []
            for tool_call in tool_calls:
                logger.info(f"Executing tool: {tool_call['tool']} with args: {tool_call['arguments']}")
                
                # Add retry logic for tool calls
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        result = await self.mcp_client.call_tool(tool_call['tool'], tool_call['arguments'])
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            result = {"error": f"Tool call failed after {max_retries} attempts: {str(e)}"}
                        else:
                            logger.warning(f"Tool call attempt {attempt + 1} failed: {e}")
                            await asyncio.sleep(1)  # Wait before retry
                
                if 'content' in result and result['content']:
                    result_text = result['content'][0].get('text', str(result))
                else:
                    result_text = str(result)
                
                execution_results.append(f"✓ {tool_call['tool']}: {result_text}")
            
            # Combine LLM response with execution results
            if execution_results:
                final_response = f"{llm_response}\n\n**Execution Results:**\n" + "\n".join(execution_results)
            else:
                final_response = llm_response
            
            # Add to conversation history
            self.conversation_history.append({"role": "assistant", "content": final_response})
            
            return final_response
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _build_context(self) -> str:
        """Build context from conversation history"""
        context_parts = []
        for msg in self.conversation_history[-5:]:  # Last 5 messages for context
            role = msg['role'].title()
            content = msg['content'][:200] + "..." if len(msg['content']) > 200 else msg['content']
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def execute_automation_workflow(self, workflow_description: str) -> str:
        """Execute a complete automation workflow"""
        if not self._initialized:
            return "Error: Integration not initialized. Please call initialize() first."
            
        steps = [
            f"I need to execute this automation workflow: {workflow_description}",
            "Please break this down into steps and execute them."
        ]
        
        results = []
        for step in steps:
            result = await self.process_user_request(step)
            results.append(result)
        
        return "\n\n".join(results)
    
    async def cleanup(self):
        """Clean up resources"""
        if not self._initialized:
            return
            
        try:
            logger.info("Cleaning up LLM Selenium Integration...")
            self._initialized = False
            
            # Clean up MCP client
            if self.mcp_client:
                await self.mcp_client.cleanup()
            
            # Clear conversation history
            self.conversation_history.clear()
            
            logger.info("Cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()

# Example usage function with proper error handling
async def main():
    """Example usage of the integrated system with proper error handling"""
    
    # Use async context manager for proper cleanup
    try:
        async with LLMSeleniumIntegration() as integration:
            # Example automation requests
            requests = [
                "Start a Chrome browser and go to Google",
                "Search for 'selenium automation' on Google",
                "Take a screenshot of the results"
            ]
            
            for request in requests:
                print(f"\n🤖 User: {request}")
                response = await integration.process_user_request(request)
                print(f"🔧 Assistant: {response}")
                print("-" * 80)
                
    except Exception as e:
        logger.error(f"Error in main: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())