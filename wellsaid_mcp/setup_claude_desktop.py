#!/usr/bin/env python3
"""
Claude Desktop MCP Server Configuration Updater

This script adds or updates the 'wellsaid' MCP server in Claude Desktop's configuration
across macOS, Linux, and Windows platforms.
"""

import json
import os
import platform
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import shutil


def get_claude_config_path() -> Optional[Path]:
    """
    Get the Claude Desktop configuration file path based on the operating system.
    
    Returns:
        Path to the Claude Desktop config file, or None if not found
    """
    system = platform.system()
    
    if system == "Darwin":  # macOS
        config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        # Try XDG_CONFIG_HOME first, then fall back to ~/.config
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_path = Path(xdg_config) / "Claude" / "claude_desktop_config.json"
        else:
            config_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        # Windows uses AppData/Roaming
        config_path = Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:
        print(f"Unsupported operating system: {system}")
        return None
    
    return config_path


def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load the existing Claude Desktop configuration.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing the configuration, or empty dict if file doesn't exist
    """
    if not config_path.exists():
        print(f"Config file not found at {config_path}")
        print("Creating new configuration...")
        return {}
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            print(f"Loaded existing configuration from {config_path}")
            return config
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON in {config_path}: {e}")
        print("Creating backup and starting with empty configuration...")
        # Create backup
        backup_path = config_path.with_suffix('.json.backup')
        config_path.rename(backup_path)
        print(f"Original config backed up to {backup_path}")
        return {}
    except Exception as e:
        print(f"Error reading config file: {e}")
        return {}


def update_wellsaid_server(config: Dict[str, Any], dev_mode: bool = False, repo_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Add or update the wellsaid MCP server configuration.
    
    Args:
        config: Current configuration dictionary
        dev_mode: Whether to use development mode configuration
        repo_path: Path to the git repository (required for dev mode)
        
    Returns:
        Updated configuration dictionary
    """

    print("looking up existing key")
    existing_api_key = None
    if "wellsaid" in config.get("mcpServers", {}):
        existing_api_key = config["mcpServers"]["wellsaid"].get("env", {}).get("WELLSAID_API_KEY",None)
    existing_api_key_message = ""
    if existing_api_key:
        existing_api_key_message = f"(Leave blank to use existing api key {existing_api_key[:6]}...)"
    api_key = input(f"Enter your Wellsaid api key {existing_api_key_message}: ")
    if not api_key:
        print("Using existing api key")
        api_key = existing_api_key

    # Ensure the mcpServers section exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
        print("Created new mcpServers section")
    
    if dev_mode:
        if not repo_path:
            raise ValueError("Repository path is required for development mode")
        
        repo_path_obj = Path(repo_path).resolve()
        if not repo_path_obj.exists():
            raise ValueError(f"Repository path does not exist: {repo_path_obj}")
        
        print(f"Configuring development mode with repo at: {repo_path_obj}")
        
        # Development mode configuration with shell command
        # Locate uv binary
        uv_path = shutil.which("uv")
        if platform.system() == "Windows":
            # Windows batch command
            wellsaid_config = {
                "command": "cmd",
                "args": ["/c", f"cd /d \"{repo_path_obj}\" && {uv_path} venv && {uv_path} run wellsaid-mcp"],
                "env": {
                    "WELLSAID_API_KEY": api_key
                }
            }
        else:
            # Unix shell command (macOS/Linux)
            wellsaid_config = {
                "command": "sh",
                "args": ["-c", f"cd \"{repo_path_obj}\" && {uv_path} run wellsaid-mcp"],
                "env": {
                    "WELLSAID_API_KEY": api_key
                }
            }
    else:
        # Production mode configuration
        
        wellsaid_config = {
            "command": "uvx",
            "args": ["wellsaid-mcp"],
            "env": {
                "WELLSAID_API_KEY": api_key
            }
        }
    
    # Check if wellsaid server already exists
    if "wellsaid" in config["mcpServers"]:
        mode_str = "development" if dev_mode else "production"
        print(f"Found existing 'wellsaid' MCP server - updating to {mode_str} configuration")
    else:
        mode_str = "development" if dev_mode else "production"
        print(f"Adding new 'wellsaid' MCP server in {mode_str} mode")
    
    # Add or update the wellsaid server
    config["mcpServers"]["wellsaid"] = wellsaid_config
    
    return config


def save_config(config: Dict[str, Any], config_path: Path) -> bool:
    """
    Save the updated configuration to file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path where to save the configuration
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure the directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the configuration with nice formatting
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved configuration to {config_path}")
        return True
        
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return False


def print_current_servers(config: Dict[str, Any]) -> None:
    """
    Print the current MCP servers in the configuration.
    
    Args:
        config: Current configuration dictionary
    """
    if "mcpServers" not in config or not config["mcpServers"]:
        print("No MCP servers currently configured")
        return
    
    print("Current MCP servers:")
    for server_name, server_config in config["mcpServers"].items():
        command = server_config.get("command", "")
        args = server_config.get("args", [])
        args_str = " ".join(args) if args else ""
        full_command = f"{command} {args_str}".strip()
        print(f"  - {server_name}: {full_command}")


def main():
    """
    Main function to update Claude Desktop MCP server configuration.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Update Claude Desktop MCP server configuration for wellsaid",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Production mode (default)
  python update_claude_config.py
  
  # Development mode
  python update_claude_config.py --dev /path/to/wellsaid-mcp-repo
  python update_claude_config.py --dev .  # if running from repo directory
        """
    )
    parser.add_argument(
        "--dev", 
        metavar="REPO_PATH",
        help="Enable development mode with path to git repository"
    )
    
    args = parser.parse_args()
    
    print("Claude Desktop MCP Server Configuration Updater")
    print("=" * 50)
    
    # Get the configuration file path
    config_path = get_claude_config_path()
    if not config_path:
        sys.exit(1)
    
    print(f"Platform: {platform.system()}")
    print(f"Config path: {config_path}")
    
    if args.dev:
        print(f"Mode: Development")
        print(f"Repository path: {args.dev}")
    else:
        print("Mode: Production")
    print()
    
    # Load existing configuration
    config = load_config(config_path)
    
    # Print current servers
    print_current_servers(config)
    print()
    
    # Update the wellsaid server
    try:
        updated_config = update_wellsaid_server(config, dev_mode=bool(args.dev), repo_path=args.dev)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Save the updated configuration
    if save_config(updated_config, config_path):
        print()
        print("Configuration updated successfully!")
        print()
        print("Updated MCP servers:")
        print_current_servers(updated_config)
        print()
        if args.dev:
            print("Development mode enabled:")
            print("- Will create virtual environment")
            print("- Will install package in editable mode")
            print("- Will run uvx wellsaid-mcp")
            print()
        print("Please restart Claude Desktop for changes to take effect.")
    else:
        print("Failed to save configuration")
        sys.exit(1)


if __name__ == "__main__":
    main()