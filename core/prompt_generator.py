def generate_review_prompt(repository_context, diff_details, directives):
    """
    Generate a formatted prompt for the LLM to review a pull request.

    Args:
        repository_context (str): Contextual information about the repository (e.g., key files, architecture).
        diff_details (str): The diff details of the pull request.
        directives (list): A list of coding standards and guidelines.

    Returns:
        str: A formatted prompt string for the LLM.
    """
    # Format the directives into a readable string
    formatted_directives = "\n".join(f"- {directive}" for directive in directives)

    # Construct the prompt
    prompt = (
        "You are an AI code reviewer with expertise in software engineering. "
        "Your task is to review the following pull request based on the provided repository context, diff details, "
        "and coding standards. Provide detailed feedback, including suggestions for improvement, "
        "potential bugs, and adherence to coding standards.\n\n"
        "### Repository Context\n"
        f"{repository_context}\n\n"
        "### Coding Standards and Guidelines\n"
        f"{formatted_directives}\n\n"
        "### Pull Request Diff\n"
        f"{diff_details}\n\n"
        "### Instructions\n"
        "1. Identify performance issues, potential bugs, and inconsistencies.\n"
        "2. Suggest improvements to code quality and adherence to coding standards.\n"
        "3. Provide specific code suggestions where applicable.\n"
        "4. Focus on SQL query optimization if relevant.\n\n"
        "Begin your review below:\n"
    )

    return prompt
