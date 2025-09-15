import json
import os
from pathlib import Path

def load_tf_plan(plan_file: str) -> dict:
    """Load Terraform plan JSON with security and error handling."""
    try:
        # Resolve and validate path to prevent traversal attacks
        path = Path(plan_file).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Plan file not found: {plan_file}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {plan_file}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in plan file: {e}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {plan_file}")

def flatten_tag_values(tag_value: str):
    """Convert string like '[dev,uat]' to list ['dev', 'uat']"""
    tag_value = tag_value.strip()
    if tag_value.startswith('[') and tag_value.endswith(']'):
        content = tag_value[1:-1].strip()
        if not content:  # Handle empty list case
            return []
        return [v.strip() for v in content.split(',') if v.strip()]
    return [tag_value]