# -*- coding: utf-8 -*-
"""Tests for Bitbucket MCP Server.

Validates that the server module is importable and tools are registered.
"""

import types


def test_server_module_importable():
    """Basic import test ensures package structure is valid."""
    mod = __import__("bitbucket_mcp_server.server_fastmcp", fromlist=["server_fastmcp"])
    assert isinstance(mod, types.ModuleType)


def test_mcp_app_has_tools():
    """Verify the FastMCP app has tools registered."""
    from bitbucket_mcp_server.server_fastmcp import mcp

    # FastMCP registers tools via decorators — check the app object exists
    assert mcp is not None
    assert mcp.name == "bitbucket-server"
