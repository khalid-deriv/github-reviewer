import os
import sys
from core.github_auth import authenticate_github
from core.github_pr import fetch_pull_request_details, fetch_pull_request_diff, post_inline_comments
from core.config_validator import load_config, validate_config
from core.prompt_generator import generate_review_prompt
from core.diff_analyzer import analyze_diff
from core.llm_wrapper import LLMWrapper
from core.logger import setup_logger

# Initialize logger
logger = setup_logger()

def main():
    """
    Main entry point for the review agent.
    """
    try:
        # Load and validate configuration
        config_path = os.path.join(os.path.dirname(__file__), "../config/schema.yaml")
        config = load_config(config_path)
        validate_config(config)

        # Authenticate with GitHub
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            logger.error("GITHUB_TOKEN environment variable is not set.")
            sys.exit(1)
        session = authenticate_github(github_token)

        # Extract pull request details from environment variables
        repo_name = os.getenv("GITHUB_REPOSITORY")
        pr_number = os.getenv("GITHUB_PR_NUMBER")
        if not repo_name or not pr_number:
            logger.error("GITHUB_REPOSITORY or GITHUB_PR_NUMBER environment variable is not set.")
            sys.exit(1)
        pr_number = int(pr_number)

        # Fetch pull request details and diff
        pr_details = fetch_pull_request_details(session, repo_name, pr_number)
        diff_details = fetch_pull_request_diff(session, repo_name, pr_number)

        # Analyze the diff
        analyzed_segments = analyze_diff(diff_details)

        # Generate review prompt
        repository_context = "Repository context is not yet implemented."  # Placeholder
        directives = config["directives"]
        prompt = generate_review_prompt(repository_context, diff_details, directives)

        # Query the LLM
        llm_wrapper = LLMWrapper(config["llm_backends"], retry_attempts=3, retry_delay=2)
        llm_response = llm_wrapper.query(prompt, max_tokens=config["llm_parameters"]["max_tokens"])

        # Post inline comments
        comments = []
        for segment in analyzed_segments:
            comments.append({
                "path": segment["code_segment"],  # Replace with actual file path if available
                "position": segment["line_number"],
                "body": llm_response.get("choices", [{}])[0].get("text", "No feedback provided.")
            })
        post_inline_comments(session, repo_name, pr_number, comments)

        logger.info("Pull request review completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the review process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
