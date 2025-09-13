"""Client for connecting to Amazon Bedrock AgentCore Runtime MCP server."""

import asyncio
import os
import sys
from typing import Optional

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


class BedrockMCPClient:
    def __init__(self):
        # Hardcoded values
        self.agent_arn = "arn:aws:bedrock-agentcore:us-east-1:654654574429:runtime/opsguide_mcp_server_example-feNooQ7JbB"
        self.aws_region = "us-east-1"

        # Only API_KEY comes from environment
        self.bearer_token = os.getenv("API_KEY")

        if not self.bearer_token:
            raise ValueError("API_KEY environment variable must be set")

        encoded_arn = self.agent_arn.replace(":", "%3A").replace("/", "%2F")
        self.mcp_url = f"https://bedrock-agentcore.{self.aws_region}.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }
        self.timeout = 120  # Default timeout in seconds
        self.session = None
        self.read_stream = None
        self.write_stream = None
        self.close_fn = None

    async def connect(self):
        """Establish connection to the Bedrock AgentCore runtime."""
        self.read_stream, self.write_stream, self.close_fn = (
            await streamablehttp_client(
                self.mcp_url,
                self.headers,
                timeout=self.timeout,
                terminate_on_close=False,
            ).__aenter__()
        )

        self.session = ClientSession(self.read_stream, self.write_stream)
        await self.session.__aenter__()
        await self.session.initialize()

    async def disconnect(self):
        """Close the connection to Bedrock AgentCore runtime."""
        if self.session:
            await self.session.__aexit__(None, None, None)
            self.session = None

        if hasattr(self, "close_fn") and self.close_fn:
            await self.close_fn()

    async def list_tools(self):
        """List available tools from the Bedrock AgentCore runtime."""
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
        return await self.session.list_tools()

    async def call_tool(self, name: str, arguments: dict):
        """Call a tool on the Bedrock AgentCore runtime.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
        return await self.session.call_tool(name, arguments)

    async def list_resources(self):
        """List available resources from the Bedrock AgentCore runtime."""
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
        return await self.session.list_resources()

    async def read_resource(self, uri: str):
        """Read a resource from the Bedrock AgentCore runtime.

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
        return await self.session.read_resource(uri)

    async def list_prompts(self):
        """List available prompts from the Bedrock AgentCore runtime."""
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
        return await self.session.list_prompts()

    async def get_prompt(self, name: str, arguments: Optional[dict] = None):
        """Get a prompt from the Bedrock AgentCore runtime.

        Args:
            name: Prompt name
            arguments: Prompt arguments

        Returns:
            Prompt result
        """
        if not self.session:
            raise RuntimeError("Not connected. Call connect() first.")
        return await self.session.get_prompt(name, arguments)
