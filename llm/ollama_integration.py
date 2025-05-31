import aiohttp
import json
import re
from typing import List, Dict, Any, Optional
from monitoring.logger_config import logger

class OllamaIntegration:
    def __init__(self, base_url="http://localhost:11434", model="qwen2.5-coder:latest"):
        self.base_url = base_url
        self.model = model
        self.system_prompt = """You are an expert web automation assistant. You can control browsers using Selenium through specific tool calls.

Available Selenium tools:
- start_browser(browser="chrome", headless=False, window_size="1920,1080")
- navigate_to(url="https://example.com")
- find_element(locator="css_selector", locator_type="css", timeout=10)
- click_element(locator="button.submit", locator_type="css", timeout=10)
- type_text(locator="input[name='search']", text="search query", locator_type="css", clear_first=True)
- get_text(locator="h1", locator_type="css")
- get_page_info()
- take_screenshot(filename="optional_name.png")
- execute_script(script="return document.title;")
- close_browser()

When users ask for web automation tasks, respond with:
1. A brief explanation of what you'll do
2. Tool calls in this exact format: TOOL_CALL: tool_name(param1="value1", param2="value2")

Example:
User: "Open Chrome and go to Google"
Response: I'll start a Chrome browser and navigate to Google for you.

TOOL_CALL: start_browser(browser="chrome", headless=False)
TOOL_CALL: navigate_to(url="https://www.google.com")
"""
    
    async def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if Ollama is running
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        models = await response.json()
                        model_names = [model['name'] for model in models.get('models', [])]
                        if self.model in model_names:
                            logger.info(f"Model {self.model} is available")
                            return True
                        else:
                            logger.warning(f"Model {self.model} not found. Available models: {model_names}")
                            return False
                    else:
                        logger.error(f"Ollama not responding: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error connecting to Ollama: {e}")
            return False
    
    async def pull_model_if_needed(self):
        """Pull the model if it's not available locally"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"name": self.model}
                async with session.post(f"{self.base_url}/api/pull", json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Successfully pulled model {self.model}")
                        return True
                    else:
                        logger.error(f"Failed to pull model: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False
    
    async def generate_response(self, user_request: str, context: str = "") -> str:
        """Generate response using Ollama with Qwen2.5-coder"""
        try:
            # Prepare the full prompt
            full_prompt = f"{self.system_prompt}\n\nContext: {context}\n\nUser: {user_request}\n\nAssistant:"
            
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40,
                    "num_predict": 1000
                }
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("response", "No response generated")
                    else:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from the LLM response"""
        tool_calls = []
        
        # Pattern to match TOOL_CALL: function_name(param1="value1", param2="value2")
        pattern = r'TOOL_CALL:\s*(\w+)\s*\((.*?)\)'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for tool_name, args_str in matches:
            try:
                # Parse the arguments string
                args = self._parse_function_args(args_str)
                tool_calls.append({
                    "tool": tool_name,
                    "arguments": args
                })
                logger.info(f"Parsed tool call: {tool_name} with args: {args}")
            except Exception as e:
                logger.warning(f"Could not parse tool call {tool_name}({args_str}): {e}")
        
        return tool_calls
    
    def _parse_function_args(self, args_str: str) -> Dict[str, Any]:
        """Parse function arguments from string format"""
        args = {}
        if not args_str.strip():
            return args
        
        # Handle simple key="value" format
        arg_pattern = r'(\w+)=(["\'])(.*?)\2'
        matches = re.findall(arg_pattern, args_str)
        
        for key, quote, value in matches:
            # Try to convert to appropriate type
            if value.lower() in ['true', 'false']:
                args[key] = value.lower() == 'true'
            elif value.isdigit():
                args[key] = int(value)
            elif self._is_float(value):
                args[key] = float(value)
            else:
                args[key] = value
        
        return args
    
    def _is_float(self, value: str) -> bool:
        """Check if string represents a float"""
        try:
            float(value)
            return True
        except ValueError:
            return False