"""
Prompt runner — load, fill, call, compare.

Orchestrates the full prompt testing workflow.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.api_client import call_model
from utils.prompt_loader import fill_prompt, load_prompt


def run_prompt(
    prompt: Dict[str, str],
    variables: Dict[str, str],
    prompt_key: str = "system",
    user_key: Optional[str] = None,
    user_message: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Fill a prompt template and call the LLM.

    Args:
        prompt: Dict from a loaded YAML prompt file.
        variables: Variables to inject into the template.
        prompt_key: Which key in the YAML to use as system prompt (default: 'system').
        user_key: Optional key in the YAML to use as user prompt.
        user_message: Direct user message string (used if user_key is not set).
        **kwargs: Passed to call_model (model, temperature, max_tokens).

    Returns:
        Dict with 'output', 'prompt_key', 'duration_seconds', 'timestamp'.
    """
    system_template = prompt.get(prompt_key, "")
    if not system_template:
        raise ValueError(f"Prompt key '{prompt_key}' not found. Available: {list(prompt.keys())}")

    system_filled = fill_prompt(system_template, variables)

    # Build user message
    if user_key and user_key in prompt:
        user_filled = fill_prompt(prompt[user_key], variables)
    elif user_message:
        user_filled = fill_prompt(user_message, variables)
    else:
        user_filled = variables.get("query", variables.get("task", ""))

    start = time.time()
    output = call_model(system_filled, user_filled, **kwargs)
    duration = time.time() - start

    return {
        "output": output,
        "prompt_key": prompt_key,
        "duration_seconds": round(duration, 2),
        "timestamp": datetime.now().isoformat(),
    }


def run_test_cases(
    prompt: Dict[str, str],
    test_cases: List[Dict[str, Any]],
    prompt_key: str = "system",
    user_key: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    Run a prompt against multiple test cases.

    Args:
        prompt: Dict from a loaded YAML prompt file.
        test_cases: List of dicts, each with a 'variables' key and optional 'name'.
        prompt_key: Which key in the YAML to use as system prompt.
        user_key: Optional key for user prompt.
        **kwargs: Passed to call_model.

    Returns:
        List of result dicts, each with 'test_name', 'variables', 'output', etc.
    """
    results = []
    for i, tc in enumerate(test_cases):
        test_name = tc.get("name", f"test_case_{i+1}")
        variables = tc.get("variables", {})
        user_message = tc.get("user_message", None)

        print(f"  Running: {test_name}...", end=" ", flush=True)

        result = run_prompt(
            prompt, variables, prompt_key, user_key,
            user_message=user_message, **kwargs,
        )
        result["test_name"] = test_name
        result["variables"] = variables
        results.append(result)

        print(f"done ({result['duration_seconds']}s)")

    return results


def compare_versions(
    results_v1: List[Dict[str, Any]],
    results_v2: List[Dict[str, Any]],
    label_v1: str = "v1 (baseline)",
    label_v2: str = "v2 (improved)",
) -> str:
    """
    Format a side-by-side comparison of two prompt versions.

    Args:
        results_v1: Results from run_test_cases for version 1.
        results_v2: Results from run_test_cases for version 2.
        label_v1: Label for version 1.
        label_v2: Label for version 2.

    Returns:
        Formatted markdown string with comparisons.
    """
    lines = [f"# Prompt Comparison: {label_v1} vs {label_v2}\n"]
    lines.append(f"Generated: {datetime.now().isoformat()}\n")

    for r1, r2 in zip(results_v1, results_v2):
        test_name = r1.get("test_name", "unknown")
        lines.append(f"---\n## Test: {test_name}\n")

        # Show input
        variables = r1.get("variables", {})
        if variables:
            lines.append("### Input Variables")
            for k, v in variables.items():
                preview = str(v)[:200] + "..." if len(str(v)) > 200 else str(v)
                lines.append(f"- **{k}**: {preview}")
            lines.append("")

        # V1 output
        lines.append(f"### {label_v1}")
        lines.append(f"*({r1['duration_seconds']}s)*\n")
        lines.append(r1["output"])
        lines.append("")

        # V2 output
        lines.append(f"### {label_v2}")
        lines.append(f"*({r2['duration_seconds']}s)*\n")
        lines.append(r2["output"])
        lines.append("")

    return "\n".join(lines)


def save_results(results: List[Dict[str, Any]], filepath: str) -> None:
    """Save results to a JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {path}")
