import re

def expand(template):
    """
    Expands a template string with various placeholders.

    Supported placeholders:
    - `(pattern)`: Optional group. If the group contains '|', it represents alternatives.
                   Example: `(abc|def)` expands to `abc` or `def`.
                   Example: `(abc)` expands to `abc` or an empty string.
    - `[pattern]`: Character set. Matches any single character in the pattern.
                   Example: `[abc]` matches `a`, `b`, or `c`.
    - `|`: Used within parentheses for alternatives.

    Args:
        template (str): The template string to expand.

    Yields:
        str: Expanded strings from the template.
    """
    if not template:
        yield ""
        return

    # Try to find the first placeholder
    match = re.search(r'(\(.*?\)|\[.*?\])', template)

    if not match:
        yield template
        return

    placeholder = match.group(1)
    start, end = match.span()
    prefix = template[:start]
    suffix = template[end:]

    if placeholder.startswith('(') and placeholder.endswith(')'):
        # Optional group with alternatives
        content = placeholder[1:-1]
        alternatives = content.split('|')
        for alt in alternatives:
            # Recursively expand with the alternative and the rest of the template
            for expanded_suffix in expand(alt + suffix):
                yield prefix + expanded_suffix
        # Also expand with an empty string for the optional group if it has alternatives
        if alternatives and content != alternatives[0] and len(alternatives) > 1:
            for expanded_suffix in expand(suffix):
                yield prefix + expanded_suffix
        elif not alternatives and content == '': # Case for empty optional ()
             for expanded_suffix in expand(suffix):
                yield prefix + expanded_suffix

    elif placeholder.startswith('[') and placeholder.endswith(']'):
        # Character set
        chars = placeholder[1:-1]
        for char in chars:
            # Recursively expand with the character and the rest of the template
            for expanded_suffix in expand(char + suffix):
                yield prefix + expanded_suffix