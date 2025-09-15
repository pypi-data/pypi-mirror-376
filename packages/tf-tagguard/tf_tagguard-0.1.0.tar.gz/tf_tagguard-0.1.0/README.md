# tf-tagguard

[![PyPI version](https://img.shields.io/pypi/v/tf-tagguard)](https://pypi.org/project/tf-tagguard/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

`tf-tagguard` is a CLI tool to validate and enforce AWS tags on resources deployed via Terraform. It is designed for **CI/CD pipelines** and **local CLI environments**, ensuring all resources meet your organization's tagging policies.

---

## Features

- Validate presence of required tags.
- Validate tag values (exact match, list of values, or regex patterns).
- Tabular summary of missing or invalid tags using `tabulate`.
- Fail-fast behavior for duplicate tag declarations.
- Easy integration into CI/CD pipelines.
- Modular design for future extensions.

---

## Installation

```
pip install tf-tagguard
```
## CLI Usage

```
validatetags-tf PLAN_FILE [OPTIONS]
```

| Option | Description | Example |
|--------|-------------|---------|
| `-r, --required-tags` | Comma-separated list of required tags (presence only). | `--required-tags Name,Environment` |
| `-v, --value-tags` | List of tags with expected values. Supports: <br> - **Exact value** → `key=value` <br> - **List of allowed values** → `key=[v1,v2,v3]` <br> - **Regex pattern** → `key=^regex$` | `Environment=dev` <br> `Team=[dev,ops,qa]` <br> `Owner=^user.*$` |

## Examples
1. Validate only tag presence

```
validatetags-tf plan.json -r Name,Environment,Owner
```
2. Validate tag values
```
validatetags-tf plan.json -v "Environment=dev","Team=[ops,dev]","Owner=^user.*$"
```
3. Validate presence + values (fallback: -v takes precedence if duplicated)
```
validatetags-tf plan.json -r Name,Owner -v "Environment=dev","Team=[ops,dev]"
```

**NOTE:**

⚠️ Tags declared in both `-r` and `-v` will trigger a warning, as a fallback mechanisim `-v` values take precedence.

### Terraform Plan JSON

tf-tagguard expects a Terraform plan in JSON format. Generate it with:

```bash
terraform plan -out=tfplan.binary
terraform show -json tfplan.binary > plan.json
```

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | ✅ All validations passed |
| `1` | ❌ Validation failed or error occurred |

## Advanced Usage

### Multiple Value Tags
Use separate `-v` flags for multiple validations:

```bash
validatetags-tf plan.json \
  -v "Environment=[dev,staging,prod]" \
  -v "Team=[ops,dev,qa]" \
  -v "Owner=^user.*$"
```

### CI/CD Integration

**GitHub Actions:**
```yaml
- name: Validate Terraform Tags
  run: |
    terraform plan -out=tfplan.binary
    terraform show -json tfplan.binary > plan.json
    validatetags-tf plan.json -r Name,Environment,Owner
```

**GitLab CI:**
```yaml
validate_tags:
  script:
    - terraform plan -out=tfplan.binary
    - terraform show -json tfplan.binary > plan.json
    - validatetags-tf plan.json -r Name,Environment,Owner
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and changes.