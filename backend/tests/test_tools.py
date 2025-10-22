"""
Comprehensive tests for the tool registry and executor.
Tests safety, functionality, and edge cases.
"""
import pytest
import tempfile
import os
import time
import threading
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.tools.registry import (
    TOOLS, 
    ToolResult, 
    echo_tool, 
    calc_tool, 
    read_file_tool, 
    list_files_tool,
    get_tool,
    list_tools,
    validate_tool_parameters
)
from app.tools.executor import ToolExecutor, run_tool, get_executor, shutdown_executor


class TestToolRegistry:
    """Test the tool registry functionality."""
    
    def test_tools_dict_exists(self):
        """Test that TOOLS dict is properly defined."""
        assert isinstance(TOOLS, dict)
        assert len(TOOLS) >= 4
        assert "echo" in TOOLS
        assert "calc" in TOOLS
        assert "read_file" in TOOLS
        assert "list_files" in TOOLS
    
    def test_tool_schema_structure(self):
        """Test that each tool has proper schema structure."""
        for tool_name, tool_def in TOOLS.items():
            assert "name" in tool_def
            assert "description" in tool_def
            assert "parameters" in tool_def
            assert "function" in tool_def
            assert tool_def["name"] == tool_name
            assert callable(tool_def["function"])
    
    def test_get_tool(self):
        """Test getting tool by name."""
        echo_tool_def = get_tool("echo")
        assert echo_tool_def is not None
        assert echo_tool_def["name"] == "echo"
        
        # Test non-existent tool
        assert get_tool("non_existent") is None
    
    def test_list_tools(self):
        """Test listing all tools."""
        tools_list = list_tools()
        assert isinstance(tools_list, dict)
        assert "echo" in tools_list
        assert "calc" in tools_list
        assert "read_file" in tools_list
        assert "list_files" in tools_list


class TestToolValidation:
    """Test tool parameter validation."""
    
    def test_validate_tool_parameters_valid(self):
        """Test valid tool parameters."""
        # Test echo tool
        assert validate_tool_parameters("echo", {"text": "hello"})
        
        # Test calc tool
        assert validate_tool_parameters("calc", {"expression": "2 + 2"})
        
        # Test read_file tool
        assert validate_tool_parameters("read_file", {"filepath": "test.txt"})
        
        # Test list_files tool (optional parameter)
        assert validate_tool_parameters("list_files", {})
        assert validate_tool_parameters("list_files", {"directory": "."})
    
    def test_validate_tool_parameters_invalid(self):
        """Test invalid tool parameters."""
        # Test non-existent tool
        assert not validate_tool_parameters("non_existent", {})
        
        # Test missing required parameters
        assert not validate_tool_parameters("echo", {})
        assert not validate_tool_parameters("calc", {})
        assert not validate_tool_parameters("read_file", {})
        
        # Test wrong parameter types
        assert not validate_tool_parameters("echo", {"text": 123})
        assert not validate_tool_parameters("calc", {"expression": 123})


class TestEchoTool:
    """Test the echo tool functionality."""
    
    def test_echo_basic(self):
        """Test basic echo functionality."""
        result = echo_tool("Hello World")
        assert result.success is True
        assert result.output == "Hello World"
        assert result.error == ""
    
    def test_echo_empty_string(self):
        """Test echo with empty string."""
        result = echo_tool("")
        assert result.success is True
        assert result.output == ""
        assert result.error == ""
    
    def test_echo_special_characters(self):
        """Test echo with special characters."""
        special_text = "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?"
        result = echo_tool(special_text)
        assert result.success is True
        assert result.output == special_text
        assert result.error == ""
    
    def test_echo_null_bytes(self):
        """Test echo sanitizes null bytes."""
        text_with_nulls = "Hello\x00World"
        result = echo_tool(text_with_nulls)
        assert result.success is True
        assert result.output == "HelloWorld"  # Null bytes removed
        assert result.error == ""
    
    def test_echo_invalid_input(self):
        """Test echo with invalid input types."""
        result = echo_tool(123)
        assert result.success is False
        assert result.output == ""
        assert "Input must be a string" in result.error
        
        result = echo_tool(None)
        assert result.success is False
        assert result.output == ""
        assert "Input must be a string" in result.error


