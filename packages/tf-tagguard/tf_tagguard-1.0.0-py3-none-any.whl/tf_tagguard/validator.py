import re
from tabulate import tabulate
from .exceptions import TagValidationError
from .utils import (
    flatten_tag_values, 
    get_terraform_version, 
    get_taggable_resources, 
    should_validate_resource,
    extract_resource_tags
)

class TagValidator:
    def __init__(self, required_tags=None, value_tags=None, delta_only=False, use_terraform_detection=True):
        """
        :param required_tags: list of tag keys to check presence
        :param value_tags: dict {tag_key: expected_value/list/regex}
        :param delta_only: if True, only validate create/update/replace actions
        :param use_terraform_detection: if True, auto-detect taggable resources
        """
        self.required_tags = required_tags or []
        self.value_tags = value_tags or {}
        self.delta_only = delta_only
        self.use_terraform_detection = use_terraform_detection
        
        # Get Terraform info
        self.terraform_version = get_terraform_version()
        self.taggable_resources, self.provider_version = get_taggable_resources() if use_terraform_detection else (set(), "disabled")

        # Handle duplicate keys consistently
        duplicates = set(self.required_tags).intersection(self.value_tags.keys())
        if duplicates:
            # Remove duplicates from required_tags, value_tags take precedence
            self.required_tags = [t for t in self.required_tags if t not in duplicates]
            print(f"Warning: Tags {duplicates} declared in both -r and -v. Using -v values.")

    def validate(self, tf_plan: dict):
        """
        Validate tags on resources in Terraform plan.
        Returns: True if all pass, raises TagValidationError if any fail.
        """
        # Print Terraform info
        print(f"Using Terraform Version: {self.terraform_version}")
        if self.use_terraform_detection:
            print(f"AWS Provider Version: {self.provider_version}")
            print(f"Detected {len(self.taggable_resources)} taggable resource types")
        
        resources = tf_plan.get("resource_changes", [])
        errors = []
        skipped_resources = []
        validated_count = 0

        for res in resources:
            resource_type = res.get("type", "unknown_resource")
            resource_address = res.get("address", "unknown_resource")
            
            # Check if resource should be validated based on actions
            if not should_validate_resource(res, self.delta_only):
                continue
                
            # Check if resource is taggable (if detection enabled)
            if self.use_terraform_detection and resource_type not in self.taggable_resources:
                skipped_resources.append(resource_address)
                continue
                
            validated_count += 1
            
            # Extract and combine tags
            all_tags = extract_resource_tags(res)
            
            missing = [t for t in self.required_tags if t not in all_tags]
            invalid = []

            for k, v in self.value_tags.items():
                if k not in all_tags:
                    missing.append(k)
                else:
                    value = all_tags[k]
                    
                    # Determine validation type based on format
                    if v.startswith('[') and v.endswith(']'):
                        # List validation
                        allowed_values = flatten_tag_values(v)
                        if value not in allowed_values:
                            invalid.append(f"{k}={value} not in {allowed_values}")
                    elif v.startswith('^') or v.endswith('$') or ('.*' in v) or ('[0-9]' in v):
                        # Regex validation
                        try:
                            if not re.match(v, value):
                                invalid.append(f"{k}={value} does not match pattern {v}")
                        except re.error:
                            invalid.append(f"{k}={value} - invalid regex pattern {v}")
                    else:
                        # Exact value validation
                        if value != v:
                            invalid.append(f"{k}={value} != {v}")

            if missing or invalid:
                errors.append({
                    "resource": resource_address,
                    "missing_tags": missing,
                    "invalid_tags": invalid
                })

        # Print summary
        if self.delta_only:
            print(f"Validated {validated_count} resources (delta mode: create/update/replace only)")
        else:
            print(f"Validated {validated_count} resources (all resources)")
            
        if skipped_resources:
            print(f"\nSkipped {len(skipped_resources)} non-taggable resources:")
            for res in skipped_resources[:5]:  # Show first 5
                print(f"  - {res}")
            if len(skipped_resources) > 5:
                print(f"  ... and {len(skipped_resources) - 5} more")

        if errors:
            print(f"\nTag validation failed for {len(errors)} resources:\n")
            table = tabulate(
                [(e["resource"], ", ".join(e["missing_tags"]), ", ".join(e["invalid_tags"]))
                 for e in errors],
                headers=["Resource", "Missing Tags", "Invalid Tags"],
                tablefmt="github"
            )
            print(table)
            raise TagValidationError("Tag validation failed for some resources.")

        print(f"\nAll {validated_count} validated resources passed tag validation.")
        return True
    
    def _validate_tag_values(self, tags: dict) -> list:
        """Validate tag values against expected patterns."""
        invalid = []
        
        for k, v in self.value_tags.items():
            if k not in tags:
                continue  # Missing tags handled separately
                
            value = tags[k]
            
            # Determine validation type based on format
            if v.startswith('[') and v.endswith(']'):
                # List validation
                allowed_values = flatten_tag_values(v)
                if value not in allowed_values:
                    invalid.append(f"{k}={value} not in {allowed_values}")
            elif self._is_regex_pattern(v):
                # Regex validation
                try:
                    if not re.match(v, value):
                        invalid.append(f"{k}={value} does not match pattern {v}")
                except re.error:
                    invalid.append(f"{k}={value} - invalid regex pattern {v}")
            else:
                # Exact value validation
                if value != v:
                    invalid.append(f"{k}={value} != {v}")
                    
        return invalid
    
    def _is_regex_pattern(self, pattern: str) -> bool:
        """Determine if a string is a regex pattern."""
        return (pattern.startswith('^') or pattern.endswith('$') or 
                '.*' in pattern or '[0-9]' in pattern or 
                '\\d' in pattern or '\\w' in pattern)