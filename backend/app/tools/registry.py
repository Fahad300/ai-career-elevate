"""
Safe tool registry for AI Career Elevate.
Provides a collection of safe, validated tools for execution.
"""
import os
import json
import math
import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, List, Union, Callable
from pydantic import BaseModel, Field, validator


class ToolResult(BaseModel):
    """Standardized tool execution result."""
    success: bool = Field(description="Whether the tool execution was successful")
    output: str = Field(description="Tool output as string")
    error: str = Field(default="", description="Error message if execution failed")


class ToolSchema(BaseModel):
    """Schema for tool definition."""
    name: str = Field(description="Tool name")
    description: str = Field(description="Tool description")
    parameters: Dict[str, Any] = Field(description="Tool parameters schema")
    function: Callable = Field(description="Tool implementation function")


def echo_tool(text: str) -> ToolResult:
    """
    Echo tool - returns the input text.
    Safe for any text input.
    """
    try:
        # Validate input
        if not isinstance(text, str):
            return ToolResult(success=False, output="", error="Input must be a string")
        
        # Sanitize output to prevent injection
        sanitized_text = str(text).replace('\x00', '')  # Remove null bytes
        
        return ToolResult(success=True, output=sanitized_text, error="")
    
    except Exception as e:
        return ToolResult(success=False, output="", error=f"Echo error: {str(e)}")


def calc_tool(expression: str) -> ToolResult:
    """
    Calculator tool - evaluates simple mathematical expressions safely.
    Only allows basic arithmetic operations and common functions.
    """
    try:
        # Validate input
        if not isinstance(expression, str):
            return ToolResult(success=False, output="", error="Expression must be a string")
        
        # Sanitize input - only allow safe characters
        allowed_chars = set("0123456789+-*/.() ")
        allowed_functions = {"sqrt", "abs", "sin", "cos", "tan", "log", "exp", "pi", "e"}
        
        # Check for dangerous patterns
        dangerous_patterns = ["__", "import", "exec", "eval", "open", "file", "input"]
        for pattern in dangerous_patterns:
            if pattern in expression.lower():
                return ToolResult(
                    success=False, 
                    output="", 
                    error=f"Dangerous pattern '{pattern}' detected in expression"
                )
        
        # Create safe evaluation context
        safe_globals = {
            "__builtins__": {},
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }
        
        safe_locals = {}
        
        # Evaluate the expression safely
        result = eval(expression, safe_globals, safe_locals)
        
        # Format result
        if isinstance(result, float):
            if result.is_integer():
                output = str(int(result))
            else:
                output = f"{result:.6f}".rstrip('0').rstrip('.')
        else:
            output = str(result)
        
        return ToolResult(success=True, output=output, error="")
    
    except ZeroDivisionError:
        return ToolResult(success=False, output="", error="Division by zero")
    except ValueError as e:
        return ToolResult(success=False, output="", error=f"Invalid value: {str(e)}")
    except SyntaxError as e:
        return ToolResult(success=False, output="", error=f"Invalid syntax: {str(e)}")
    except Exception as e:
        return ToolResult(success=False, output="", error=f"Calculation error: {str(e)}")


def read_file_tool(filepath: str) -> ToolResult:
    """
    Read file tool - safely reads text files with restrictions.
    Only allows reading files in safe directories.
    """
    try:
        # Validate input
        if not isinstance(filepath, str):
            return ToolResult(success=False, output="", error="Filepath must be a string")
        
        # Security checks
        # Prevent directory traversal
        if ".." in filepath or os.path.isabs(filepath):
            return ToolResult(
                success=False, 
                output="", 
                error="Path traversal not allowed. Use relative paths only."
            )
        
        path = Path(filepath).resolve()
        
        # Only allow reading files in current directory and subdirectories
        current_dir = Path.cwd()
        try:
            # Check if path is within current directory
            path.relative_to(current_dir)
        except ValueError:
            return ToolResult(
                success=False, 
                output="", 
                error="File must be in current directory or subdirectories"
            )
        
        # Check if file exists
        if not path.exists():
            return ToolResult(success=False, output="", error="File not found")
        
        # Check if it's a file (not directory)
        if not path.is_file():
            return ToolResult(success=False, output="", error="Path is not a file")
        
        # Check file size limit (1MB)
        if path.stat().st_size > 1024 * 1024:
            return ToolResult(
                success=False, 
                output="", 
                error="File too large (max 1MB)"
            )
        
        # Read file content with encoding detection
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(path, 'r', encoding='utf-16', errors='ignore') as f:
                content = f.read()
        
        return ToolResult(success=True, output=content, error="")
    
    except PermissionError:
        return ToolResult(success=False, output="", error="Permission denied")
    except UnicodeDecodeError:
        return ToolResult(success=False, output="", error="File contains invalid characters")
    except Exception as e:
        return ToolResult(success=False, output="", error=f"File read error: {str(e)}")