class TestCalcTool:
    """Test the calculator tool functionality."""
    
    def test_calc_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        # Addition
        result = calc_tool("2 + 3")
        assert result.success is True
        assert result.output == "5"
        
        # Subtraction
        result = calc_tool("10 - 4")
        assert result.success is True
        assert result.output == "6"
        
        # Multiplication
        result = calc_tool("3 * 4")
        assert result.success is True
        assert result.output == "12"
        
        # Division
        result = calc_tool("15 / 3")
        assert result.success is True
        assert result.output == "5"
    
    def test_calc_complex_expressions(self):
        """Test complex mathematical expressions."""
        # Parentheses
        result = calc_tool("(2 + 3) * 4")
        assert result.success is True
        assert result.output == "20"
        
        # Multiple operations
        result = calc_tool("2 + 3 * 4 - 1")
        assert result.success is True
        assert result.output == "13"
        
        # Decimal numbers
        result = calc_tool("3.14 * 2")
        assert result.success is True
        assert float(result.output) == pytest.approx(6.28, rel=1e-5)
    
    def test_calc_math_functions(self):
        """Test mathematical functions."""
        # Square root
        result = calc_tool("sqrt(16)")
        assert result.success is True
        assert result.output == "4"
        
        # Absolute value
        result = calc_tool("abs(-5)")
        assert result.success is True
        assert result.output == "5"
        
        # Power
        result = calc_tool("pow(2, 3)")
        assert result.success is True
        assert result.output == "8"
        
        # Trigonometric functions
        result = calc_tool("sin(0)")
        assert result.success is True
        assert float(result.output) == pytest.approx(0.0, abs=1e-6)
    
    def test_calc_constants(self):
        """Test mathematical constants."""
        result = calc_tool("pi")
        assert result.success is True
        assert float(result.output) == pytest.approx(3.14159, rel=1e-5)
        
        result = calc_tool("e")
        assert result.success is True
        assert float(result.output) == pytest.approx(2.71828, rel=1e-5)
    
    def test_calc_division_by_zero(self):
        """Test division by zero handling."""
        result = calc_tool("1 / 0")
        assert result.success is False
        assert result.output == ""
        assert "Division by zero" in result.error
    
    def test_calc_dangerous_patterns(self):
        """Test that dangerous patterns are blocked."""
        dangerous_expressions = [
            "__import__('os')",
            "exec('print(1)')",
            "eval('1+1')",
            "open('/etc/passwd')",
            "file('/etc/passwd')",
            "input()",
        ]
        
        for expr in dangerous_expressions:
            result = calc_tool(expr)
            assert result.success is False
            assert "Dangerous pattern" in result.error
    
    def test_calc_invalid_syntax(self):
        """Test invalid syntax handling."""
        result = calc_tool("2 +")
        assert result.success is False
        assert result.output == ""
        assert "Invalid syntax" in result.error
        
        result = calc_tool("(2 + 3")
        assert result.success is False
        assert result.output == ""
        assert "Invalid syntax" in result.error
    
    def test_calc_invalid_input(self):
        """Test invalid input types."""
        result = calc_tool(123)
        assert result.success is False
        assert result.output == ""
        assert "Expression must be a string" in result.error
        
        result = calc_tool(None)
        assert result.success is False
        assert result.output == ""
        assert "Expression must be a string" in result.error


class TestFileTools:
    """Test file-related tools."""
    
    def test_read_file_basic(self):
        """Test basic file reading."""
        # Create a test file in current directory
        test_file = "test_file.txt"
        with open(test_file, 'w') as f:
            f.write("Hello World")
        
        try:
            result = read_file_tool(test_file)
            assert result.success is True
            assert result.output == "Hello World"
            assert result.error == ""
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)
    
    def test_read_file_not_found(self):
        """Test reading non-existent file."""
        result = read_file_tool("non_existent_file.txt")
        assert result.success is False
        assert result.output == ""
        assert "File not found" in result.error
    
    def test_read_file_path_traversal(self):
        """Test path traversal prevention."""
        result = read_file_tool("../etc/passwd")
        assert result.success is False
        assert result.output == ""
        assert "Path traversal not allowed" in result.error
        
        result = read_file_tool("/etc/passwd")
        assert result.success is False
        assert result.output == ""
        assert "Path traversal not allowed" in result.error
    
    def test_list_files_basic(self):
        """Test basic directory listing."""
        result = list_files_tool(".")
        assert result.success is True
        assert "FILE:" in result.output or "DIR:" in result.output or "Directory is empty" in result.output
        assert result.error == ""
    
    def test_list_files_nonexistent(self):
        """Test listing non-existent directory."""
        result = list_files_tool("non_existent_dir")
        assert result.success is False
        assert result.output == ""
        assert "Directory not found" in result.error
    
    def test_list_files_path_traversal(self):
        """Test path traversal prevention in list_files."""
        result = list_files_tool("../")
        assert result.success is False
        assert result.output == ""
        assert "Path traversal not allowed" in result.error


