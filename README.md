# aistack_a2a_sample01


This project demonstrates a simple agent-to-agent (A2A) interaction using Python, with a focus on handling long-running agent tasks. It illustrates a pattern where:

- The client submits a task to the agent and receives an immediate response (such as a task ID or acknowledgment).
- The client then periodically checks (polls) the state of the task using the task ID.
- Once the task is completed, the client retrieves the results.

This approach allows the system to handle long-running operations asynchronously, ensuring that the client is not blocked while the agent processes the task.

## Project Structure

- `main.py` — Main entry point to start the agent system.
- `agent_executor.py` — Contains logic for executing agent actions.
- `test_client.py` — Script to test agent interactions.
- `requirements.txt` — Python dependencies for the project.


## Handling Long-Running Tasks (A2A Pattern)

1. **Task Submission:**
  - The client sends a request to the agent to start a long-running task.
  - The agent immediately returns a response (e.g., a task ID) to acknowledge receipt.

2. **Polling for Status:**
  - The client periodically checks the status of the task by querying the agent with the task ID.
  - The agent responds with the current state (e.g., pending, running, completed).

3. **Retrieving Results:**
  - Once the agent reports the task as completed, the client requests and receives the final results.

This pattern is useful for scalable, non-blocking agent systems where tasks may take significant time to complete.

### Prerequisites
- Python 3.10+

### Installation
1. Clone the repository:
   ```sh
   git clone <repo-url>
   cd aistack_a2a_sample01
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```


### Usage
- To run the main agent system:
  ```sh
  python main.py
  ```
- To test agent interactions:
  ```sh
  python test_client.py
  ```

### Sample Client Interaction Output

Below is a shortened example of the output from running `python test_client.py`, illustrating the A2A long-running task pattern:

```
[17:54:38] Fetching public agent card from: http://localhost:9999/.well-known/agent_card.json
[17:54:38] Fetched public agent card
[17:54:38] A2AClient initialized
[17:54:38] Submitting task...
[17:54:38] Task submitted successfully! Task ID: <task-id>
[17:54:38] Initial response: { ... "status": { "state": "submitted" } ... }
[17:54:38] Starting to poll for task completion...
[17:54:44] Task state: submitted
[17:54:49] Task state: working
[17:54:59] Task state: completed
[17:54:59] Task completed successfully!
[17:54:59] Task result: { ... "text": "Hello There!" ... }
```

This demonstrates submitting a task, polling for status, and retrieving the result when complete.

## Notes
- For development or extension, see the respective Python files for logic and entry points.
- The A2A pattern implemented here is suitable for distributed systems, microservices, and scenarios where agents need to manage asynchronous or long-running operations.

## License
MIT

