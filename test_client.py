import uuid
import asyncio
from datetime import datetime

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    GetTaskRequest,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    TaskQueryParams,
    TextPart,
    TaskState,
)

PUBLIC_AGENT_CARD_PATH = "/.well-known/agent_card.json"
BASE_URL = "http://localhost:9999"


async def check_task_status(client: A2AClient, task_id: str) -> tuple[TaskState, str | None]:
    """Check the status of a task and return the state and result if completed"""
    try:
        # Create proper GetTaskRequest
        query_params = TaskQueryParams(id=task_id)
        request = GetTaskRequest(
            id=str(uuid.uuid4()),
            params=query_params
        )
        response = await client.get_task(request)
        
        # Check if response is an error or success
        if hasattr(response.root, 'error'):
            # This is an error response
            error = response.root.error
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Task error: {error}")
            return TaskState.failed, None
        elif hasattr(response.root, 'result'):
            # This is a success response
            task = response.root.result
            return task.status.state, task.status.message
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Unknown response type: {type(response.root)}")
            return TaskState.failed, None
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error checking task status: {e}")
        return TaskState.failed, None

async def main() -> None:
    async with httpx.AsyncClient() as httpx_client:
        # Initialize A2ACardResolver
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=BASE_URL,
        )

        final_agent_card_to_use: AgentCard | None = None

        try:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] Fetching public agent card from: {BASE_URL}{PUBLIC_AGENT_CARD_PATH}"
            )
            _public_card = await resolver.get_agent_card()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetched public agent card")
            print(_public_card.model_dump_json(indent=2))

            final_agent_card_to_use = _public_card

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error fetching public agent card: {e}")
            raise RuntimeError("Failed to fetch public agent card")

        client = A2AClient(
            httpx_client=httpx_client, agent_card=final_agent_card_to_use
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] A2AClient initialized")

        # Generate IDs beforehand
        request_id = str(uuid.uuid4())
        context_id = str(uuid.uuid4())
        message_id = str(uuid.uuid4())
        
        # Submit the task using proper Message structure (don't set taskId, let framework generate it)
        message_payload = Message(
            role=Role.user,
            messageId=message_id,
            contextId=context_id,  # Set the context ID in the message
            parts=[Part(root=TextPart(text="Hello, please process this greeting task!"))],
        )
        
        # Create MessageSendParams with the message and configure for non-blocking execution
        from a2a.types import MessageSendConfiguration
        
        message_send_params = MessageSendParams(
            message=message_payload,
            configuration=MessageSendConfiguration(
                blocking=False  # Enable non-blocking execution for background processing
            )
        )
        
        # Use a request ID for JSON-RPC tracking
        request = SendMessageRequest(
            id=request_id,
            params=message_send_params,
        )
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Submitting task...")

        response = await client.send_message(request)
        
        # Extract the actual task ID from the response
        if hasattr(response.root, 'result') and hasattr(response.root.result, 'id'):
            task_id = response.root.result.id
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Task submitted successfully! Task ID: {task_id}")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to get task ID from response")
            print(response.model_dump_json(indent=2))
            return
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Initial response:")
        print(response.model_dump_json(indent=2))
        
        # Poll for task completion every 10 seconds instead of 1 minute
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting to poll for task completion every 5 seconds...")
        
        while True:
            await asyncio.sleep(5)  # Wait 10 seconds
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking task status...")
            
            try:
                # Get task status using proper GetTaskRequest
                query_params = TaskQueryParams(id=task_id)
                request = GetTaskRequest(
                    id=str(uuid.uuid4()),
                    params=query_params
                )
                response = await client.get_task(request)
                
                # Check if response is an error or success
                if hasattr(response.root, 'error'):
                    # This is an error response
                    error = response.root.error
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Task error: {error}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Will retry in 5 seconds...")
                    continue
                elif hasattr(response.root, 'result'):
                    # This is a success response
                    task = response.root.result
                    current_state = task.status.state
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Unknown response type: {type(response.root)}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Will retry in 5 seconds...")
                    continue
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Task state: {current_state}")
                
                if current_state == TaskState.completed:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Task completed successfully!")
                    if task.status.message:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Task result:")
                        print(task.status.message.model_dump_json(indent=2))
                    break
                elif current_state == TaskState.failed:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Task failed!")
                    if task.status.message:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Error details:")
                        print(task.status.message.model_dump_json(indent=2))
                    break
                elif current_state == TaskState.working:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Task is still working, will check again in 10 seconds...")
                elif current_state == TaskState.submitted:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Task is submitted, waiting to start...")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Task state: {current_state}, continuing to poll...")
                    
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Error checking task status: {e}")
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Will retry in 10 seconds...")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
