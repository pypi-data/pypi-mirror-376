import re

def safelink_zwsp(text: str) -> str:
    """
    Insert zero-width spaces into URLs to prevent auto-linking and allow
    copy-pasting while retaining readability.

    This function identifies URLs within the input text and inserts a
    zero-width space character (U+200B) after the protocol (e.g., "http://").
    This prevents most markdown/text renderers from automatically
    converting the URL into a clickable link, while still allowing users to
    copy the full URL.

    Args:
        text: The input string possibly containing URLs.

    Returns:
        The modified string with zero-width spaces inserted into URLs.
    """
    # Regex to find common URL schemes followed by ://
    # This is a simplified regex for demonstration; a more robust one might be needed for production.
    url_pattern = re.compile(r'(https?://)', re.IGNORECASE)
    
    def replacer(match):
        return match.group(1) + '\u200b' # U+200B is the zero-width space

    return url_pattern.sub(replacer, text)