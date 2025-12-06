from fastmcp import FastMCP
import subprocess
import shlex

# Initialize FastMCP server
mcp = FastMCP("Kali Security Tools")

@mcp.tool()
def scan_network_fast(target: str) -> str:
    """
    Perform a fast Nmap scan on the target (Top 100 ports).
    Args:
        target: The IP address or hostname to scan.
    """
    command = f"nmap -F {shlex.quote(target)}"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running nmap: {e.stderr}"

@mcp.tool()
def scan_network_comprehensive(target: str) -> str:
    """
    Perform a comprehensive Nmap scan (Service version detection, default scripts).
    Use with caution as this is intrusive.
    Args:
        target: The IP address or hostname to scan.
    """
    command = f"nmap -sV -sC {shlex.quote(target)}"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running nmap: {e.stderr}"

@mcp.tool()
def analyze_web_technologies(url: str) -> str:
    """
    Identify technologies used by a website using WhatWeb.
    Args:
        url: The full URL to analyze (e.g., https://example.com).
    """
    command = f"whatweb --no-errors {shlex.quote(url)}"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running whatweb: {e.stderr}"

@mcp.tool()
def fuzz_directories(url: str, wordlist_path: str = "/usr/share/wordlists/dirb/common.txt") -> str:
    """
    Fuzz directories using Gobuster.
    Args:
        url: The target URL.
        wordlist_path: Path to wordlist (defaults to standard Kali wordlist).
    """
    # Using gobuster dir mode
    # -n: No progress (cleaner output for MCP)
    command = f"gobuster dir -u {shlex.quote(url)} -w {shlex.quote(wordlist_path)} -n -z --timeout 10s"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error running gobuster: {e.stderr}"

@mcp.tool()
def api_request(method: str, url: str, headers: dict = None, body: str = None):
    import requests
    response = requests.request(method, url, headers=headers, data=body)
    return {
        "status": response.status_code,
        "headers": dict(response.headers),
        "body": response.text,
    }

@mcp.tool()
def run_nuclei(target: str):
    command = f"nuclei -u {shlex.quote(target)}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return result.stdout

import jwt

@mcp.tool()
def fuzz_api(url: str, wordlist="/usr/share/wordlists/api.txt"):
    command = f"ffuf -u {url} -w {wordlist}"
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout

@mcp.tool()
def run_sqlmap(url: str):
    command = f"sqlmap -u {shlex.quote(url)} --batch"
    return subprocess.run(command, shell=True, capture_output=True, text=True).stdout

if __name__ == "__main__":
    mcp.run()
