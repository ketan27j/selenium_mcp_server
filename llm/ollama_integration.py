# ollama_integration.py
import aiohttp
import json

class OllamaIntegration:
    def __init__(self, base_url="http://localhost:11434"):
        self.base_url = base_url
        self.model = "llama2"
    
    async def generate_selenium_actions(self, user_request: str, context: str = ""):
        """Generate Selenium actions from user request"""
        prompt = f"""
You are a web automation expert. Convert the following user request into specific Selenium actions.

User Request: {user_request}
Context: {context}

Available Selenium MCP tools:
- start_browser(browser="chrome", headless=False)
- navigate_to(url="https://example.com")
- find_element(locator="css_selector", locator_type="css")
- click_element(locator="button.submit")
- type_text(locator="input[name='search']", text="search query")
- get_text(locator="h1")
- take_screenshot()
- close_browser()

Respond with a JSON array of actions to perform:
"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return json.loads(result["response"])
                else:
                    raise Exception(f"Ollama API error: {response.status}")