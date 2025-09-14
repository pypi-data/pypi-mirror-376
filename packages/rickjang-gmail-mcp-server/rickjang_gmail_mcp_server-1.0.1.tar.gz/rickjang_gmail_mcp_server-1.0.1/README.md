
# Gmail MCP Server

A resilient MCP (Model Context Protocol) server built with fastMCP for sending emails through Gmail's SMTP server using AI agents.

[![PyPI version](https://badge.fury.io/py/rickjang-gmail-mcp-server.svg)](https://badge.fury.io/py/rickjang-gmail-mcp-server)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- Send emails via Gmail SMTP
- Fetch recent emails from Gmail folders
- Handle email attachments
- Health check endpoint for deployment monitoring

## Deployment on Smithery.ai

This server is configured for deployment on Smithery.ai using Streamable HTTP transport.

### Configuration

The server requires the following configuration parameters:
- `smtp_username`: Your Gmail email address
- `smtp_password`: Your Gmail app password (not your regular password)

### Health Check

The server provides a health check endpoint at `/health` for Smithery deployment monitoring.


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

- **Default Port**: 8989
- **Default Host**: 0.0.0.0 (binds to all interfaces)
- **Transport**: Streamable HTTP for MCP compatibility

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
        "SMTP_USERNAME": "your-email@gmail.com",
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

## Docker

Build and run with Docker:
```bash
docker build -t gmail-mcp .
docker run -p 5000:5000 -e SMTP_USERNAME=your-email -e SMTP_PASSWORD=your-password gmail-mcp
```
