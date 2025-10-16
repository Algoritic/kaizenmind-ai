import os
import re

# Placeholder for the MCP client
class MCPClient:
    def __init__(self, api_url, token):
        import requests
        self.requests = requests
        
        # FIX 1: Explicitly check for an empty string, which occurs when 
        # GITHUB_API_BASE_URL is set to = in docker-compose.yml
        if not api_url:
            api_url = "https://api.github.com"
            
        # Store the configurable API URL, ensuring no trailing slash for clean path joining
        self.api_url = api_url.rstrip('/')
        self.token = token

    def get_pr_diff(self, pr_url: str) -> str:
        """
        Fetches the diff of a GitHub pull request.
        """
        pr_url_pattern = re.compile(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)')
        match = pr_url_pattern.match(pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}. Expected format: https://github.com/owner/repo/pull/123")
        
        owner, repo_name_with_git, pr_number = match.groups()
        # FIX 2: Clean the repo name by removing the optional .git suffix
        repo_name = repo_name_with_git.removesuffix('.git')
        
        request_url = f"{self.api_url}/repos/{owner}/{repo_name}/pulls/{pr_number}"

        headers = {
            "Accept": "application/vnd.github.v3.diff",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        response = self.requests.get(request_url, headers=headers)
        response.raise_for_status()
        return response.text

    def get_pr_files(self, pr_url: str) -> list:
        """
        Fetches the files changed in a GitHub pull request.
        """
        pr_url_pattern = re.compile(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)')
        match = pr_url_pattern.match(pr_url)
        if not pr_url_pattern.match(pr_url):
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}. Expected format: https://github.com/owner/repo/pull/123")
            
        owner, repo_name_with_git, pr_number = match.groups()
        # FIX 2: Clean the repo name by removing the optional .git suffix
        repo_name = repo_name_with_git.removesuffix('.git')
        
        files_url = f"{self.api_url}/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        response = self.requests.get(files_url, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_branches(self, repo_url: str) -> list[str]:
        """
        Fetches the branches of a GitHub repository.
        """
        repo_url_pattern = re.compile(r'https://github\.com/([^/]+)/([^/]+)')
        match = repo_url_pattern.match(repo_url)
        if not match:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}. Expected format: https://github.com/owner/repo")
        
        owner, repo_name_with_git = match.groups()
        # FIX 2: Clean the repo name by removing the optional .git suffix
        repo_name = repo_name_with_git.removesuffix('.git')
        
        api_url = f"{self.api_url}/repos/{owner}/{repo_name}/branches"
        
        headers = {}
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        response = self.requests.get(api_url, headers=headers)
        response.raise_for_status()
        return [branch['name'] for branch in response.json()]

    def get_branch_diff(self, repo_url: str, base: str, head: str) -> str:
        """
        Fetches the diff between two branches of a GitHub repository.
        """
        repo_url_pattern = re.compile(r'https://github\.com/([^/]+)/([^/]+)')
        match = repo_url_pattern.match(repo_url)
        if not match:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}. Expected format: https://github.com/owner/repo")
        
        owner, repo_name_with_git = match.groups()
        # FIX 2: Clean the repo name by removing the optional .git suffix
        repo_name = repo_name_with_git.removesuffix('.git')
        
        # This line now correctly prepends the scheme/host (self.api_url) 
        api_url = f"{self.api_url}/repos/{owner}/{repo_name}/compare/{base}...{head}"
        
        headers = {
            "Accept": "application/vnd.github.v3.diff",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        response = self.requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.text

    def post_pr_review_comment(self, pr_url: str, body: str):
        """
        Posts a simple comment on a GitHub pull request.
        """
        pr_url_pattern = re.compile(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)')
        match = pr_url_pattern.match(pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL: {pr_url}")

        owner, repo_name_with_git, pr_number = match.groups()
        # FIX 2: Clean the repo name by removing the optional .git suffix
        repo_name = repo_name_with_git.removesuffix('.git')
        
        api_url = f"{self.api_url}/repos/{owner}/{repo_name}/issues/{pr_number}/comments"

        headers = {
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"

        data = {"body": body}
        
        response = self.requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()

# Set up the base URL from environment variable, defaulting to GitHub API
GITHUB_API_BASE_URL = os.environ.get("GITHUB_API_BASE_URL", "https://api.github.com")

# Initialize the client with the configurable base URL
mcp_client = MCPClient(GITHUB_API_BASE_URL, os.environ.get("GITHUB_TOKEN", "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"))

def get_pr_diff(pr_url: str) -> str:
    """Fetches the diff of a GitHub pull request."""
    return mcp_client.get_pr_diff(pr_url)

def get_pr_files(pr_url: str) -> list:
    """Fetches the files changed in a GitHub pull request."""
    return mcp_client.get_pr_files(pr_url)

def get_branches(repo_url: str) -> list[str]:
    """Fetches the branches of a GitHub repository."""
    return mcp_client.get_branches(repo_url)

def get_branch_diff(repo_url: str, base: str, head: str) -> str:
    """Fetches the diff between two branches of a GitHub repository."""
    return mcp_client.get_branch_diff(repo_url, base, head)

def post_pr_review_comment(pr_url: str, body: str):
    """Posts a review comment on a GitHub pull request."""
    return mcp_client.post_pr_review_comment(pr_url, body)