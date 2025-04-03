import requests
from logger import setup_logger

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

def fetch_latest_commit_id(session, repo_name, pr_number):
    """
    Fetch the latest commit ID of a pull request using the GitHub API.

    Args:
        session (requests.Session): An authenticated session object.
        repo_name (str): The repository name in the format 'owner/repo'.
        pr_number (int): The pull request number.

    Returns:
        str: The latest commit ID.

    Raises:
        ValueError: If the repository name or pull request number is invalid.
        Exception: If the API request fails.
    """
    if not repo_name or not isinstance(pr_number, int):
        raise ValueError("Invalid repository name or pull request number.")
    
    # Fetch pull request details
    pr_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    pr_response = session.get(pr_url)
    if pr_response.status_code != 200:
        logger.error(f"Failed to fetch PR details: {pr_response.json().get('message', 'Unknown error')}")
        raise Exception(f"Failed to fetch pull request details: {pr_response.json().get('message', 'Unknown error')}")
    
    pr_data = pr_response.json()
    latest_commit_id = pr_data.get("head", {}).get("sha", None)
    if not latest_commit_id:
        logger.error("Failed to retrieve the latest commit ID.")
        raise Exception("Failed to retrieve the latest commit ID.")
    
    return latest_commit_id

def validate_comments_structure(comments):
    """
    Validate the structure of the comments to ensure it follows the desired format.

    Args:
        comments (list): List of comments to validate.

    Raises:
        ValueError: If the comments structure is invalid.
    """
    if not isinstance(comments, list):
        raise ValueError("Comments should be a list.")

    for comment in comments:
        if not isinstance(comment, dict):
            raise ValueError("Each comment should be a dictionary.")
        required_keys = {"file_path", "start_line_number", "end_line_number", "content"}
        if not required_keys.issubset(comment.keys()):
            raise ValueError(f"Each comment must contain the keys: {required_keys}")
        if not isinstance(comment["file_path"], str):
            raise ValueError("The 'file_path' must be a string.")
        if not isinstance(comment["start_line_number"], int) or not isinstance(comment["end_line_number"], int):
            raise ValueError("The 'start_line_number' and 'end_line_number' must be integers.")
        if not isinstance(comment["content"], str):
            raise ValueError("The 'content' must be a string.")

def post_inline_comments(session, repo_name, pr_number, comments):
    """
    Post inline comments on a pull request.

    Args:
        session: Authenticated GitHub session.
        repo_name: Repository name in the format 'owner/repo'.
        pr_number: Pull request number.
        comments: List of comments to post, each containing 'file_path', 'start_line_number',
                  'end_line_number', and 'content'.
    """

    try:
        validate_comments_structure(comments)
        latest_commit_id = fetch_latest_commit_id(session, repo_name, pr_number)
        for comment in comments:
            url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/comments"
            payload = {
                "commit_id": latest_commit_id,  # The commit ID to which the comment is attached
                "path": comment["file_path"],
                "start_line": int(comment["start_line_number"]),  # GitHub API uses 'line' for single-line comments
                "line": int(comment["end_line_number"]),  # GitHub API uses 'line' for inline comments
                "side": "RIGHT",  # Assuming comments are for the right side of the diff
                "start_side": "RIGHT",  # Assuming comments are for the right side of the diff
                "body": comment["content"]
            }
            response = session.post(url, json=payload)
            if response.status_code != 201:
                logger.error(f"Failed to post comment: {response.json().get('message', 'Unknown error')}")
            else:
                logger.info(f"Comment posted successfully on {comment['file_path']} at line {comment['start_line_number']}.")
    except Exception as e:
        logger.error(f"An error occurred while posting comments: {e}")
        raise e
