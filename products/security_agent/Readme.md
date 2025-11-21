```bash
pip install langchain langchain-openai langchain-mcp-adapters langgraph mcp requests pyyaml
2.  **Set Keys:**
```bash
export OPENAI_API_KEY="sk-..."
3.  **Mock Target:** Ensure you have a local API running at `localhost:5000` or update the `BASE_URL` in `tools_server.py`.
```

```bash
python security_agent.py
```

this agent:

Uses Context: It reads the API spec to understand what parameters to test for SSRF and BOLA.

Decoupled Architecture: By using MCP, you can easily swap the tools_server.py for a real remote pentesting server without changing the agent code.

Logic Verification: It verifies state. For example, in the BOLA test, it doesn't just look for a 200 OK; it logs into the server (via the tool) and checks if the data returned matches the victim's data.