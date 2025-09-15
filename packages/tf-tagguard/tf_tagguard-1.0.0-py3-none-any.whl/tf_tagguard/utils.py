import json
import os
import subprocess
import re
from pathlib import Path
from typing import Set, Tuple, List

# File Operations
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

# Tag Processing
def flatten_tag_values(tag_value: str) -> List[str]:
    """Convert string like '[dev,uat]' to list ['dev', 'uat']"""
    tag_value = tag_value.strip()
    if tag_value.startswith('[') and tag_value.endswith(']'):
        content = tag_value[1:-1].strip()
        if not content:  # Handle empty list case
            return []
        return [v.strip() for v in content.split(',') if v.strip()]
    return [tag_value]

# Terraform Integration
def get_terraform_version() -> str:
    """Fetch the current Terraform version installed."""
    try:
        result = subprocess.run(["terraform", "version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return "unknown"
        
        match = re.search(r"Terraform v(\d+\.\d+\.\d+)", result.stdout)
        return match.group(1) if match else "unknown"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "unknown"

def get_taggable_resources() -> Tuple[Set[str], str]:
    """
    Fetch all AWS resource types that support tagging dynamically.
    Returns: (taggable_resources_set, provider_version)
    """
    try:
        result = subprocess.run(
            ["terraform", "providers", "schema", "-json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return set(), "unknown"

        provider_schema = json.loads(result.stdout)
        taggable_resources = set()
        
        # Get AWS provider info
        aws_provider = provider_schema.get("provider_schemas", {}).get("registry.terraform.io/hashicorp/aws", {})
        provider_version = aws_provider.get("provider", {}).get("version", "unknown")
        
        aws_resources = aws_provider.get("resource_schemas", {})

        for resource, schema in aws_resources.items():
            attributes = schema.get("block", {}).get("attributes", {})
            if "tags" in attributes or "tags_all" in attributes:
                taggable_resources.add(resource)

        return taggable_resources, provider_version
        
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return set(), "unknown"

# Resource Filtering
def should_validate_resource(resource: dict, delta_only: bool = False) -> bool:
    """
    Determine if a resource should be validated based on actions.
    
    Args:
        resource: Resource from Terraform plan
        delta_only: If True, only validate create/update/replace actions
    
    Returns:
        bool: True if resource should be validated
    """
    if not delta_only:
        return True
        
    actions = resource.get("change", {}).get("actions", [])
    return any(action in ["create", "update", "replace"] for action in actions)

def extract_resource_tags(resource: dict) -> dict:
    """Extract and combine tags from both 'tags' and 'tags_all' fields."""
    after_config = resource.get("change", {}).get("after", {})
    tags = after_config.get("tags", {})
    tags_all = after_config.get("tags_all", {})
    
    # Combine tags for validation (tags override tags_all)
    return {**tags_all, **tags}