
# Gmail MCP Server

A resilient MCP (Model Context Protocol) server built with fastMCP for sending emails through Gmail's SMTP server using AI agents. This server uses stdio transport for seamless integration with MCP clients.

[![PyPI version](https://badge.fury.io/py/rickjang-gmail-mcp-server.svg)](https://badge.fury.io/py/rickjang-gmail-mcp-server)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Send emails via Gmail SMTP
- Fetch recent emails from Gmail folders
- Handle email attachments (from URLs, local files, or pre-staged files)
- stdio transport for MCP client integration


## Gmail App Password Setup

To use this MCP server, you'll need to create a Gmail App Password:

1. Go to your [Google Account settings](https://myaccount.google.com/)
2. Select **Security** from the navigation panel
3. Under "How you sign in to Google," select **2-Step Verification**
4. At the bottom, select **App passwords**
5. Select the app and device you want to generate the app password for
6. Select **Generate**
7. Follow the instructions to enter the app password on your device
8. Select **Done**

Use this app password as your `SMTP_PASSWORD` in the configuration.


## Configuration Options

### Environment Variables

- `SMTP_USERNAME`: Your Gmail email address
- `SMTP_PASSWORD`: Your Gmail app password (not your regular password)

### Server Configuration

- **Transport**: stdio for MCP client integration
- **Protocol**: MCP (Model Context Protocol)

## Installation

### Option 1: Direct Installation with pip

Install the package from PyPI:

```bash
pip install rickjang-gmail-mcp-server
```

Then set up your Gmail credentials as environment variables:
```bash
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

Run the server:
```bash
rickjang-gmail-mcp-server
```

### Option 2: MCP Server Configuration with uv (Recommended)

Add the following to your MCP client configuration (e.g., Claude Desktop):

```json
{
  "mcpServers": {
    "gmail-mcp": {
      "command": "uv",
      "args": [
        "tool", 
        "run", 
        "rickjang-gmail-mcp-server"
      ],
      "env": {
        "SMTP_USERNAME": "your-email@gmail.com",
        "SMTP_PASSWORD": "your-gmail-app-password"
      }
    }
  }
}
```

This method automatically installs the package using uv and sets the environment variables directly in the configuration.

### Claude Desktop Configuration

For Claude Desktop, add this to your `claude_desktop_config.json` file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "gmail-mcp": {
      "command": "uv",
      "args": [
        "tool", 
        "run", 
        "rickjang-gmail-mcp-server"
      ],
      "env": {
        "SMTP_USERNAME": "jyjang@uengine.org",
        "SMTP_PASSWORD": "your-gmail-app-password"
      }
    }
  }
}
```

After adding this configuration, restart Claude Desktop to load the MCP server.

## Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/rickjang/Gmail-mcp-server.git
   cd Gmail-mcp-server
   ```

2. Install in development mode:
   ```bash
   pip install -e .
   ```

3. Set environment variables and run:
   ```bash
   export SMTP_USERNAME="your-email@gmail.com"
   export SMTP_PASSWORD="your-app-password"
   rickjang-gmail-mcp-server
   ```

## Available Tools

This MCP server provides the following tools:

### send_email_tool
Send emails via Gmail SMTP with optional attachments.

**Parameters:**
- `recipient` (string): Email address to send to
- `subject` (string): Email subject
- `body` (string): Email body text
- `attachment_path` (string, optional): Direct file path for attachment
- `attachment_url` (string, optional): URL to download attachment from
- `attachment_name` (string, optional): Filename for attachment

### fetch_recent_emails
Fetch recent emails from a Gmail folder.

**Parameters:**
- `folder` (string, optional): Email folder to fetch from (default: "INBOX")
- `limit` (integer, optional): Maximum number of emails to fetch (default: 10)

## Testing

Test the server locally:

```bash
# Basic functionality test
python test_local.py

# stdio transport test
python test_stdio.py
```
