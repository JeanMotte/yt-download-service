# src/yt_download_service/app/utils/file_utils.py (New File)

import re
import string


def sanitize_filename(filename: str) -> str:
    """
    Take a string and returns a valid filename.

    This function:
    - Replaces spaces with underscores.
    - Removes characters that are invalid in most filesystems.
    - Limits the length to a reasonable number of characters.
    """
    # Replace spaces and other whitespace with a single underscore
    filename = re.sub(r"\s+", "_", filename)

    # Define a whitelist of allowed characters (alphanumeric, underscore, hyphen, dot)
    # Anything NOT in this set will be removed.
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)

    # Keep only valid characters
    filename = "".join(c for c in filename if c in valid_chars)

    # Limit the length of the filename to avoid issues with max path length
    # 200 is a safe number, leaving room for extensions and paths.
    max_length = 200
    if len(filename) > max_length:
        # Find the last underscore or dot to avoid cutting a word in half
        try:
            split_index = filename.rindex("_", 0, max_length)
        except ValueError:
            split_index = max_length
        filename = filename[:split_index]

    # Ensure the filename is not empty after sanitization
    return filename or "downloaded_video"
