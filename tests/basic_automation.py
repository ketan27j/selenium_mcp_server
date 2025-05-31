import asyncio
import sys
import os
# Add the parent directory to Python path to import selenium_mcp_server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from llm.llm_integration import LLMSeleniumIntegration

# example_usage.py - Example of how to use the integration
async def main():
    # Initialize the integration
    integration = LLMSeleniumIntegration("http://localhost:11434")  # Your LLM endpoint
    await integration.initialize()
    
    try:
        # Example interaction
        response = await integration.process_user_request(
            "Open a browser, go to solalerter.cryptoconsulting.tech, and take a screenshot"
        )
        print("Response:", response)
        
        # Another example
        response = await integration.process_user_request(
            "Click on the 'More information...' link and get the page title"
        )
        print("Response:", response)
        
    finally:
        await integration.cleanup()

if __name__ == "__main__":
    asyncio.run(main())