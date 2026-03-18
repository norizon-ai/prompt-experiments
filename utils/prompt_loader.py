"""
YAML prompt loader with variable injection.

Loads prompt files from the prompts/ directory and fills {{variable}} placeholders.
"""

import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_prompt(prompt_path: str) -> Dict[str, Any]:
    """
    Load a YAML prompt file and return its contents as a dict.

    Args:
        prompt_path: Path to the YAML prompt file (relative or absolute).

    Returns:
        Dict with prompt keys (e.g. 'system', 'synthesize_findings', etc.)
    """
    path = Path(prompt_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fill_prompt(template: str, variables: Dict[str, str]) -> str:
    """
    Replace {variable} placeholders in a prompt template with actual values.

    Supports both {variable} and {{variable}} syntax.

    Args:
        template: The prompt template string with placeholders.
        variables: Dict mapping variable names to their values.

    Returns:
        The filled prompt string.
    """
    result = template
    for key, value in variables.items():
        # Replace both {key} and {{key}} patterns
        result = result.replace(f"{{{{{key}}}}}", str(value))
        result = result.replace(f"{{{key}}}", str(value))
    return result


def get_prompt_variables(template: str) -> list[str]:
    """
    Extract all variable names from a prompt template.

    Args:
        template: The prompt template string.

    Returns:
        List of unique variable names found in the template.
    """
    # Match both {var} and {{var}} patterns, but not JSON-like structures
    singles = re.findall(r"(?<!\{)\{(\w+)\}(?!\})", template)
    doubles = re.findall(r"\{\{(\w+)\}\}", template)
    return list(set(singles + doubles))


def list_prompt_keys(prompt_path: str) -> list[str]:
    """
    List all prompt keys in a YAML file.

    Args:
        prompt_path: Path to the YAML prompt file.

    Returns:
        List of top-level keys (e.g. ['system', 'synthesize_findings', ...])
    """
    data = load_prompt(prompt_path)
    return list(data.keys())


def list_all_prompts(prompts_dir: str = "prompts") -> Dict[str, list[str]]:
    """
    List all prompt files and their keys.

    Args:
        prompts_dir: Path to the prompts directory.

    Returns:
        Dict mapping filename to list of prompt keys.
    """
    prompts_path = Path(prompts_dir)
    result = {}
    for yaml_file in sorted(prompts_path.rglob("*.yaml")):
        rel_path = str(yaml_file.relative_to(prompts_path))
        try:
            data = load_prompt(str(yaml_file))
            result[rel_path] = list(data.keys())
        except Exception as e:
            result[rel_path] = [f"ERROR: {e}"]
    return result
