"""JSON Schema 2020-12 compliant utilities for MCP tools."""

import inspect
from typing import Dict, List, Optional, Union, get_type_hints, get_origin, get_args
from pydantic import BaseModel


def create_compliant_schema(func) -> Dict:
    """Create a JSON Schema 2020-12 compliant schema from function signature."""
    sig = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        if param_name == 'return':
            continue
            
        param_type = type_hints.get(param_name, str)
        param_schema = _convert_type_to_schema(param_type)
        
        # Extract description from docstring
        description = _extract_param_description(func.__doc__, param_name)
        if description:
            param_schema["description"] = description
        
        properties[param_name] = param_schema
        
        # Check if parameter is required (no default value)
        if param.default == inspect.Parameter.empty:
            required.append(param_name)
    
    # Create fully compliant JSON Schema 2020-12
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False
    }
    
    return schema


def _convert_type_to_schema(type_hint) -> Dict:
    """Convert Python type hint to JSON Schema 2020-12 format."""
    origin = get_origin(type_hint)
    args = get_args(type_hint)
    
    # Handle Optional[T] -> Union[T, None]
    if origin is Union:
        # Check if it's Optional (Union with None)
        if len(args) == 2 and type(None) in args:
            non_none_type = args[0] if args[1] is type(None) else args[1]
            base_schema = _convert_type_to_schema(non_none_type)
            return {
                "anyOf": [
                    base_schema,
                    {"type": "null"}
                ]
            }
        else:
            # Handle other Union types
            return {
                "anyOf": [_convert_type_to_schema(arg) for arg in args]
            }
    
    # Handle List[T]
    if origin is list or type_hint is list:
        if args:
            item_schema = _convert_type_to_schema(args[0])
            return {
                "type": "array",
                "items": item_schema
            }
        return {"type": "array"}
    
    # Handle Dict types
    if origin is dict or type_hint is dict:
        return {"type": "object"}
    
    # Handle basic types
    if type_hint is str:
        return {"type": "string"}
    elif type_hint is int:
        return {"type": "integer"}
    elif type_hint is float:
        return {"type": "number"}
    elif type_hint is bool:
        return {"type": "boolean"}
    
    # Handle Pydantic models
    if inspect.isclass(type_hint) and issubclass(type_hint, BaseModel):
        # Get Pydantic model schema and ensure 2020-12 compliance
        model_schema = type_hint.model_json_schema()
        
        # Convert definitions to $defs for 2020-12 compliance
        if "definitions" in model_schema:
            model_schema["$defs"] = model_schema.pop("definitions")
        
        # Ensure proper $schema
        model_schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        
        # Remove any OpenAPI-specific fields that might cause issues
        _clean_openapi_fields(model_schema)
        
        return model_schema
    
    # Default fallback
    return {"type": "string"}


def _clean_openapi_fields(schema: Dict) -> None:
    """Remove OpenAPI-specific fields that are not valid in JSON Schema 2020-12."""
    openapi_fields = ["nullable", "example", "examples", "discriminator", "xml"]
    
    def clean_recursive(obj):
        if isinstance(obj, dict):
            for field in openapi_fields:
                obj.pop(field, None)
            for value in obj.values():
                clean_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                clean_recursive(item)
    
    clean_recursive(schema)


def _extract_param_description(docstring: Optional[str], param_name: str) -> Optional[str]:
    """Extract parameter description from docstring."""
    if not docstring:
        return None
    
    lines = docstring.split('\n')
    in_args_section = False
    
    for line in lines:
        line = line.strip()
        if line.startswith('Args:'):
            in_args_section = True
            continue
        
        if in_args_section:
            if line.startswith('Returns:') or line.startswith('Raises:'):
                break
            
            if line.startswith(f'{param_name} (') or line.startswith(f'{param_name}:'):
                # Extract description after the type annotation
                if ':' in line:
                    desc = line.split(':', 1)[1].strip()
                    return desc
    
    return None
