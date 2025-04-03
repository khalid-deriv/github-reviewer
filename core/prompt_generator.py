import os

def load_directive_content(directive):
    if os.path.isfile(directive):
        with open(directive, 'r') as file:
            directive = file.read().strip()
    return directive

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
    formatted_directives = "\n\n".join(f"{load_directive_content(directive)}" for directive in directives)

    # Construct the prompt
    prompt = "\n".join([f"""
        You are an AI code reviewer with expertise in data engineering, architecture, query optimization, modeling, and security. 
        Your task is to review the following pull request based on the provided repository context, diff details, 
        and coding standards. Provide detailed feedback, including suggestions for improvement, 
        potential bugs, and adherence to coding standards.\n\n
        ### Repository Context\n
        {repository_context}\n\n
        ### Coding Standards and Guidelines\n
        {formatted_directives}\n\n
        ### Pull Request Diff\n
        {diff_details}\n\n
        ### Instructions\n
        1. Identify performance issues, potential bugs, and inconsistencies.\n
        2. Suggest improvements to code quality and adherence to coding standards.\n
        3. Provide specific code suggestions where applicable.\n
        4. Focus on SQL query optimization if relevant.\n\n
        The output MUST be in this json format where each comment is an element of the array:\n
    """, """
        {
            comments: [
                {
                    file_path: ,
                    start_line_number: 1,
                    end_line_number: 10,
                    content: Comment content,
                }
            ]
        }
        \n
        Where each comment is directed at a portion of the diff identified by the start_line_number and end_line_number. Calculate the appropriate start_line_number and end_line_number to highlight only the part of the diff that is relevant to the comment.\n
        IMPORTANT: make sure that the start_line_number and end_line_number values must be part of the same hunk as the line\n\n
        IMPORTANT: DO NOT include any other text, only the json format.\n

        Begin your review below:\n

    """])

    return prompt
