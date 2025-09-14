#!/usr/bin/env python3
"""YouTube MCP Server using FastMCP and you-get."""

import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from fastmcp import FastMCP

server = FastMCP("YouTube MCP Server")


@server.tool
def download_youtube_video(
    url: str, 
    output_dir: Optional[str] = None,
    format_type: Optional[str] = None,
    info_only: bool = False
) -> Dict[str, Any]:
    """
    Download YouTube video using you-get.
    
    Args:
        url: YouTube video URL
        output_dir: Output directory (default: current directory)
        format_type: Video format preference (e.g., 'mp4', 'flv')
        info_only: If True, only return video information without downloading
    
    Returns:
        Dictionary with download status and information
    """
    try:
        # Build you-get command
        cmd = ["you-get"]
        
        if info_only:
            cmd.append("--info")
        
        if output_dir:
            cmd.extend(["--output-dir", str(output_dir)])
            
        if format_type:
            cmd.extend(["--format", format_type])
            
        cmd.append(url)
        
        # Execute command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Operation completed successfully",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            return {
                "status": "error", 
                "message": f"you-get command failed with code {result.returncode}",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Download timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }


@server.tool
def get_video_info(url: str) -> Dict[str, Any]:
    """
    Get video information without downloading.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Dictionary with video information
    """
    try:
        cmd = ["you-get", "--info", url]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Video information retrieved successfully",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            return {
                "status": "error", 
                "message": f"you-get command failed with code {result.returncode}",
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "message": "Command timed out after 60 seconds"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }


@server.tool
def list_available_formats(url: str) -> Dict[str, Any]:
    """
    List available video formats for a YouTube URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Dictionary with available formats information
    """
    try:
        cmd = ["you-get", "--info", "--debug", url]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        return {
            "status": "success" if result.returncode == 0 else "error",
            "message": "Format information retrieved" if result.returncode == 0 else f"Command failed with code {result.returncode}",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error getting format info: {str(e)}"
        }


def main():
    """Main entry point for the server."""
    server.run()


if __name__ == "__main__":
    main()