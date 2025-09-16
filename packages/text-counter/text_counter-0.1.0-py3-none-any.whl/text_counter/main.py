import re
from mcp.server.fastmcp import FastMCP

mcp = FastMCP()

@mcp.tool()
def get_text_count(text: str):
    """
    Calculate basic text metrics for the input text.
    - characters: total character count
    - characters_without_space: character count excluding whitespace
    - words: word count
    """

    return {
        "characters": len(text),
        "characters_without_space": len(re.sub(r"\s+", "", text)),
        "words": len(text.split()),
    }

if __name__ == "__main__":
    mcp.run()