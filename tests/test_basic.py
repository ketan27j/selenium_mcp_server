import asyncio
import sys
import os
# Add the parent directory to Python path to import selenium_mcp_server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from selenium_mcp_server import SeleniumMCPServer

async def test():
    server = SeleniumMCPServer()
    
    # Test browser start
    result = await server._start_browser(browser="chrome", headless=True)
    print("Browser start:", result[0].text)
    
    # Test navigation
    result = await server._navigate_to("https://solalerter.cryptoconsulting.tech")
    print("Navigation:", result[0].text)
    
    # Test screenshot
    result = await server._take_screenshot()
    print("Screenshot taken:", result[0].text)

    # Test element interaction
    result = await server._click_element(locator="button#sign-up")
    print("Element click:", result[0].text)

    # Test page info
    result = await server._get_page_info()
    print("Page info:", result[0].text)
    
    # Close browser
    result = await server._close_browser()
    print("Browser close:", result[0].text)

if __name__ == "__main__":
    asyncio.run(test())