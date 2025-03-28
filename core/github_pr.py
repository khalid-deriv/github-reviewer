import requests
from core.logger import setup_logger

# Initialize logger
logger = setup_logger()

def fetch_pull_request_details(session, repo_name, pr_number):
    """
    Fetch pull request details using the GitHub API.

    Args:
        session (requests.Session): An authenticated session object.
        repo_name (str): The repository name in the format 'owner/repo'.
        pr_number (int): The pull request number.

    Returns:
        dict: A dictionary containing the author, title, and list of changed files.

    Raises:
        ValueError: If the repository name or pull request number is invalid.
        Exception: If the API request fails.
    """
    if not repo_name or not isinstance(pr_number, int):
        raise ValueError("Invalid repository name or pull request number.")
    
    logger.info(f"Fetching details for PR #{pr_number} in repository '{repo_name}'")
    
    # Fetch pull request details
    pr_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    pr_response = session.get(pr_url)
    if pr_response.status_code != 200:
        logger.error(f"Failed to fetch PR details: {pr_response.json().get('message', 'Unknown error')}")
        raise Exception(f"Failed to fetch pull request details: {pr_response.json().get('message', 'Unknown error')}")
    
    pr_data = pr_response.json()
    author = pr_data.get("user", {}).get("login", "Unknown")
    title = pr_data.get("title", "No title provided")
    
    logger.info(f"Successfully fetched PR details: Author={author}, Title={title}")
    
    # Fetch list of changed files
    files_url = f"{pr_url}/files"
    files_response = session.get(files_url)
    if files_response.status_code != 200:
        raise Exception(f"Failed to fetch changed files: {files_response.json().get('message', 'Unknown error')}")
    
    changed_files = [file["filename"] for file in files_response.json()]
    
    logger.info(f"Fetched {len(changed_files)} changed files for PR #{pr_number}")
    
    return {
        "author": author,
        "title": title,
        "changed_files": changed_files
    }

def fetch_pull_request_diff(session, repo_name, pr_number):
    """
    Fetch the diff of a pull request using the GitHub API.

    Args:
        session (requests.Session): An authenticated session object.
        repo_name (str): The repository name in the format 'owner/repo'.
        pr_number (int): The pull request number.

    Returns:
        str: The diff of the pull request as a string.

    Raises:
        ValueError: If the repository name or pull request number is invalid.
        Exception: If the API request fails.
    """
    if not repo_name or not isinstance(pr_number, int):
        raise ValueError("Invalid repository name or pull request number.")
    
    logger.info(f"Fetching diff for PR #{pr_number} in repository '{repo_name}'")
    
    # Fetch the pull request diff
    diff_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    headers = {"Accept": "application/vnd.github.v3.diff"}
    diff_response = session.get(diff_url, headers=headers)
    
    if diff_response.status_code != 200:
        logger.error(f"Failed to fetch PR diff: {diff_response.json().get('message', 'Unknown error')}")
        raise Exception(f"Failed to fetch pull request diff: {diff_response.json().get('message', 'Unknown error')}")
    
    logger.info(f"Successfully fetched diff for PR #{pr_number}")
    
    return diff_response.text
