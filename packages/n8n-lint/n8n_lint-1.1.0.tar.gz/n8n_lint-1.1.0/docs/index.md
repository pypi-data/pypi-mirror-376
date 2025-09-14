# n8n-lint

**A Python CLI tool for validating n8n workflow JSON files**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/n8n-lint)](https://pypi.org/project/n8n-lint/)
[![Tests](https://img.shields.io/badge/tests-87%20passing-green.svg)](https://github.com/capp3/n8n_lint)

## 🚀 Quick Start

### Installation

```bash
# Using pip
pip install n8n-lint

# Using uv (recommended)
uvx n8n-lint validate workflow.json
```

### Basic Usage

```bash
# Validate a workflow file
n8n_lint validate workflow.json

# Get help
n8n_lint --help
```

### Example

```bash
# Validate an n8n workflow
n8n_lint validate my-workflow.json

# Output with errors
❌ ERROR: Required property 'typeVersion' is missing (Node: n8n-nodes-base.function)
❌ ERROR: Required property 'position' is missing (Node: n8n-nodes-base.function)

╭─────────────────────────── ❌ Validation Summary ────────────────────────────╮
│                                                                              │
│  Validation complete: 2 errors (took 0.00s) - 1 node validated               │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## ✨ Features

- ✅ **Validate n8n workflows** - Check JSON structure and node properties
- ✅ **Complete CLI interface** - validate, import-schema, list-schemas, export-report
- ✅ **Multiple output formats** - Console, JSON, HTML, and Markdown
- ✅ **Custom schemas** - Import your own node schemas
- ✅ **Rich formatting** - Beautiful console output with progress bars
- ✅ **Report generation** - Export validation reports in HTML/Markdown
- ✅ **High performance** - Validates 1000+ nodes in under a second
- ✅ **Production ready** - 87 tests passing, 0 linting issues

## 📚 Documentation

### User Guides

- [Installation Guide](user-guide/installation.md) - Complete installation instructions
- [Basic Usage](user-guide/basic-usage.md) - Getting started with n8n-lint
- [Examples](user-guide/examples.md) - Common usage patterns and examples
- [Troubleshooting](user-guide/troubleshooting.md) - Common issues and solutions

### CLI Reference

- [Command Overview](cli-reference/index.md) - All available commands
- [validate](cli-reference/validate.md) - Validate workflow files
- [import-schema](cli-reference/import-schema.md) - Import custom schemas
- [list-schemas](cli-reference/list-schemas.md) - List available schemas
- [export-report](cli-reference/export-report.md) - Export validation reports

### Developer Documentation

- [API Reference](api-reference/index.md) - Complete API documentation
- [Contributing](developer/contributing.md) - How to contribute to the project
- [Architecture](developer/architecture.md) - System architecture overview
- [Development Setup](developer/development-setup.md) - Local development environment

## 🎯 Use Cases

- **CI/CD Integration** - Validate workflows in automated pipelines
- **Development Workflow** - Catch errors before deployment
- **Quality Assurance** - Ensure workflow compliance
- **Documentation** - Generate validation reports for teams

## 🔧 Advanced Usage

```bash
# JSON output for automation
n8n_lint validate workflow.json --output json

# Import custom node schema
n8n_lint import-schema custom-schema.json --node-type my.custom.node

# Export HTML report
n8n_lint export-report workflow.json --output report.html --format html

# Quiet mode (errors only)
n8n_lint validate workflow.json --quiet
```

## 📦 Package Information

- **Version**: 1.1.0
- **Python**: 3.12+
- **Dependencies**: typer, rich, jsonschema
- **License**: MIT
- **Repository**: [GitHub](https://github.com/capp3/n8n_lint)
- **PyPI**: [n8n-lint](https://pypi.org/project/n8n-lint/)

## 🚀 Get Started

Ready to validate your n8n workflows? [Install n8n-lint](user-guide/installation.md) and start with the [Basic Usage Guide](user-guide/basic-usage.md).

---

_Need help? Check out our [Troubleshooting Guide](user-guide/troubleshooting.md) or [open an issue](https://github.com/capp3/n8n_lint/issues)._
