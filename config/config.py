
import json
import os
from typing import Dict, Any

class MCPConfig:
    def __init__(self):
        self.config = {
            "mcpServers": {
                "selenium-automation": {
                    "command": "python",
                    "args": ["selenium_mcp_server.py"],
                    "env": {
                        "DISPLAY": ":99",  # For headless display if needed
                        "SELENIUM_BROWSER": "chrome"
                    }
                }
            }
        }
    
    def save_config(self, path: str = "mcp_config.json"):
        """Save MCP configuration to file"""
        with open(path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_config(self, path: str = "mcp_config.json"):
        """Load MCP configuration from file"""
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.config = json.load(f)
        return self.config