"""
MCP (Model Context Protocol) markers for xplainable-client methods.

This module provides a decorator to mark which client methods should be 
exposed through the MCP server interface.
"""

import inspect
from functools import wraps
from typing import Any, Callable, Dict, List
from enum import Enum


class MCPCategory(Enum):
    """Categories for MCP tools."""
    READ = "read"
    WRITE = "write"
    ANALYSIS = "analysis"
    ADMIN = "admin"
    INFERENCE = "inference"


# Global registry of MCP-eligible methods
_MCP_REGISTRY: Dict[str, Dict[str, Any]] = {}


def mcp_tool(category: MCPCategory) -> Callable:
    """
    Decorator to mark a method for MCP exposure with an explicit category.
    All other metadata is extracted from the function itself (signature, docstring, etc).
    
    Args:
        category: The category for this tool (required)
    
    Example:
        @mcp_tool(category=MCPCategory.READ)
        def list_team_models(self, limit: int = 100):
            '''List all models for the current team.'''
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Extract all metadata from the function
        signature = inspect.signature(func)
        docstring = inspect.getdoc(func) or ""
        
        # Extract parameters with type hints
        params = {}
        for param_name, param in signature.parameters.items():
            if param_name in ['self', 'cls']:
                continue
                
            param_info = {
                'name': param_name,
                'type': None,
                'default': param.default if param.default != inspect.Parameter.empty else None,
                'required': param.default == inspect.Parameter.empty
            }
            
            # Get type hint
            if param.annotation != inspect.Parameter.empty:
                param_info['type'] = param.annotation
                
            params[param_name] = param_info
        
        # Register in global registry
        full_name = f"{func.__module__}.{func.__qualname__}"
        _MCP_REGISTRY[full_name] = {
            'function': func,
            'name': func.__name__,
            'signature': signature,
            'docstring': docstring,
            'category': category,
            'parameters': params,
            'module_path': func.__module__,
            'qualname': func.__qualname__
        }
        
        # Add marker attribute to function
        func._is_mcp_tool = True
        func._mcp_category = category
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def get_mcp_registry() -> Dict[str, Dict[str, Any]]:
    """Get the complete MCP registry with all metadata."""
    return _MCP_REGISTRY.copy()


def generate_mcp_tool_code(method_path: str) -> str:
    """
    Generate complete MCP server tool code for a registered method.
    
    Args:
        method_path: Full path to the method in the registry
        
    Returns:
        Complete Python code string for the MCP tool
    """
    if method_path not in _MCP_REGISTRY:
        raise ValueError(f"Method {method_path} not found in MCP registry")
    
    metadata = _MCP_REGISTRY[method_path]
    
    # Extract the client module name (e.g., 'models' from 'ModelsClient')
    qualname_parts = metadata['qualname'].split('.')
    if len(qualname_parts) >= 2 and qualname_parts[-2].endswith('Client'):
        client_module = qualname_parts[-2].replace('Client', '').lower()
    else:
        # Fallback to extracting from module path
        module_parts = metadata['module_path'].split('.')
        client_module = module_parts[-1] if len(module_parts) > 0 else 'client'
    
    method_name = metadata['name']
    
    # Build parameter list for function signature
    param_strings = []
    arg_strings = []
    
    for param_name, param_info in metadata['parameters'].items():
        # Build parameter with type hint and default
        param_str = param_name
        
        # Add type hint if available
        if param_info['type']:
            type_str = _format_type_hint(param_info['type'])
            param_str = f"{param_name}: {type_str}"
        
        # Add default value if present
        if not param_info['required']:
            default_repr = repr(param_info['default'])
            param_str = f"{param_str} = {default_repr}"
            
        param_strings.append(param_str)
        arg_strings.append(param_name)
    
    params_signature = ', '.join(param_strings)
    args_call = ', '.join(arg_strings)
    
    # Extract first line of docstring for description
    docstring_lines = metadata['docstring'].split('\n')
    description = docstring_lines[0] if docstring_lines else f"Execute {method_name}"
    
    # Check if we need additional imports for model types
    model_imports = set()
    for param_info in metadata['parameters'].values():
        if param_info['type']:
            type_str = str(param_info['type'])
            if 'xplainable_client.client.py_models' in type_str:
                model_imports.add(type_str.split()[0])  # Extract the module path
    
    # Generate imports if needed
    import_lines = ""
    if model_imports:
        for import_path in sorted(model_imports):
            import_lines += f"import {import_path}\n"
    
    # Generate the complete function code
    code = f'''{import_lines}
@mcp.tool()
def {client_module}_{method_name}({params_signature}):
    """
    {description}
    
    Category: {metadata['category'].value}
    Client method: {client_module}.{method_name}
    """
    try:
        client = get_client()
        result = client.{client_module}.{method_name}({args_call})
        logger.info(f"Executed {client_module}.{method_name}")
        
        # Handle different return types
        if hasattr(result, 'model_dump'):
            return result.model_dump()
        elif isinstance(result, list) and result and hasattr(result[0], 'model_dump'):
            return [item.model_dump() for item in result]
        else:
            return result
    except Exception as e:
        logger.error(f"Error in {client_module}_{method_name}: {{e}}")
        raise
'''
    
    return code


def _format_type_hint(type_hint) -> str:
    """Format a type hint for code generation."""
    import typing
    
    # Check for generic types first (which have both __origin__ and __args__)
    if hasattr(type_hint, '__origin__') and hasattr(type_hint, '__args__') and type_hint.__args__:
        # For generic types like Dict[str, Any], List[int], etc.
        origin = type_hint.__origin__
        args = type_hint.__args__
        
        # Special handling for Union types (including Optional)
        if origin is typing.Union:
            # Check if this is Optional (Union[X, NoneType])
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
                inner_type = _format_type_hint(non_none_type)
                return f"Optional[{inner_type}]"
            else:
                # Regular Union
                formatted_args = [_format_type_hint(arg) for arg in args]
                return f"Union[{', '.join(formatted_args)}]"
        
        # Map built-in types to their typing counterparts
        type_mapping = {
            dict: 'Dict',
            list: 'List',
            tuple: 'Tuple',
            set: 'Set',
            frozenset: 'FrozenSet'
        }
        
        if origin in type_mapping:
            origin_name = type_mapping[origin]
        elif hasattr(origin, '__name__'):
            origin_name = origin.__name__
        else:
            origin_name = str(origin).replace('typing.', '')
        
        # Format the arguments recursively
        formatted_args = []
        for arg in args:
            if arg is type(None):
                formatted_args.append('None')
            else:
                formatted_args.append(_format_type_hint(arg))
        return f"{origin_name}[{', '.join(formatted_args)}]"
    
    # Handle simple types with __name__
    elif hasattr(type_hint, '__name__'):
        return type_hint.__name__
    
    # Handle non-generic types with __origin__ but no __args__
    elif hasattr(type_hint, '__origin__'):
        origin = type_hint.__origin__
        if hasattr(origin, '__name__'):
            return origin.__name__
        else:
            return str(origin).replace('typing.', '')
    
    # Fallback to string processing
    else:
        type_str = str(type_hint)
        # Replace typing module references and clean up
        type_str = type_str.replace('typing.', '')
        return type_str


def scan_client_for_mcp_tools(client_module) -> List[Dict[str, Any]]:
    """
    Scan a client module for methods marked with @mcp_tool.
    
    Args:
        client_module: The module to scan
        
    Returns:
        List of method metadata dictionaries
    """
    mcp_methods = []
    
    # Scan all classes in the module
    for name, obj in inspect.getmembers(client_module, inspect.isclass):
        if name.endswith('Client'):
            # Scan methods in the client class
            for method_name, method in inspect.getmembers(obj, inspect.ismethod):
                if hasattr(method, '_is_mcp_tool'):
                    full_path = f"{client_module.__name__}.{name}.{method_name}"
                    if full_path in _MCP_REGISTRY:
                        mcp_methods.append(_MCP_REGISTRY[full_path])
    
    return mcp_methods


def export_mcp_tools_to_file(output_path: str):
    """
    Export all MCP tool code to a Python file.
    
    Args:
        output_path: Path to write the generated code
    """
    lines = [
        "# Auto-generated MCP tools from xplainable-client",
        "# Generated using mcp_markers.py",
        "",
        "import logging",
        "from typing import Optional, List, Dict, Any",
        "from fastmcp import FastMCP",
        "",
        "logger = logging.getLogger(__name__)",
        "mcp = FastMCP('xplainable-mcp')",
        "",
        "# Import get_client function",
        "from .server import get_client",
        "",
        "# Generated MCP Tools",
        ""
    ]
    
    # Generate code for each method (sorted by module and method name)
    sorted_methods = sorted(
        _MCP_REGISTRY.items(),
        key=lambda x: (x[1]['module_path'], x[1]['name'])
    )
    
    for method_path, metadata in sorted_methods:
        try:
            tool_code = generate_mcp_tool_code(method_path)
            lines.append(tool_code)
        except Exception as e:
            lines.append(f"# Failed to generate tool for {method_path}: {e}")
            lines.append("")
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))