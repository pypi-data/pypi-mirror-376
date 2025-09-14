#!/usr/bin/env python3
"""Test script for YouTube MCP Server."""

import asyncio
from fastmcp import Client
from youtube_mcp_server import server

async def test_server():
    """Test the server with a sample YouTube URL."""
    async with Client(server) as client:
        try:
            # Test getting video info
            print("Testing get_video_info...")
            result = await client.call_tool("get_video_info", {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            })
            print("Video info result:", result)
            
            # Test listing available formats
            print("\nTesting list_available_formats...")
            formats_result = await client.call_tool("list_available_formats", {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            })
            print("Formats result:", formats_result)
            
        except Exception as e:
            print(f"Test failed with error: {e}")
            
if __name__ == "__main__":
    asyncio.run(test_server())