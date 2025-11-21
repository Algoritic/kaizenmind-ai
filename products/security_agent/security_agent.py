import asyncio
import argparse
import sys
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

# --- CLI SETUP ---
parser = argparse.ArgumentParser(description="AI Agent for OWASP API Security Testing")
parser.add_argument("--url", required=True, help="Target API Base URL (e.g., http://localhost:5000)")
parser.add_argument("--token", required=True, help="Valid Authorization Token for the Attacker (User A)")
parser.add_argument("--spec", required=True, help="Path or URL to OpenAPI/Swagger Spec")
parser.add_argument("--victim-id", required=False, default="0000", help="A valid ID of another user (User B) to test BOLA against")
args = parser.parse_args()

SERVER_SCRIPT_PATH = "./tools_server.py"
PYTHON_PATH = "python" 

async def run_security_audit():
    print(f"--- 🔒 STARTING AUDIT ON {args.url} ---")
    
    client = MultiServerMCPClient(
        {
            "api_arsenal": {
                "command": PYTHON_PATH,
                "args": [SERVER_SCRIPT_PATH],
                "transport": "stdio",
            }
        }
    )
    
    try:
        async with client.session("api_arsenal") as session:
            tools = await session.get_tools()
            
            # --- DYNAMIC SYSTEM PROMPT ---
            # We inject the user's specific args into the LLM's brain
            system_prompt = f"""
            You are an elite API Security Auditor.
            
            TARGET CONFIGURATION:
            - Base URL: {args.url}
            - Attacker Token: {args.token}
            - OpenAPI Spec: {args.spec}
            - Victim ID (for BOLA): {args.victim_id}
            
            MISSION:
            Execute a rigorous OWASP Top 10 audit on the TARGET.
            
            RULES:
            1. ALWAYS pass the 'base_url' and 'auth_token' provided above to every tool call.
            2. Start by parsing the spec provided at '{args.spec}'.
            3. For BOLA tests, use the Victim ID '{args.victim_id}'.
            4. For Rate Limiting, pick ONE safe endpoint (like /info or /health) and test it.
            
            CHECKLIST:
            1. [Discovery] Parse spec.
            2. [API1] Test BOLA on endpoints with IDs.
            3. [API3] Test Mass Assignment on POST endpoints.
            4. [API4] Test Rate Limiting.
            5. [Report] Summarize findings.
            """
            
            llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
            agent = create_react_agent(llm, tools, state_modifier=system_prompt)
            
            print("--- 🚀 AGENT ACTIVATED ---")
            
            async for event in agent.astream_events(
                {"messages": [("user", "Start the audit now.")]}, 
                version="v1"
            ):
                kind = event["event"]
                if kind == "on_tool_start":
                    print(f"\n[TOOL] {event['name']}...")
                elif kind == "on_tool_end":
                    output = str(event['data'].get('output'))
                    print(f"[RESULT] {output[:150]}..." if len(output) > 150 else f"[RESULT] {output}")
                elif kind == "on_chain_end":
                    if "messages" in event["data"].get("output", {}):
                        last_msg = event["data"]["output"]["messages"][-1]
                        if hasattr(last_msg, "content") and not last_msg.tool_calls:
                             print(f"\n--- 📝 FINAL REPORT ---\n{last_msg.content}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.aclose()

if __name__ == "__main__":
    asyncio.run(run_security_audit())