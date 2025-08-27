import os
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from agent_executor import GreetingAgentExecutor
from starlette.responses import JSONResponse
from a2a.server.tasks import TaskUpdater

def main():
    # Get port from environment variable (Azure App Service sets this)
    port = int(os.environ.get("PORT", 9999))
    
    # Get the base URL from environment or construct it
    base_url = os.environ.get("WEBSITE_HOSTNAME")
    if base_url:
        agent_url = f"https://{base_url}/"
    else:
        agent_url = f"http://localhost:{port}/"
    
    skill = AgentSkill(
        id="hello_world",
        name="Greet",
        description="Return a greeting",
        tags=["greeting", "hello", "world"],
        examples=["Hey", "Hello", "Hi"],
    )
    task_store=InMemoryTaskStore()

    agent_card = AgentCard(
        name="Greeting Agent",
        description="A simple agent that returns a greeting",
        url=agent_url,
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        skills=[skill],
        version="1.0.0",
        capabilities=AgentCapabilities(),
    )
    request_handler = DefaultRequestHandler(
        agent_executor=GreetingAgentExecutor(task_store=task_store),
        task_store=task_store,
    )
    server = A2AStarletteApplication(
        http_handler=request_handler,
        agent_card=agent_card,
    )
    app = server.build()  # This returns a Starlette app
    # ✅ Define the GET / route for platform health checks
    @app.route("/", methods=["GET"])
    async def root(request):
        return JSONResponse({"status": "OK"})
    uvicorn.run(app, host="0.0.0.0", port=port)
if __name__ == "__main__":
    main()