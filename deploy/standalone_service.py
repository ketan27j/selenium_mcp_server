# deploy/standalone_service.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from llm.llm_integration import LLMSeleniumIntegration

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.selenium_integration = LLMSeleniumIntegration()
    await app.state.selenium_integration.initialize()
    yield
    # Shutdown
    await app.state.selenium_integration.cleanup()

app = FastAPI(lifespan=lifespan)

@app.post("/automate")
async def automate_task(request: dict):
    user_request = request.get("task", "")
    result = await app.state.selenium_integration.process_user_request(user_request)
    return {"result": result}