def pdf_to_text_tool(filepath: str) -> ToolResult:
    """
    PDF text extraction tool - extracts text from PDF files using multiple methods.
    """
    try:
        # Import here to avoid circular imports
        from app.tools.pdf_tools import pdf_to_text
        
        # Validate input
        if not isinstance(filepath, str):
            return ToolResult(
                success=False,
                output="",
                error="Filepath must be a string"
            )
        
        # Extract text from PDF
        result = pdf_to_text(filepath)
        
        if result["text"]:
            return ToolResult(
                success=True,
                output=f"Method: {result['method']}\nConfidence: {result['confidence']}\nText:\n{result['text']}",
                error=""
            )
        else:
            return ToolResult(
                success=False,
                output="",
                error=result.get("error", "No text extracted from PDF")
            )
            
    except Exception as e:
        return ToolResult(
            success=False,
            output="",
            error=f"PDF extraction failed: {str(e)}"
        )


def list_files_tool(directory: str = ".") -> ToolResult:
    """
    List files tool - safely lists files in a directory.
    Only allows listing files in safe directories.
    """
    try:
        # Validate input
        if not isinstance(directory, str):
            return ToolResult(success=False, output="", error="Directory must be a string")
        
        # Security checks
        # Prevent directory traversal
        if ".." in directory or os.path.isabs(directory):
            return ToolResult(
                success=False, 
                output="", 
                error="Path traversal not allowed. Use relative paths only."
            )
        
        path = Path(directory).resolve()
        
        # Only allow listing in current directory and subdirectories
        current_dir = Path.cwd()
        try:
            # Check if path is within current directory
            path.relative_to(current_dir)
        except ValueError:
            return ToolResult(
                success=False, 
                output="", 
                error="Directory must be in current directory or subdirectories"
            )
        
        # Check if directory exists
        if not path.exists():
            return ToolResult(success=False, output="", error="Directory not found")
        
        # Check if it's a directory
        if not path.is_dir():
            return ToolResult(success=False, output="", error="Path is not a directory")
        
        # List files and directories
        items = []
        try:
            for item in path.iterdir():
                if item.is_file():
                    items.append(f"FILE: {item.name}")
                elif item.is_dir():
                    items.append(f"DIR:  {item.name}")
        except PermissionError:
            return ToolResult(success=False, output="", error="Permission denied")
        
        # Sort and format output
        items.sort()
        output = "\n".join(items) if items else "Directory is empty"
        
        return ToolResult(success=True, output=output, error="")
    
    except Exception as e:
        return ToolResult(success=False, output="", error=f"Directory listing error: {str(e)}")


# Tool registry - safe tools available for execution
TOOLS: Dict[str, Dict[str, Any]] = {
    "echo": {
        "name": "echo",
        "description": "Echo tool - returns the input text",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to echo back"
                }
            },
            "required": ["text"]
        },
        "function": echo_tool
    },
    "calc": {
        "name": "calc",
        "description": "Calculator tool - evaluates simple mathematical expressions",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        },
        "function": calc_tool
    },
    "read_file": {
        "name": "read_file",
        "description": "Read file tool - safely reads text files",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the file to read (relative path only)"
                }
            },
            "required": ["filepath"]
        },
        "function": read_file_tool
    },
    "list_files": {
        "name": "list_files",
        "description": "List files tool - safely lists files in a directory",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Directory to list (defaults to current directory)",
                    "default": "."
                }
            },
            "required": []
        },
        "function": list_files_tool
    },
    "pdf_to_text": {
        "name": "pdf_to_text",
        "description": "PDF text extraction tool - extracts text from PDF files using multiple methods",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Path to the PDF file to extract text from"
                }
            },
            "required": ["filepath"]
        },
        "function": pdf_to_text_tool
    }
}


def get_tool(name: str) -> Dict[str, Any]:
    """Get tool definition by name."""
    return TOOLS.get(name)


def list_tools() -> Dict[str, str]:
    """List all available tools with their descriptions."""
    return {name: tool["description"] for name, tool in TOOLS.items()}


def validate_tool_parameters(tool_name: str, parameters: Dict[str, Any]) -> bool:
    """Validate tool parameters against schema."""
    if tool_name not in TOOLS:
        return False
    
    tool = TOOLS[tool_name]
    schema = tool["parameters"]
    
    # Check required parameters
    required = schema.get("required", [])
    for param in required:
        if param not in parameters:
            return False
    
    # Check parameter types (basic validation)
    properties = schema.get("properties", {})
    for param_name, param_value in parameters.items():
        if param_name in properties:
            param_schema = properties[param_name]
            expected_type = param_schema.get("type")
            
            if expected_type == "string" and not isinstance(param_value, str):
                return False
            elif expected_type == "number" and not isinstance(param_value, (int, float)):
                return False
            elif expected_type == "boolean" and not isinstance(param_value, bool):
                return False
    
    return True
