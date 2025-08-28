

# WellSaid MCP Server
Guide to walk through the end-to-end process of using the WellSaid MCP server
## **Overview**

The WellSaid MCP Server lets you connect AI clients (such as Claude Desktop) directly to the WellSaid API. Once installed, your AI client can generate speech, discover voices, and manage advanced audio features without writing any custom integration code.

This guide covers installation, configuration, and common usage patterns.



## **Prerequisites**

Before getting started, make sure you have:

* A WellSaid API key, available in your WellSaid account
* An MCP-compatible AI client (e.g., Claude Desktop)
* [uv](https://docs.astral.sh/uv/getting-started/installation/) installed — this tool manages the MCP server environment
* The <Anchor label="WellSaid MCP Server" target="_blank" href="https://github.com/wellsaid-labs/mcp-server">WellSaid MCP Server</Anchor> installed in your LLM client



## Installation

### Option 1: From Package

If you only need the server for use with Claude Desktop, install from the published package:

```powershell bash
uvx --from wellsaid-mcp wellsaid-mcp-setup-claude-desktop
```

### Option 2: Local Development

If you want to run the MCP server locally for development:

```powershell bash
# Create and activate a virtual environment
uv venv

# Install the server in editable mode
uv pip install --editable .
```

### Configuration with Claude Desktop

Once installed, you'll need to register the WellSaid MCP server with Claude Desktop.

```powershell bash
uv run wellsaid-mcp-setup-claude-desktop --dev .
```

When prompted, enter your WellSaid API key.\
After configuration, **restart Claude Desktop** to apply the changes.

***

## Available Tools

Once connected, your AI client can call WellSaid functions through natural prompts.

### Voice Discovery

* `get_avatar_criteria` – Lists available filters for voices\
  Example: "Show me all available voice filtering options"
* `get_avatars` – Search for voices matching specific traits\
  Example: "Find a confident, professional female voice with US accent"
* `get_avatar_characteristics` – Lists available voice characteristics\
  Example: "What voice characteristics can I choose from?"

### Speech Generation

* `text_to_speech` – Convert text into speech with a selected voice\
  Example: "Generate speech for 'Welcome to our training program' using speaker ID 145"
* `create_multiple_clips_and_combine` – Generate multi-speaker or long-form audio\
  Example: "Create a dialogue where Speaker 89 says 'Hello there' and Speaker 76 replies 'Good morning'"

### Advanced Voice Controls (Caruso Model)

* `Adjust_pitch` – Modify pitch (-250 to +500)
* `Adjust_tempo` – Change speaking speed (0.5 to 2.5)
* `Adjust_loudness` – Control loudness (-20 to +10)
* `Apply_respelling` – Override pronunciations
* `Validate_AI_Director_tags` – Validate markup formatting

## Example Workflows

**Training Content**\
"Find a clear, informative voice for eLearning, then generate speech at a slower tempo so it's easy to comprehend:
'Today we'll learn about machine learning algorithms.'"

**Marketing**\
"Use an upbeat voice, increase pitch by 50, and generate a script that has a sales pitch for our new product"

**Character Dialogue**\
"Select two characters to have a conversation the first says 'Hello,' and the second will reply 'Hi there,' with short natural pauses in the conversation."

**Multilingual**\
"Find a Spanish voice with Mexico accent and a French voice to say the following line in each language:
'Welcome to our new program.'"

## Conclusion

The WellSaid MCP Server makes it easy to:

* Discover and select the right voice for your project
* Generate professional AI-powered audio directly in your AI client
* Control pitch, pacing, and pronunciation with precision

With this integration, you get the full power of the WellSaid API — without having to write API calls manually.
