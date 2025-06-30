import asyncio
import pytest
import sys
import os
import json
from unittest.mock import Mock, AsyncMock, patch

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from selenium_mcp_server import SeleniumMCPServer
import mcp.types as types

class TestSeleniumMCPServer:
    """Test cases for SeleniumMCPServer with assertions"""
    
    @pytest.fixture
    async def server(self):
        """Create a server instance for testing"""
        server = SeleniumMCPServer()
        yield server
        # Cleanup
        if server.driver:
            await server._close_browser()
    
    @pytest.mark.asyncio
    async def test_start_browser_chrome_success(self, server):
        """Test successful Chrome browser startup"""
        with patch('selenium_mcp_server.webdriver.Chrome') as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver
            
            result = await server._start_browser(browser="chrome", headless=True)
            
            # Assertions
            assert len(result) == 1
            assert isinstance(result[0], types.TextContent)
            assert "Browser chrome started successfully" in result[0].text
            assert server.driver == mock_driver
            mock_chrome.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_browser_firefox_success(self, server):
        """Test successful Firefox browser startup"""
        with patch('selenium_mcp_server.webdriver.Firefox') as mock_firefox:
            mock_driver = Mock()
            mock_firefox.return_value = mock_driver
            
            result = await server._start_browser(browser="firefox", headless=False)
            
            # Assertions
            assert len(result) == 1
            assert "Browser firefox started successfully" in result[0].text
            assert server.driver == mock_driver
            mock_firefox.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_navigate_to_success(self, server):
        """Test successful navigation"""
        # Setup mock driver
        mock_driver = Mock()
        server.driver = mock_driver
        
        test_url = "https://example.com"
        result = await server._navigate_to(url=test_url)
        
        # Assertions
        assert len(result) == 1
        assert f"Navigated to {test_url}" in result[0].text
        mock_driver.get.assert_called_once_with(test_url)
    
    @pytest.mark.asyncio
    async def test_navigate_to_no_browser(self, server):
        """Test navigation without browser started"""
        result = await server._navigate_to(url="https://example.com")
        
        # Assertions
        assert len(result) == 1
        assert "Browser not started" in result[0].text
    
    @pytest.mark.asyncio
    async def test_find_element_success(self, server):
        """Test successful element finding"""
        # Setup mocks
        mock_element = Mock()
        mock_element.tag_name = "button"
        mock_element.text = "Click me"
        mock_element.is_enabled.return_value = True
        mock_element.is_displayed.return_value = True
        
        mock_wait = Mock()
        mock_wait.until.return_value = mock_element
        
        server.driver = Mock()
        server.wait = mock_wait
        
        with patch('selenium_mcp_server.WebDriverWait', return_value=mock_wait):
            result = await server._find_element(locator="button", locator_type="css")
        
        # Assertions
        assert len(result) == 1
        response_data = json.loads(result[0].text.replace("Element found: ", ""))
        assert response_data["found"] == True
        assert response_data["tag_name"] == "button"
        assert response_data["text"] == "Click me"
        assert response_data["enabled"] == True
        assert response_data["displayed"] == True
    
    @pytest.mark.asyncio
    async def test_click_element_success(self, server):
        """Test successful element clicking"""
        # Setup mocks
        mock_element = Mock()
        mock_wait = Mock()
        mock_wait.until.return_value = mock_element
        
        server.driver = Mock()
        
        with patch('selenium_mcp_server.WebDriverWait', return_value=mock_wait):
            result = await server._click_element(locator="#submit-btn", locator_type="css")
        
        # Assertions
        assert len(result) == 1
        assert "Element clicked successfully" in result[0].text
        mock_element.click.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_type_text_success(self, server):
        """Test successful text typing"""
        # Setup mocks
        mock_element = Mock()
        mock_driver = Mock()
        mock_driver.find_element.return_value = mock_element
        server.driver = mock_driver
        
        test_text = "Hello World"
        result = await server._type_text(locator="#input-field", text=test_text, clear_first=True)
        
        # Assertions
        assert len(result) == 1
        assert f"Typed text: {test_text}" in result[0].text
        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with(test_text)
    
    @pytest.mark.asyncio
    async def test_get_text_success(self, server):
        """Test successful text retrieval"""
        # Setup mocks
        expected_text = "Sample text content"
        mock_element = Mock()
        mock_element.text = expected_text
        mock_driver = Mock()
        mock_driver.find_element.return_value = mock_element
        server.driver = mock_driver
        
        result = await server._get_text(locator=".content", locator_type="css")
        
        # Assertions
        assert len(result) == 1
        assert f"Element text: {expected_text}" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_page_info_success(self, server):
        """Test successful page info retrieval"""
        # Setup mocks
        expected_title = "Test Page"
        expected_url = "https://test.example.com"
        expected_size = {"width": 1920, "height": 1080}
        
        mock_driver = Mock()
        mock_driver.title = expected_title
        mock_driver.current_url = expected_url
        mock_driver.get_window_size.return_value = expected_size
        server.driver = mock_driver
        
        result = await server._get_page_info()
        
        # Assertions
        assert len(result) == 1
        page_info = json.loads(result[0].text.replace("Page info: ", ""))
        assert page_info["title"] == expected_title
        assert page_info["url"] == expected_url
        assert page_info["window_size"] == expected_size
    
    @pytest.mark.asyncio
    async def test_execute_script_success(self, server):
        """Test successful JavaScript execution"""
        # Setup mocks
        expected_result = "Script executed successfully"
        mock_driver = Mock()
        mock_driver.execute_script.return_value = expected_result
        server.driver = mock_driver
        
        test_script = "return document.title;"
        result = await server._execute_script(script=test_script)
        
        # Assertions
        assert len(result) == 1
        assert f"Script executed. Result: {expected_result}" in result[0].text
        mock_driver.execute_script.assert_called_once_with(test_script)
    
    @pytest.mark.asyncio
    async def test_get_element_xpath_success(self, server):
        """Test successful XPath generation"""
        # Setup mocks
        mock_element = Mock()
        mock_element.tag_name = "button"
        mock_element.text = "Submit"
        mock_element.get_attribute.side_effect = lambda attr: {
            "id": "submit-btn",
            "class": "btn btn-primary",
            "name": ""
        }.get(attr, "")
        
        mock_wait = Mock()
        mock_wait.until.return_value = mock_element
        
        mock_driver = Mock()
        mock_driver.find_element.return_value = mock_element
        mock_driver.execute_script.return_value = '//*[@id="submit-btn"]'
        
        server.driver = mock_driver
        
        with patch('selenium_mcp_server.WebDriverWait', return_value=mock_wait):
            result = await server._get_element_xpath(
                locator="button", 
                locator_type="css", 
                xpath_type="smart"
            )
        
        # Assertions
        assert len(result) == 1
        response_text = result[0].text
        assert "XPath Generated:" in response_text
        
        # Parse the JSON response
        xpath_info = json.loads(response_text.replace("XPath Generated:\n", ""))
        assert xpath_info["original_locator"] == "css: button"
        assert xpath_info["generated_xpath"] == '//*[@id="submit-btn"]'
        assert xpath_info["xpath_type"] == "smart"
        assert xpath_info["element_info"]["tag_name"] == "button"
        assert xpath_info["element_info"]["id"] == "submit-btn"
    
    @pytest.mark.asyncio
    async def test_close_browser_success(self, server):
        """Test successful browser closure"""
        # Setup mock
        mock_driver = Mock()
        server.driver = mock_driver
        
        result = await server._close_browser()
        
        # Assertions
        assert len(result) == 1
        assert "Browser closed successfully" in result[0].text
        assert server.driver is None
        assert server.wait is None
        mock_driver.quit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, server):
        """Test error handling in various scenarios"""
        # Test navigation error
        mock_driver = Mock()
        mock_driver.get.side_effect = Exception("Navigation failed")
        server.driver = mock_driver
        
        result = await server._navigate_to(url="invalid-url")
        
        # Assertions
        assert len(result) == 1
        assert "Navigation failed" in result[0].text
    
    def test_get_by_locator_mapping(self, server):
        """Test locator type mapping"""
        from selenium.webdriver.common.by import By
        
        # Test various locator types
        test_cases = [
            ("css", "#test", By.CSS_SELECTOR),
            ("xpath", "//div[@id='test']", By.XPATH),
            ("id", "test-id", By.ID),
            ("name", "test-name", By.NAME),
            ("class", "test-class", By.CLASS_NAME),
            ("tag", "div", By.TAG_NAME),
            ("link_text", "Click here", By.LINK_TEXT),
            ("partial_link_text", "Click", By.PARTIAL_LINK_TEXT)
        ]
        
        for locator_type, locator_value, expected_by in test_cases:
            by, loc = server._get_by_locator(locator_type, locator_value)
            assert by == expected_by
            assert loc == locator_value
