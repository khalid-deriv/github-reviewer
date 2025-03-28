import requests

def authenticate_github(token):
    """
    Authenticate with the GitHub API using a personal access token.

    Args:
        token (str): The GitHub personal access token.

    Returns:
        requests.Session: An authenticated session object.

    Raises:
        ValueError: If the token is invalid or missing.
    """
    if not token:
        raise ValueError("GitHub token is required for authentication.")
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    })
    
    # Test the authentication by making a simple API request
    response = session.get("https://api.github.com/user")
    if response.status_code != 200:
        raise ValueError("Failed to authenticate with GitHub. Check your token.")
    
    return session
