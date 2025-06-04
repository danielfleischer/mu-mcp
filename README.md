# MCP Weather Server (Python)

This project implements a Model Context Protocol (MCP) server in Python that provides weather alerts and forecasts using the US National Weather Service API.

## Features
- `get_alerts(state)`: Get weather alerts for a US state (e.g. CA, NY)
- `get_forecast(latitude, longitude)`: Get weather forecast for a location

## Setup
1. Create and activate a Python virtual environment:
   ```fish
   python3 -m venv .venv
   source .venv/bin/activate.fish
   ```
2. Install dependencies:
   ```fish
   pip install --upgrade pip
   pip install mcp[cli] httpx
   ```

## Running the server
```fish
python weather.py
```

The server will start and listen for MCP stdio connections.

## References
- MCP Python SDK: https://github.com/modelcontextprotocol/create-python-server
- MCP Protocol: https://modelcontextprotocol.io/llms-full.txt
