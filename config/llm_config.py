# config/llm_config.py
LLM_CONFIG = {
    "endpoint": "http://localhost:11434",  # Ollama default
    "model": "llama2",  # or your preferred model
    "api_key": None,  # if required
    "headers": {
        "Content-Type": "application/json"
    }
}

SELENIUM_CONFIG = {
    "default_browser": "chrome",
    "headless": False,
    "implicit_wait": 10,
    "page_load_timeout": 30,
    "window_size": "1920,1080"
}