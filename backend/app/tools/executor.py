"""
Safe tool executor for AI Career Elevate.
Executes tools in a controlled environment with timeout protection.
"""
import asyncio
import concurrent.futures
import threading
import time
from typing import Any, Dict, Optional
from .registry import TOOLS, ToolResult, validate_tool_parameters


class ToolExecutionError(Exception):
    """Custom exception for tool execution errors."""
    pass


class ToolTimeoutError(ToolExecutionError):
    """Exception raised when tool execution times out."""
    pass


class ToolExecutor:
    """Safe tool executor with timeout and thread isolation."""
    
    def __init__(self, max_workers: int = 4):
        """
        Initialize the tool executor.
        
        Args:
            max_workers: Maximum number of worker threads for tool execution
        """
        self.max_workers = max_workers
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="tool_executor"
        )
    
    def run_tool(
        self, 
        name: str, 
        args: Dict[str, Any], 
        timeout: int = 6
    ) -> Dict[str, Any]:
        """
        Execute a tool with timeout protection.
        
        Args:
            name: Tool name
            args: Tool arguments
            timeout: Timeout in seconds (default: 6)
            
        Returns:
            Dict with 'success', 'output', and 'error' keys
        """
        try:
            # Validate tool exists
            if name not in TOOLS:
                return {
                    "success": False,
                    "output": "",
                    "error": f"Tool '{name}' not found in registry"
                }
            
            # Validate parameters
            if not validate_tool_parameters(name, args):
                return {
                    "success": False,
                    "output": "",
                    "error": f"Invalid parameters for tool '{name}'"
                }
            
            # Get tool function
            tool = TOOLS[name]
            tool_function = tool["function"]
            
            # Execute tool with timeout
            future = self._executor.submit(self._execute_tool_safely, tool_function, args)
            
            try:
                result = future.result(timeout=timeout)
                return {
                    "success": result.success,
                    "output": result.output,
                    "error": result.error
                }
            
            except concurrent.futures.TimeoutError:
                # Cancel the future if possible
                future.cancel()
                return {
                    "success": False,
                    "output": "",
                    "error": f"Tool '{name}' execution timed out after {timeout} seconds"
                }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": f"Tool execution error: {str(e)}"
            }
    
    def _execute_tool_safely(self, tool_function, args: Dict[str, Any]) -> ToolResult:
        """
        Execute tool function in a controlled environment.
        
        Args:
            tool_function: The tool function to execute
            args: Tool arguments
            
        Returns:
            ToolResult object
        """
        try:
            # Execute the tool function
            result = tool_function(**args)
            
            # Ensure result is a ToolResult
            if not isinstance(result, ToolResult):
                return ToolResult(
                    success=False,
                    output="",
                    error="Tool function did not return a ToolResult"
                )
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Tool execution failed: {str(e)}"
            )
    
    def shutdown(self, wait: bool = True):
        """Shutdown the executor and cleanup resources."""
        self._executor.shutdown(wait=wait)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


# Global executor instance
_executor_instance: Optional[ToolExecutor] = None


def get_executor() -> ToolExecutor:
    """Get the global tool executor instance."""
    global _executor_instance
    if _executor_instance is None:
        _executor_instance = ToolExecutor()
    return _executor_instance


def run_tool(
    name: str, 
    args: Dict[str, Any], 
    timeout: int = 6
) -> Dict[str, Any]:
    """
    Convenience function to run a tool using the global executor.
    
    Args:
        name: Tool name
        args: Tool arguments
        timeout: Timeout in seconds (default: 6)
        
    Returns:
        Dict with 'success', 'output', and 'error' keys
    """
    executor = get_executor()
    return executor.run_tool(name, args, timeout)


def shutdown_executor():
    """Shutdown the global executor."""
    global _executor_instance
    if _executor_instance is not None:
        _executor_instance.shutdown()
        _executor_instance = None


# Cleanup on module unload
import atexit
atexit.register(shutdown_executor)
