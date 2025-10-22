from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

from app.tools import run_tool, list_tools, get_tool, TOOLS

router = APIRouter(prefix="/tool", tags=["tool"])


class ToolExecutionRequest(BaseModel):
    name: str
    args: Dict[str, Any]
    timeout: int = 6


class ToolExecutionResponse(BaseModel):
    success: bool
    output: str
    error: str


@router.get("/list")
def list_available_tools() -> Dict[str, str]:
    """List all available tools with their descriptions."""
    return list_tools()


@router.get("/{tool_name}")
def get_tool_info(tool_name: str) -> Dict[str, Any]:
    """Get information about a specific tool."""
    tool = get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return {
        "name": tool["name"],
        "description": tool["description"],
        "parameters": tool["parameters"]
    }


@router.post("/execute", response_model=ToolExecutionResponse)
def execute_tool(request: ToolExecutionRequest) -> ToolExecutionResponse:
    """Execute a tool with the given arguments."""
    try:
        result = run_tool(request.name, request.args, request.timeout)
        return ToolExecutionResponse(
            success=result["success"],
            output=result["output"],
            error=result["error"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tool execution failed: {str(e)}"
        )