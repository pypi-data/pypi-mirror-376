import re

def normalize_whitespace(text: str) -> str:
    """
    Collapse runs of spaces/tabs to a single space on each line, trim trailing
    whitespace from each line, and remove blank lines.

    Args:
        text: The input string to normalize.

    Returns:
        The whitespace-normalized string.
    """
    lines = text.splitlines()
    normalized_lines = []
    for line in lines:
        # Collapse multiple spaces/tabs to a single space
        stripped_line = re.sub(r'[ \t]+', ' ', line.strip())
        if stripped_line:  # Keep only non-empty lines after stripping
            normalized_lines.append(stripped_line)
    return "\n".join(normalized_lines)