import pytest
import asyncio
from selenium_mcp_server import SeleniumMCPServer

@pytest.mark.asyncio
async def test_browser_start():
    server = SeleniumMCPServer()
    result = await server._start_browser(browser="chrome", headless=True)
    assert "started successfully" in result[0].text
    await server._close_browser()

@pytest.mark.asyncio
async def test_navigation():
    server = SeleniumMCPServer()
    await server._start_browser(browser="chrome", headless=True)
    result = await server._navigate_to("https://httpbin.org")
    assert "Navigated to" in result[0].text
    await server._close_browser()

@pytest.mark.asyncio
async def test_element_interaction():
    server = SeleniumMCPServer()
    await server._start_browser(browser="chrome", headless=True)
    await server._navigate_to("https://httpbin.org/forms/post")
    
    # Test form filling
    result = await server._type_text("input[name='custname']", "Test User")
    assert "Typed text" in result[0].text
    
    await server._close_browser()