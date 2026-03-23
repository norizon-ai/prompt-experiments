"""
Prompt runner => load, fill, call, compare across models.

Orchestrates the full prompt testing workflow with model-variant support.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.api_client import call_model
from utils.prompt_loader import fill_prompt, get_template


def run_prompt(
    prompt: Dict[str, str],
    variables: Dict[str, str],
    prompt_key: str = "system",
    user_key: Optional[str] = None,
    user_message: Optional[str] = None,
    target_model: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Fill a prompt template and call the LLM."""

    system_template = get_template(prompt, prompt_key, model=target_model)
    system_filled = fill_prompt(system_template, variables)

    # Build user message
    if user_key:
        user_template = get_template(prompt, user_key, model=target_model)
        user_filled = fill_prompt(user_template, variables)
    elif user_message:
        user_filled = fill_prompt(user_message, variables)
    else:
        user_filled = variables.get("query", variables.get("task", ""))

    # Use target_model as the API model if not explicitly set in kwargs
    if target_model and "model" not in kwargs:
        kwargs["model"] = target_model

    start = time.time()
    output = call_model(system_filled, user_filled, **kwargs)
    duration = time.time() - start

    return {
        "output": output,
        "prompt_key": prompt_key,
        "target_model": target_model or kwargs.get("model", "default"),
        "duration_seconds": round(duration, 2),
        "timestamp": datetime.now().isoformat(),
    }


def run_test_cases(
    prompt: Dict[str, str],
    test_cases: List[Dict[str, Any]],
    prompt_key: str = "system",
    user_key: Optional[str] = None,
    target_model: Optional[str] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    """Run a prompt against multiple test cases."""

    results = []
    for i, tc in enumerate(test_cases):
        test_name = tc.get("name", f"test_case_{i+1}")
        variables = tc.get("variables", {})
        user_message = tc.get("user_message", None)

        print(f"  Running: {test_name}...", end=" ", flush=True)

        result = run_prompt(
            prompt, variables, prompt_key, user_key,
            user_message=user_message, target_model=target_model, **kwargs,
        )
        result["test_name"] = test_name
        result["variables"] = variables
        results.append(result)

        print(f"done ({result['duration_seconds']}s)")

    return results


def compare_models(
    prompt: Dict[str, str],
    variables: Dict[str, str],
    prompt_key: str = "system",
    models: List[str] = None,
    user_key: Optional[str] = None,
    user_message: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Run the same prompt against multiple models and compare outputs."""

    if not models:
        models = ["gpt-4o"]

    results = {}
    for model in models:
        print(f"  Running with {model}...", end=" ", flush=True)
        result = run_prompt(
            prompt, variables, prompt_key, user_key,
            user_message=user_message, target_model=model, **kwargs,
        )
        results[model] = result
        print(f"done ({result['duration_seconds']}s)")

    # Build comparison text
    lines = [f"# Model Comparison: {' vs '.join(models)}\n"]
    lines.append(f"Generated: {datetime.now().isoformat()}\n")
    lines.append(f"Prompt: {prompt_key}\n")

    for model, result in results.items():
        lines.append(f"---\n## {model} ({result['duration_seconds']}s)\n")
        lines.append(result["output"])
        lines.append("")

    return {
        "models": results,
        "comparison": "\n".join(lines),
    }


def compare_versions(
    results_v1: List[Dict[str, Any]],
    results_v2: List[Dict[str, Any]],
    label_v1: str = "v1 (baseline)",
    label_v2: str = "v2 (improved)",
) -> str:
    """Format a side-by-side comparison of two prompt versions."""

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