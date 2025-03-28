def analyze_diff(diff_text):
    """
    Parse and analyze pull request diffs to identify code segments requiring comments or suggestions.

    Args:
        diff_text (str): The diff text of the pull request.

    Returns:
        list: A list of dictionaries, each containing a code segment and its line number.
              Example: [{"line_number": 42, "code_segment": "def example_function():"}, ...]
    """
    segments = []
    current_file = None
    line_number = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            # Start of a new file
            current_file = line.split(" ")[-1]
            line_number = 0
        elif line.startswith("@@"):
            # Extract the line number from the diff hunk header
            hunk_header = line.split(" ")[1]
            line_number = int(hunk_header.split(",")[0].replace("+", ""))
        elif line.startswith("+") and not line.startswith("+++"):
            # Identify added lines in the diff
            code_segment = line[1:].strip()
            if code_segment:  # Ignore empty lines
                segments.append({"line_number": line_number, "code_segment": code_segment})
            line_number += 1
        elif not line.startswith("-"):
            # Increment line number for unchanged lines
            line_number += 1

    return segments
