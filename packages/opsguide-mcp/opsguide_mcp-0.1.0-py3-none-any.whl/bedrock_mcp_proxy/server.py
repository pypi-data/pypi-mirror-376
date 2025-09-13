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
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    Prompt,
    GetPromptResult,
    ListPromptsResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceResult,
    CallToolResult,
)

from .client import BedrockMCPClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BedrockMCPProxyServer:
    """MCP Server that proxies requests to Bedrock AgentCore Runtime."""
    
    def __init__(self):
        self.server = Server("bedrock-mcp-proxy")
        self.bedrock_client: BedrockMCPClient = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up MCP server handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools from Bedrock AgentCore."""
            if not self.bedrock_client:
                return ListToolsResult(tools=[])
            
            try:
                result = await self.bedrock_client.list_tools()
                return result
            except Exception as e:
                logger.error(f"Error listing tools: {e}")
                return ListToolsResult(tools=[])
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
            """Call a tool on Bedrock AgentCore."""
            if not self.bedrock_client:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: Not connected to Bedrock AgentCore")]
                )
            
            try:
                result = await self.bedrock_client.call_tool(name, arguments)
                return result
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error calling tool: {str(e)}")]
                )
        
        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            """List available resources from Bedrock AgentCore."""
            if not self.bedrock_client:
                return ListResourcesResult(resources=[])
            
            try:
                result = await self.bedrock_client.list_resources()
                return result
            except Exception as e:
                logger.error(f"Error listing resources: {e}")
                return ListResourcesResult(resources=[])
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            """Read a resource from Bedrock AgentCore."""
            if not self.bedrock_client:
                return ReadResourceResult(
                    contents=[TextContent(type="text", text="Error: Not connected to Bedrock AgentCore")]
                )
            
            try:
                result = await self.bedrock_client.read_resource(uri)
                return result
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[TextContent(type="text", text=f"Error reading resource: {str(e)}")]
                )
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> ListPromptsResult:
            """List available prompts from Bedrock AgentCore."""
            if not self.bedrock_client:
                return ListPromptsResult(prompts=[])
            
            try:
                result = await self.bedrock_client.list_prompts()
                return result
            except Exception as e:
                logger.error(f"Error listing prompts: {e}")
                return ListPromptsResult(prompts=[])
        
        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Optional[dict] = None) -> GetPromptResult:
            """Get a prompt from Bedrock AgentCore."""
            if not self.bedrock_client:
                return GetPromptResult(
                    description="Error: Not connected to Bedrock AgentCore",
                    messages=[]
                )
            
            try:
                result = await self.bedrock_client.get_prompt(name, arguments)
                return result
            except Exception as e:
                logger.error(f"Error getting prompt {name}: {e}")
                return GetPromptResult(
                    description=f"Error getting prompt: {str(e)}",
                    messages=[]
                )
    
    async def connect_to_bedrock(self):
        """Establish connection to Bedrock AgentCore."""
        try:
            self.bedrock_client = BedrockMCPClient()
            await self.bedrock_client.connect()
            logger.info("Successfully connected to Bedrock AgentCore Runtime")
        except Exception as e:
            logger.error(f"Failed to connect to Bedrock AgentCore: {e}")
            raise
    
    async def disconnect_from_bedrock(self):
        """Disconnect from Bedrock AgentCore."""
        if self.bedrock_client:
            await self.bedrock_client.disconnect()
            logger.info("Disconnected from Bedrock AgentCore Runtime")
    
    async def run(self):
        """Run the MCP server."""
        # Connect to Bedrock AgentCore
        await self.connect_to_bedrock()
        
        try:
            # Run the MCP server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream, 
                    write_stream, 
                    InitializationOptions(
                        server_name="bedrock-mcp-proxy",
                        server_version="0.1.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities=None,
                        ),
                    ),
                )
        finally:
            # Ensure we disconnect even if server fails
            await self.disconnect_from_bedrock()


async def main():
    """Main entry point for the MCP server."""
    try:
        proxy_server = BedrockMCPProxyServer()
        await proxy_server.run()
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


def cli():
    """Command line interface entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()