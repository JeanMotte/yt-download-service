import re


def is_valid_youtube_url(url: str) -> bool:
    """
    Check if the given URL is a valid YouTube video or Shorts URL.

    Args:
    ----
        url: The URL to validate.

    Returns:
    -------
        True if the URL is a valid YouTube URL, False otherwise.

    """
    pattern = r"^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|youtube-nocookie\.com)\/(watch\?v=|embed\/|v\/|shorts\/|.+\?v=)?([a-zA-Z0-9_-]{11})"  # noqa: E501
    return re.match(pattern, url) is not None
