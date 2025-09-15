import re
from tabulate import tabulate
from .exceptions import TagValidationError, DuplicateTagDeclarationError
from .utils import flatten_tag_values

class TagValidator:
    def __init__(self, required_tags=None, value_tags=None):
        """
        :param required_tags: list of tag keys to check presence
        :param value_tags: dict {tag_key: expected_value/list/regex}
        """
        self.required_tags = required_tags or []
        self.value_tags = value_tags or {}

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
        resources = tf_plan.get("resource_changes", [])
        errors = []

        for res in resources:
            tags = res.get("change", {}).get("after", {}).get("tags", {})
            missing = [t for t in self.required_tags if t not in tags]
            invalid = []

            for k, v in self.value_tags.items():
                if k not in tags:
                    missing.append(k)
                else:
                    value = tags[k]
                    
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
                    "resource": f"{res.get('address')}",
                    "missing_tags": missing,
                    "invalid_tags": invalid
                })

        if errors:
            table = tabulate(
                [(e["resource"], ", ".join(e["missing_tags"]), ", ".join(e["invalid_tags"]))
                 for e in errors],
                headers=["Resource", "Missing Tags", "Invalid Tags"],
                tablefmt="github"
            )
            print(table)
            raise TagValidationError("Tag validation failed for some resources.")

        print("All resources passed tag validation.")
        return True