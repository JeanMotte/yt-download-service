import re


def is_valid_youtube_url(url: str) -> bool:
    """Check if the given URL is a valid YouTube video URL.

    Args:
    ----
        url: The URL to validate.

    Returns:
    -------
        True if the URL is a valid YouTube video URL, False otherwise.

    """
    pattern = r"^(https://?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})"
    return re.match(pattern, url) is not None
