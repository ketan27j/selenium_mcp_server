#!/usr/bin/env python3
import subprocess
import json
import time

def test_mcp_server():
    # Start server
    process = subprocess.Popen(
        ["python3", "selenium_mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    time.sleep(1)  # Let server start
    
    # Send initialize message
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    
    print(f"Sending: {json.dumps(init_msg)}")
    process.stdin.write(json.dumps(init_msg) + "\n")
    process.stdin.flush()
    
    # Read response
    response = process.stdout.readline()
    print(f"Init response: {response.strip()}")
    
    # Send tools/list
    tools_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list"
    }
    
    print(f"Sending: {json.dumps(tools_msg)}")
    process.stdin.write(json.dumps(tools_msg) + "\n")
    process.stdin.flush()
    
    # Read response
    response = process.stdout.readline()
    print(f"Tools response: {response.strip()}")
    
    # Check for errors
    process.poll()
    if process.returncode is not None:
        stderr_output = process.stderr.read()
        print(f"Server errors: {stderr_output}")
    
    process.terminate()

if __name__ == "__main__":
    test_mcp_server()
