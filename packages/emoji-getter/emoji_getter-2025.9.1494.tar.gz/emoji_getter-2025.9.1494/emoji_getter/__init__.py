import re

def emoji_extract(text: str) -> str:
    """
    Return a string that contains only emoji characters from text.
    Heuristic considered: Emojis are Unicode characters that fall within
    specific ranges or are part of specific Unicode blocks. This function
    uses a simplified regex to capture common emoji patterns.
    """
    # This regex is a simplification and might not capture all emojis
    # or might capture some non-emojis. It targets common emoji ranges.
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F64F"  # Emoticons, emotional portraits
        "\U0001F650-\U0001F67F"  # Ornamental dingbats
        "\U0001F680-\U0001F6FF"  # Transport and map symbols
        "\U0001F700-\U0001F77F"  # Alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-A
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"
        "]+"
    )
    return "".join(emoji_pattern.findall(text))