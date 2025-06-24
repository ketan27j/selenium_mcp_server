#!/usr/bin/env python3
"""
Custom Selenium MCP Server
Provides web automation capabilities through MCP protocol
"""

import asyncio
import json
import sys
import traceback
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urljoin, urlparse
from monitoring.logger_config import logger

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    logger.info("Selenium imports successful")
except ImportError as e:
    logger.error(f"Failed to import Selenium: {e}")
    sys.exit(1)

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.types import (
        Resource,
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
        LoggingLevel
    )
    import mcp.types as types
    logger.info("MCP imports successful")
except ImportError as e:
    logger.error(f"Failed to import MCP: {e}")
    sys.exit(1)

class SeleniumMCPServer:
    def __init__(self):
        logger.info("Initializing SeleniumMCPServer")
        try:
            self.server = Server("selenium-automation")
            self.driver: Optional[webdriver.Remote] = None
            self.wait: Optional[WebDriverWait] = None
            logger.info("Server initialized successfully")
            self.setup_handlers()
            logger.info("Handlers setup completed")
        except Exception as e:
            logger.error(f"Failed to initialize server: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        logger.info("Setting up handlers")
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available Selenium tools"""
            return [
                Tool(
                    name="start_browser",
                    description="Start a new browser session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "browser": {
                                "type": "string",
                                "enum": ["chrome", "firefox"],
                                "default": "chrome",
                                "description": "Browser to use"
                            },
                            "headless": {
                                "type": "boolean",
                                "default": True,
                                "description": "Run browser in headless mode"
                            },
                            "window_size": {
                                "type": "string",
                                "default": "1920,1080",
                                "description": "Browser window size (width,height)"
                            }
                        }
                    }
                ),
                Tool(
                    name="navigate_to",
                    description="Navigate to a URL",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to navigate to"
                            }
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="find_element",
                    description="Find an element on the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "locator": {
                                "type": "string",
                                "description": "CSS selector, XPath, or other locator"
                            },
                            "locator_type": {
                                "type": "string",
                                "enum": ["css", "xpath", "id", "name", "class", "tag", "link_text", "partial_link_text"],
                                "default": "css",
                                "description": "Type of locator"
                            },
                            "timeout": {
                                "type": "number",
                                "default": 10,
                                "description": "Timeout in seconds"
                            }
                        },
                        "required": ["locator"]
                    }
                ),
                Tool(
                    name="get_element_xpath",
                    description="Get the precise XPath of an element for reliable automation",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "locator": {
                                "type": "string",
                                "description": "Initial locator to find the element (CSS selector, XPath, etc.)"
                            },
                            "locator_type": {
                                "type": "string",
                                "enum": ["css", "xpath", "id", "name", "class", "tag", "link_text", "partial_link_text"],
                                "default": "css",
                                "description": "Type of locator"
                            },
                            "xpath_type": {
                                "type": "string",
                                "enum": ["absolute", "relative", "smart"],
                                "default": "smart",
                                "description": "Type of XPath to generate: absolute (full path), relative (shorter), or smart (optimized for stability)"
                            },
                            "timeout": {
                                "type": "number",
                                "default": 10,
                                "description": "Timeout in seconds"
                            }
                        },
                        "required": ["locator"]
                    }
                ),
                Tool(
                    name="click_element",
                    description="Click on an element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "locator": {
                                "type": "string",
                                "description": "Element locator"
                            },
                            "locator_type": {
                                "type": "string",
                                "enum": ["css", "xpath", "id", "name", "class", "tag", "link_text", "partial_link_text"],
                                "default": "css"
                            },
                            "timeout": {
                                "type": "number",
                                "default": 10
                            }
                        },
                        "required": ["locator"]
                    }
                ),
                Tool(
                    name="type_text",
                    description="Type text into an element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "locator": {
                                "type": "string",
                                "description": "Element locator"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text to type"
                            },
                            "locator_type": {
                                "type": "string",
                                "enum": ["css", "xpath", "id", "name", "class", "tag"],
                                "default": "css"
                            },
                            "clear_first": {
                                "type": "boolean",
                                "default": True,
                                "description": "Clear field before typing"
                            }
                        },
                        "required": ["locator", "text"]
                    }
                ),
                Tool(
                    name="get_text",
                    description="Get text content from an element",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "locator": {
                                "type": "string",
                                "description": "Element locator"
                            },
                            "locator_type": {
                                "type": "string",
                                "enum": ["css", "xpath", "id", "name", "class", "tag"],
                                "default": "css"
                            }
                        },
                        "required": ["locator"]
                    }
                ),
                Tool(
                    name="get_page_info",
                    description="Get current page information",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="take_screenshot",
                    description="Take a screenshot of the current page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Optional filename for screenshot"
                            }
                        }
                    }
                ),
                Tool(
                    name="execute_script",
                    description="Execute JavaScript on the page",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script": {
                                "type": "string",
                                "description": "JavaScript code to execute"
                            }
                        },
                        "required": ["script"]
                    }
                ),
                Tool(
                    name="close_browser",
                    description="Close the browser session",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
            """Handle tool calls"""
            try:
                if name == "start_browser":
                    return await self._start_browser(**arguments)
                elif name == "navigate_to":
                    return await self._navigate_to(**arguments)
                elif name == "find_element":
                    return await self._find_element(**arguments)
                elif name == "get_element_xpath":
                    return await self._get_element_xpath(**arguments)
                elif name == "click_element":
                    return await self._click_element(**arguments)
                elif name == "type_text":
                    return await self._type_text(**arguments)
                elif name == "get_text":
                    return await self._get_text(**arguments)
                elif name == "get_page_info":
                    return await self._get_page_info()
                elif name == "take_screenshot":
                    return await self._take_screenshot(**arguments)
                elif name == "execute_script":
                    return await self._execute_script(**arguments)
                elif name == "close_browser":
                    return await self._close_browser()
                else:
                    return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                logger.error(f"Error executing tool {name}: {str(e)}")
                logger.error(traceback.format_exc())
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

        # @self.server.request_handlers("tools/list")
        # async def handle_tools_list_request(request) -> List[Tool]:
        #     """Handle tools/list JSON-RPC request"""
        #     return await handle_list_tools()  # Reuse the existing function
        
    async def _start_browser(self, browser: str = "chrome", headless: bool = True, window_size: str = "1920,1080") -> List[types.TextContent]:
        """Start browser session"""
        logger.info(f"Starting browser: {browser}, headless: {headless}")
        try:
            if self.driver:
                self.driver.quit()
            
            if browser.lower() == "chrome":
                options = ChromeOptions()
                if headless:
                    options.add_argument("--headless")
                options.add_argument(f"--window-size={window_size}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                self.driver = webdriver.Chrome(options=options)
            elif browser.lower() == "firefox":
                options = FirefoxOptions()
                if headless:
                    options.headless = True
                width, height = window_size.split(",")
                self.driver = webdriver.Firefox(options=options)
                self.driver.set_window_size(int(width), int(height))
            
            self.wait = WebDriverWait(self.driver, 10)
            return [types.TextContent(type="text", text=f"Browser {browser} started successfully")]
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return [types.TextContent(type="text", text=f"Failed to start browser: {str(e)}")]

    async def _navigate_to(self, url: str) -> List[types.TextContent]:
        """Navigate to URL"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started. Use start_browser first.")]
        
        try:
            self.driver.get(url)
            return [types.TextContent(type="text", text=f"Navigated to {url}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Navigation failed: {str(e)}")]

    def _get_by_locator(self, locator_type: str, locator: str):
        """Get By object based on locator type"""
        locator_map = {
            "css": By.CSS_SELECTOR,
            "xpath": By.XPATH,
            "id": By.ID,
            "name": By.NAME,
            "class": By.CLASS_NAME,
            "tag": By.TAG_NAME,
            "link_text": By.LINK_TEXT,
            "partial_link_text": By.PARTIAL_LINK_TEXT
        }
        return locator_map.get(locator_type, By.CSS_SELECTOR), locator

    def _generate_xpath(self, element, xpath_type: str = "smart"):
        """Generate XPath for an element"""
        if xpath_type == "absolute":
            return self._get_absolute_xpath(element)
        elif xpath_type == "relative":
            return self._get_relative_xpath(element)
        else:  # smart
            return self._get_smart_xpath(element)

    def _get_absolute_xpath(self, element):
        """Generate absolute XPath (full path from root)"""
        script = """
        function getAbsoluteXPath(element) {
            var xpath = '';
            for (; element && element.nodeType == 1; element = element.parentNode) {
                var id = element.id;
                if (id) {
                    xpath = '//*[@id="' + id + '"]' + xpath;
                    break;
                }
                var tagName = element.tagName.toLowerCase();
                var siblings = element.parentNode ? element.parentNode.children : [];
                var sameTagSiblings = [];
                for (var i = 0; i < siblings.length; i++) {
                    if (siblings[i].tagName.toLowerCase() === tagName) {
                        sameTagSiblings.push(siblings[i]);
                    }
                }
                if (sameTagSiblings.length > 1) {
                    var index = sameTagSiblings.indexOf(element) + 1;
                    xpath = '/' + tagName + '[' + index + ']' + xpath;
                } else {
                    xpath = '/' + tagName + xpath;
                }
            }
            return xpath.startsWith('/') ? xpath : '/' + xpath;
        }
        return getAbsoluteXPath(arguments[0]);
        """
        return self.driver.execute_script(script, element)

    def _get_relative_xpath(self, element):
        """Generate relative XPath (shorter, context-aware)"""
        script = """
        function getRelativeXPath(element) {
            // Check for unique attributes first
            if (element.id) {
                return '//*[@id="' + element.id + '"]';
            }
            
            var className = element.className;
            if (className && typeof className === 'string') {
                var classes = className.trim().split(/\\s+/);
                for (var i = 0; i < classes.length; i++) {
                    var selector = '//*[@class="' + classes[i] + '"]';
                    var elements = document.evaluate(selector, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    if (elements.snapshotLength === 1) {
                        return selector;
                    }
                }
            }
            
            // Check for unique text content
            var textContent = element.textContent.trim();
            if (textContent && textContent.length < 50) {
                var selector = '//*[text()="' + textContent + '"]';
                var elements = document.evaluate(selector, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                if (elements.snapshotLength === 1) {
                    return selector;
                }
            }
            
            // Fall back to tag with attributes
            var xpath = '//' + element.tagName.toLowerCase();
            if (element.name) {
                xpath += '[@name="' + element.name + '"]';
            } else if (element.type) {
                xpath += '[@type="' + element.type + '"]';
            } else if (className) {
                xpath += '[@class="' + className + '"]';
            }
            
            return xpath;
        }
        return getRelativeXPath(arguments[0]);
        """
        return self.driver.execute_script(script, element)

    def _get_smart_xpath(self, element):
        """Generate smart XPath (optimized for stability and uniqueness)"""
        script = """
        function getSmartXPath(element) {
            // Priority 1: ID (most stable)
            if (element.id) {
                return '//*[@id="' + element.id + '"]';
            }
            
            // Priority 2: Data attributes (usually stable)
            var attributes = element.attributes;
            for (var i = 0; i < attributes.length; i++) {
                var attr = attributes[i];
                if (attr.name.startsWith('data-') && attr.value) {
                    var selector = '//*[@' + attr.name + '="' + attr.value + '"]';
                    var elements = document.evaluate(selector, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    if (elements.snapshotLength === 1) {
                        return selector;
                    }
                }
            }
            
            // Priority 3: Name attribute for form elements
            if (element.name && (element.tagName === 'INPUT' || element.tagName === 'SELECT' || element.tagName === 'TEXTAREA')) {
                var selector = '//' + element.tagName.toLowerCase() + '[@name="' + element.name + '"]';
                var elements = document.evaluate(selector, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                if (elements.snapshotLength === 1) {
                    return selector;
                }
            }
            
            // Priority 4: Unique class combinations
            var className = element.className;
            if (className && typeof className === 'string') {
                var classes = className.trim().split(/\\s+/);
                if (classes.length > 1) {
                    // Try combination of first two classes
                    var selector = '//*[contains(@class, "' + classes[0] + '") and contains(@class, "' + classes[1] + '")]';
                    var elements = document.evaluate(selector, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    if (elements.snapshotLength === 1) {
                        return selector;
                    }
                }
            }
            
            // Priority 5: Text content for clickable elements
            if (element.tagName === 'BUTTON' || element.tagName === 'A' || element.getAttribute('role') === 'button') {
                var textContent = element.textContent.trim();
                if (textContent && textContent.length < 50) {
                    var selector = '//' + element.tagName.toLowerCase() + '[normalize-space(text())="' + textContent + '"]';
                    var elements = document.evaluate(selector, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    if (elements.snapshotLength === 1) {
                        return selector;
                    }
                }
            }
            
            // Priority 6: Parent-child relationship with unique parent
            var parent = element.parentNode;
            if (parent && parent.id) {
                var tagName = element.tagName.toLowerCase();
                var siblings = parent.children;
                var sameTagSiblings = [];
                for (var i = 0; i < siblings.length; i++) {
                    if (siblings[i].tagName.toLowerCase() === tagName) {
                        sameTagSiblings.push(siblings[i]);
                    }
                }
                if (sameTagSiblings.length === 1) {
                    return '//*[@id="' + parent.id + '"]/' + tagName;
                } else {
                    var index = sameTagSiblings.indexOf(element) + 1;
                    return '//*[@id="' + parent.id + '"]/' + tagName + '[' + index + ']';
                }
            }
            
            // Fallback: position-based XPath
            var xpath = '';
            var current = element;
            while (current && current.nodeType === 1) {
                var tagName = current.tagName.toLowerCase();
                if (current.id) {
                    xpath = '//*[@id="' + current.id + '"]' + xpath;
                    break;
                }
                
                var parent = current.parentNode;
                if (parent) {
                    var siblings = [];
                    for (var i = 0; i < parent.children.length; i++) {
                        if (parent.children[i].tagName.toLowerCase() === tagName) {
                            siblings.push(parent.children[i]);
                        }
                    }
                    if (siblings.length > 1) {
                        var index = siblings.indexOf(current) + 1;
                        xpath = '/' + tagName + '[' + index + ']' + xpath;
                    } else {
                        xpath = '/' + tagName + xpath;
                    }
                }
                current = parent;
            }
            
            return xpath || '//' + element.tagName.toLowerCase();
        }
        return getSmartXPath(arguments[0]);
        """
        return self.driver.execute_script(script, element)

    async def _get_element_xpath(self, locator: str, locator_type: str = "css", xpath_type: str = "smart", timeout: int = 10) -> List[types.TextContent]:
        """Get precise XPath of an element"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started")]
        
        try:
            # First find the element using the provided locator
            by, loc = self._get_by_locator(locator_type, locator)
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, loc)))
            
            # Generate the requested type of XPath
            xpath = self._generate_xpath(element, xpath_type)
            
            # Verify the generated XPath works
            try:
                test_element = self.driver.find_element(By.XPATH, xpath)
                xpath_valid = test_element == element
            except:
                xpath_valid = False
            
            # Get element info for context
            element_info = {
                "original_locator": f"{locator_type}: {locator}",
                "generated_xpath": xpath,
                "xpath_type": xpath_type,
                "xpath_valid": xpath_valid,
                "element_info": {
                    "tag_name": element.tag_name,
                    "text": element.text[:100] + "..." if len(element.text) > 100 else element.text,
                    "id": element.get_attribute("id") or "",
                    "class": element.get_attribute("class") or "",
                    "name": element.get_attribute("name") or ""
                }
            }
            
            return [types.TextContent(type="text", text=f"XPath Generated:\n{json.dumps(element_info, indent=2)}")]
            
        except TimeoutException:
            return [types.TextContent(type="text", text=f"Element not found within {timeout} seconds using locator: {locator_type}={locator}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error generating XPath: {str(e)}")]

    async def _find_element(self, locator: str, locator_type: str = "css", timeout: int = 10) -> List[types.TextContent]:
        """Find element on page"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started")]
        
        try:
            by, loc = self._get_by_locator(locator_type, locator)
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, loc)))
            
            info = {
                "found": True,
                "tag_name": element.tag_name,
                "text": element.text[:100] + "..." if len(element.text) > 100 else element.text,
                "enabled": element.is_enabled(),
                "displayed": element.is_displayed()
            }
            return [types.TextContent(type="text", text=f"Element found: {json.dumps(info, indent=2)}")]
        except TimeoutException:
            return [types.TextContent(type="text", text=f"Element not found within {timeout} seconds")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Error finding element: {str(e)}")]

    async def _click_element(self, locator: str, locator_type: str = "css", timeout: int = 10) -> List[types.TextContent]:
        """Click element"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started")]
        
        try:
            by, loc = self._get_by_locator(locator_type, locator)
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((by, loc)))
            element.click()
            return [types.TextContent(type="text", text="Element clicked successfully")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Click failed: {str(e)}")]

    async def _type_text(self, locator: str, text: str, locator_type: str = "css", clear_first: bool = True) -> List[types.TextContent]:
        """Type text into element"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started")]
        
        try:
            by, loc = self._get_by_locator(locator_type, locator)
            element = self.driver.find_element(by, loc)
            
            if clear_first:
                element.clear()
            element.send_keys(text)
            return [types.TextContent(type="text", text=f"Typed text: {text}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Type failed: {str(e)}")]

    async def _get_text(self, locator: str, locator_type: str = "css") -> List[types.TextContent]:
        """Get text from element"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started")]
        
        try:
            by, loc = self._get_by_locator(locator_type, locator)
            element = self.driver.find_element(by, loc)
            text = element.text
            return [types.TextContent(type="text", text=f"Element text: {text}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get text failed: {str(e)}")]

    async def _get_page_info(self) -> List[types.TextContent]:
        """Get current page information"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started")]
        
        try:
            info = {
                "title": self.driver.title,
                "url": self.driver.current_url,
                "window_size": self.driver.get_window_size()
            }
            return [types.TextContent(type="text", text=f"Page info: {json.dumps(info, indent=2)}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Get page info failed: {str(e)}")]

    async def _take_screenshot(self, filename: Optional[str] = None) -> List[types.TextContent]:
        """Take screenshot"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started")]
        
        try:
            if not filename:
                filename = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
            
            self.driver.save_screenshot(filename)
            return [types.TextContent(type="text", text=f"Screenshot saved as {filename}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Screenshot failed: {str(e)}")]

    async def _execute_script(self, script: str) -> List[types.TextContent]:
        """Execute JavaScript"""
        if not self.driver:
            return [types.TextContent(type="text", text="Browser not started")]
        
        try:
            result = self.driver.execute_script(script)
            return [types.TextContent(type="text", text=f"Script executed. Result: {result}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Script execution failed: {str(e)}")]

    async def _close_browser(self) -> List[types.TextContent]:
        """Close browser"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.wait = None
                return [types.TextContent(type="text", text="Browser closed successfully")]
            except Exception as e:
                return [types.TextContent(type="text", text=f"Error closing browser: {str(e)}")]
        return [types.TextContent(type="text", text="No browser session to close")]

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting MCP server run")
        try:
            from mcp.server.stdio import stdio_server
            
            logger.info("Setting up stdio server")
            async with stdio_server() as (read_stream, write_stream):
                logger.info("Running server")
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="selenium-automation",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"Error in server run: {e}")
            logger.error(traceback.format_exc())
            raise

def main():
    """Main entry point"""
    logger.info("=== Starting Selenium MCP Server ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {sys.path}")
    try:
        server = SeleniumMCPServer()
        logger.info("Server created, starting run")
        asyncio.run(server.run())
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()