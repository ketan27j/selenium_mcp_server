# examples/form_automation.py
from llm.llm_integration import LLMSeleniumIntegration

async def form_filling_workflow():
    integration = LLMSeleniumIntegration()
    await integration.initialize()
    
    try:
        await integration.process_user_request("""
            Go to https://httpbin.org/forms/post
            Fill out the form with:
            - Customer name: John Doe
            - Telephone: 555-1234
            - Email: john@example.com
            - Pizza size: Large
            - Toppings: cheese, pepperoni
            Then submit the form and capture the result
        """)
        
    finally:
        await integration.cleanup()