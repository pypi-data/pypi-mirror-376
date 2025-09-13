"""MCP Server that proxies requests to Amazon Bedrock AgentCore Runtime."""

import asyncio
import sys
import os
import json
import logging
from typing import Any, Sequence, Optional
from dotenv import load_dotenv

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    ListToolsResult,
    CallToolResult,
)

from .client import BedrockMCPClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockMCPProxyServer:
    """Stateless MCP Server that proxies requests to Bedrock AgentCore Runtime."""
    
    def __init__(self):
        self.server = Server("opsguide-mcp-proxy")
        self._setup_handlers()
    
    async def _create_client_and_execute(self, operation):
        """Create a fresh client, execute operation, and clean up."""
        logger.info("Creating fresh connection to Bedrock AgentCore...")
        client = BedrockMCPClient()
        try:
            await client.connect()
            logger.info("Connected - executing operation...")
            result = await operation(client)
            logger.info("Operation completed successfully")
            return result
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise
        finally:
            logger.info("Closing connection...")
            await client.disconnect()
            logger.info("Connection closed")
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools from Bedrock AgentCore."""
            try:
                async def list_operation(client):
                    return await client.list_tools()
                
                return await self._create_client_and_execute(list_operation)
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return ListToolsResult(tools=[])
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Call a tool on Bedrock AgentCore."""
            try:
                async def call_operation(client):
                    return await client.call_tool(name, arguments)
                
                return await self._create_client_and_execute(call_operation)
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error calling tool: {str(e)}")]
                )

    
    async def run(self):
        """Run the stateless MCP proxy server."""
        logger.info("Starting OpsGuide MCP Proxy Server (stateless mode)")
        
        try:
            # Run the MCP server without persistent connections
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream, 
                    write_stream, 
                    InitializationOptions(
                        server_name="opsguide-mcp-proxy",
                        server_version="0.1.2",
                        capabilities=self.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities=None,
                        ),
                    ),
                )
        except KeyboardInterrupt:
            logger.info("Server interrupted by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


async def main():
    """Main entry point for the MCP server."""
    proxy_server = BedrockMCPProxyServer()
    await proxy_server.run()


def cli():
    """Command line interface entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()