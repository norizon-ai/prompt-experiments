"""
YAML prompt loader with variable injection and model-variant support.

Loads prompt files from the prompts/ directory and fills {variable} placeholders.
Supports model-specific overrides (prepend, append, wrap) for tuning prompts
to different LLMs (gpt-4o vs mistral-25b).
"""

import re
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

def load_prompt(prompt_path: str) -> Dict[str, Any]:
    """Load a YAML prompt file and return its contents as a dict."""

    path = Path(prompt_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_template(prompt_data: Dict[str, Any], key: str, model: Optional[str] = None) -> str:
    """Get a prompt template from loaded YAML data, with optional model overrides."""

    if key not in prompt_data:
        raise KeyError(f"Prompt key '{key}' not found. Available: {list(prompt_data.keys())}")

    entry = prompt_data[key]

    if not isinstance(entry, dict):
        return str(entry)

    # Model-variant format (has "base" key)
    if "base" in entry:
        template = str(entry["base"])

        if model and "model_overrides" in entry:
            overrides = entry["model_overrides"].get(model, {})
            if overrides:
                if "prepend" in overrides:
                    template = str(overrides["prepend"]) + "\n" + template
                if "append" in overrides:
                    template = template + "\n" + str(overrides["append"])
                if "wrap" in overrides:
                    template = str(overrides["wrap"]).replace("{base}", template)

        return template

    # Legacy dict with "template" key
    if "template" in entry:
        return str(entry["template"])

    raise KeyError(f"Prompt '{key}' is a dict but has no 'base' or 'template' key")


def fill_prompt(template: str, variables: Dict[str, str]) -> str:
    """Replace {variable} placeholders in a prompt template with actual values."""

    result = template
    for key, value in variables.items():
        # Replace both {key} and {{key}} patterns
        result = result.replace(f"{{{{{key}}}}}", str(value))
        result = result.replace(f"{{{key}}}", str(value))
    return result


def get_prompt_variables(template: str) -> list[str]:
    """Extract all variable names from a prompt template."""

    # Match both {var} and {{var}} patterns, but not JSON-like structures
    singles = re.findall(r"(?<!\{)\{(\w+)\}(?!\})", template)
    doubles = re.findall(r"\{\{(\w+)\}\}", template)
    return list(set(singles + doubles))


def list_prompt_keys(prompt_path: str) -> list[str]:
    """List all prompt keys in a YAML file. => (e.g. ['system', 'synthesize_findings', ...])"""

    data = load_prompt(prompt_path)
    return list(data.keys())


def list_all_prompts(prompts_dir: str = "prompts") -> Dict[str, list[str]]:
    """List all prompt files and their keys."""

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