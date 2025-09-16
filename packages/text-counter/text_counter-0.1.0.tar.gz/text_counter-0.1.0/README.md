# Text Counter MCP Server

An MCP (Model Context Protocol) server that calculates basic text metrics for input text.

## Features

- `get_text_count(text: str)`: Returns basic metrics for the provided text
  - `characters`: total character count
  - `characters_without_space`: character count excluding whitespace
  - `words`: word count

Example:

```json
{
  "characters": 12,
  "characters_without_space": 11,
  "words": 2
}
```

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) installed

All Python dependencies are defined in `pyproject.toml` and will be resolved by `uv`.

## Run locally

From this directory:

```bash
uv run python main.py
```

Or from anywhere using an explicit directory:

```bash
uv run --directory /home/gws8820/devochat/mcp-proxy/servers/text-counter python main.py
```

## Use with an MCP client

Add the following in your MCP client configuration (example `servers.json`):

```json
{
  "mcpServers": {
    "text-counter": {
      "command": "uvx",
      "args": ["text-counter"]
    }
  }
}
```

Once connected, call the tool `get_text_count` with a `text` string argument.

## License

Distributed under the [MIT License](LICENSE).