class TestToolExecutor:
    """Test the tool executor functionality."""
    
    def test_executor_initialization(self):
        """Test executor initialization."""
        executor = ToolExecutor(max_workers=2)
        assert executor.max_workers == 2
        executor.shutdown()
    
    def test_run_tool_basic(self):
        """Test basic tool execution."""
        executor = ToolExecutor()
        try:
            result = executor.run_tool("echo", {"text": "Hello"})
            assert result["success"] is True
            assert result["output"] == "Hello"
            assert result["error"] == ""
        finally:
            executor.shutdown()
    
    def test_run_tool_calc(self):
        """Test calculator tool execution."""
        executor = ToolExecutor()
        try:
            result = executor.run_tool("calc", {"expression": "2 + 3"})
            assert result["success"] is True
            assert result["output"] == "5"
            assert result["error"] == ""
        finally:
            executor.shutdown()
    
    def test_run_tool_timeout(self):
        """Test tool execution timeout."""
        # Create a slow tool function
        def slow_tool(*args, **kwargs):
            time.sleep(2)  # Sleep for 2 seconds
            return ToolResult(success=True, output="done", error="")
        
        # Patch the echo tool to be slow
        with patch('app.tools.registry.echo_tool', side_effect=slow_tool):
            executor = ToolExecutor()
            try:
                result = executor.run_tool("echo", {"text": "test"}, timeout=1)
                assert result["success"] is False
                assert result["output"] == ""
                assert "timed out" in result["error"]
            finally:
                executor.shutdown()
    
    def test_run_tool_invalid_tool(self):
        """Test execution of non-existent tool."""
        executor = ToolExecutor()
        try:
            result = executor.run_tool("non_existent", {})
            assert result["success"] is False
            assert result["output"] == ""
            assert "not found in registry" in result["error"]
        finally:
            executor.shutdown()
    
    def test_run_tool_invalid_parameters(self):
        """Test execution with invalid parameters."""
        executor = ToolExecutor()
        try:
            result = executor.run_tool("echo", {})  # Missing required parameter
            assert result["success"] is False
            assert result["output"] == ""
            assert "Invalid parameters" in result["error"]
        finally:
            executor.shutdown()
    
    def test_run_tool_context_manager(self):
        """Test executor as context manager."""
        with ToolExecutor() as executor:
            result = executor.run_tool("echo", {"text": "test"})
            assert result["success"] is True
            assert result["output"] == "test"


class TestGlobalExecutor:
    """Test the global executor functionality."""
    
    def test_run_tool_global(self):
        """Test using the global run_tool function."""
        result = run_tool("echo", {"text": "global test"})
        assert result["success"] is True
        assert result["output"] == "global test"
        assert result["error"] == ""
    
    def test_get_executor(self):
        """Test getting the global executor instance."""
        executor = get_executor()
        assert isinstance(executor, ToolExecutor)
        
        # Should return the same instance
        executor2 = get_executor()
        assert executor is executor2
    
    def test_shutdown_executor(self):
        """Test shutting down the global executor."""
        executor = get_executor()
        shutdown_executor()
        
        # Getting executor after shutdown should create new instance
        executor2 = get_executor()
        assert executor is not executor2


class TestToolSafety:
    """Test tool safety and security features."""
    
    def test_calc_no_imports(self):
        """Test that calc tool cannot import modules."""
        dangerous_expressions = [
            "import os",
            "from os import system",
            "__import__('subprocess')",
            "exec('import os')",
        ]
        
        for expr in dangerous_expressions:
            result = calc_tool(expr)
            assert result.success is False
            assert result.error != ""
    
    def test_file_tools_security(self):
        """Test file tools security restrictions."""
        # Test absolute paths are blocked
        result = read_file_tool("/etc/passwd")
        assert result.success is False
        assert "Path traversal not allowed" in result.error
        
        result = list_files_tool("/etc")
        assert result.success is False
        assert "Path traversal not allowed" in result.error
    
    def test_tool_result_serialization(self):
        """Test that tool results can be serialized."""
        result = echo_tool("test")
        assert isinstance(result.success, bool)
        assert isinstance(result.output, str)
        assert isinstance(result.error, str)
        
        # Test result can be converted to dict
        result_dict = {
            "success": result.success,
            "output": result.output,
            "error": result.error
        }
        assert isinstance(result_dict, dict)
