# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Literal, Required, TypedDict

__all__ = ["McpToolCallParam"]


class McpToolCallParam(TypedDict, total=False):
    id: Required[str]
    """The unique ID of the tool call."""

    arguments: Required[str]
    """A JSON string of the arguments passed to the tool."""

    name: Required[str]
    """The name of the tool that was run."""

    server_label: Required[str]
    """The label of the MCP server running the tool."""

    type: Required[Literal["mcp_call"]]
    """The type of the item. Always `mcp_call`."""

    error: Optional[str]
    """The error from the tool call, if any."""

    output: Optional[str]
    """The output from the tool call."""
