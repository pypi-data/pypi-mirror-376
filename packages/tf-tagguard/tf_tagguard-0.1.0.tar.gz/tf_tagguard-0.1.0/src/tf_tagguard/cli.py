import typer
import json
from .validator import TagValidator
from .utils import load_tf_plan
from .exceptions import TagValidationError, DuplicateTagDeclarationError

app = typer.Typer(help="Validate Terraform tags on AWS resources.")

def parse_value_tags(values: list[str]) -> dict:
    """
    Convert list like ["Env=dev", "Team=[ops,dev]"] to dict
    """
    result = {}
    for item in values:
        if "=" not in item:
            raise typer.BadParameter(f"Invalid -v value '{item}', must be key=value")
        k, v = item.split("=", 1)
        result[k.strip()] = v.strip()
    return result

@app.command()
def main(
    plan_file: str = typer.Argument(..., help="Terraform plan JSON file"),
    required_tags_str: str = typer.Option("", "--required-tags", "-r", help="Comma-separated required tags"),
    value_tags_list: list[str] = typer.Option(None, "--value-tags", "-v", help="List of key=value, key=[list], key=regex")
):
    """Validate Terraform tags on AWS resources."""
    required_tags = [t.strip() for t in required_tags_str.split(",") if t.strip()] if required_tags_str else []
    value_tags = parse_value_tags(value_tags_list) if value_tags_list else {}

    try:
        tf_plan = load_tf_plan(plan_file)
        validator = TagValidator(required_tags, value_tags)
        validator.validate(tf_plan)
    except (FileNotFoundError, ValueError, PermissionError) as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except TagValidationError as e:
        typer.secho(str(e), fg=typer.colors.RED)
        raise typer.Exit(code=1)
