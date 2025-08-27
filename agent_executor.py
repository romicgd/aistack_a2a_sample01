from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.utils import new_agent_text_message
from pydantic import BaseModel
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InvalidParamsError,
    Message,
    MessageSendConfiguration,
    MessageSendParams,
    Task,
    InternalError,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
import asyncio

class GreetingAgent(BaseModel):
    """Greeting agent that returns a greeting"""
    async def invoke(self) -> str:
        return "Hello There!"

class GreetingAgentExecutor(AgentExecutor):
    def __init__(self, task_store=None):
        """Initialize the executor with a reference to the task store"""
        super().__init__()
        self.task_store = task_store
        
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        print(f"[EXECUTOR] Execute method called!")
        print(f"[EXECUTOR] Context: {context}")
        print(f"[EXECUTOR] Event queue: {event_queue}")
        
        try:
            if not context.task_id or not context.context_id:
                print(f"[EXECUTOR] Missing task_id or context_id: task_id={context.task_id}, context_id={context.context_id}")
                raise ValueError("RequestContext must have task_id and context_id")
            if not context.message:
                print(f"[EXECUTOR] Missing message in context")
                raise ValueError("RequestContext must have a message")
            
            taskId = context.task_id
            print(f"[EXECUTOR] Processing task with ID: {taskId}")
            updater = TaskUpdater(event_queue, taskId, context.context_id)

            # Submit the task
            print(f"[EXECUTOR] Submitting task {taskId}...")
            await updater.submit()
            print(f"[EXECUTOR] Task {taskId} submitted successfully")
            
            # Try to retrieve the task after submission to verify it was created
            try:
                if self.task_store:
                    # Add a small delay to allow task to be stored
                    await asyncio.sleep(0.1)
                    retrieved_task = await self.task_store.get(taskId)
                    if retrieved_task:
                        print(f"[EXECUTOR] Task {taskId} successfully retrieved after submission: {retrieved_task.status.state}")
                    else:
                        print(f"[EXECUTOR] Task {taskId} not found in task store after delay")
                else:
                    print(f"[EXECUTOR] No task store reference available to verify task {taskId}")
                    
            except Exception as e:
                print(f"[EXECUTOR] Failed to retrieve task {taskId} after submission: {e}")
            
            # For non-blocking execution, we need to do the work here but allow the framework
            # to handle the queue lifecycle properly. The key is that this method should
            # complete all the work, but the framework will handle returning to client early
            # when blocking=False is configured.
            
            # Update task to working state
            print(f"[EXECUTOR] Processing task {taskId} (waiting 10 seconds)...")
            print(f"[EXECUTOR] Updating task {taskId} to working state")
            await asyncio.sleep(10)  # 5 seconds for faster testing
            await updater.update_status(TaskState.working)
            print(f"[EXECUTOR] Task {taskId} updated to working state")
            
            # Process the actual task (reduced delay for faster testing)
            print(f"[EXECUTOR] Processing task {taskId} (waiting 10 seconds)...")
            
            # Invoke the greeting agent
            print(f"[EXECUTOR] Invoking greeting agent for task {taskId}")
            agent = GreetingAgent()
            result = await agent.invoke()
            print(f"[EXECUTOR] Agent result for task {taskId}: {result}")
            
            await asyncio.sleep(10)  # 5 seconds for faster testing
            # Send the result and mark task as completed
            print(f"[EXECUTOR] Updating task {taskId} to completed state")
            await updater.update_status(
                TaskState.completed,
                message=updater.new_agent_message([
                    Part(root=TextPart(text=result))
                ]),
                final=True
            )
            print(f"[EXECUTOR] Task {taskId} completed successfully")
            
            # Return - the A2A framework will handle queue cleanup after all events are processed
            print(f"[EXECUTOR] Returning from execute method for task {taskId}")
            return
            
        except Exception as e:
            # Handle all other exceptions
            error_msg = f"An error occurred while processing the request: {str(e)}"
            
            if 'updater' in locals():
                # Update task to failed state with detailed error message
                await updater.update_status(
                    TaskState.failed,
                    message=updater.new_agent_message([
                        Part(root=TextPart(
                            text=f"Task failed: {error_msg}\n\nPlease try again or contact support if the issue persists.",
                            metadata={"error_type": type(e).__name__}
                        ))
                    ]),
                    final=True
                )
                # Return gracefully - error already sent through updater
                return
            else:
                # Only raise ServerError if we couldn't create an updater
                # This happens when context validation fails early
                if context and context.task_id and context.context_id:
                    try:
                        temp_updater = TaskUpdater(event_queue, context.task_id, context.context_id)
                        await temp_updater.update_status(
                            TaskState.failed,
                            message=temp_updater.new_agent_message([
                                Part(root=TextPart(text=f"Task failed during initialization: {error_msg}"))
                            ]),
                            final=True
                        )
                        return  # Error sent through temp updater
                    except:
                        pass  # Fall through to raise ServerError
                
                # Only raise if we absolutely couldn't send error through updater
                raise ServerError(error=InternalError(message=error_msg)) from e
    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise Exception("Cancel not supported")