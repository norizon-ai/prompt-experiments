# Norizon AI — Prompt Experiments

Isolated environment for testing and improving LLM prompts used across the Norizon platform.

## Structure

```
prompts/                  # Baseline prompts (YAML) — DO NOT edit directly
├── deepsearch/           # Search system prompts (supervisor, agents, retriever)
├── deepgram/             # Speaker identification prompts
└── workflow/             # Meeting protocol generation prompts

test_cases/               # Test case JSON files (exported from Excel)
notebooks/
└── prompt_testing.ipynb  # Main workbench — load, run, compare prompts
utils/                    # Utility code (loader, API client, runner)
results/                  # Experiment outputs (gitignored)
```

## Workflow

1. **Pick a prompt** from `prompts/` — each YAML file contains one or more prompt templates
2. **Read the baseline** — understand what it does and what variables it expects
3. **Test manually** — use the notebook to run the baseline with sample inputs
4. **Document test cases** — record inputs + expected outputs in your Excel sheet
5. **Create a v2** — copy the YAML, make improvements, save as `*_v2.yaml`
6. **Compare** — run both versions on the same inputs and compare

## Rules

- **DO NOT** modify files in `prompts/` directly — these are baselines
- Create copies with version suffixes for experiments: `supervisor_v2.yaml`, `supervisor_v3.yaml`
- Keep the same variable placeholders (`{query}`, `{search_findings}`, etc.)
- Test cases go in `test_cases/` as JSON (exported from your Excel tracker)
- Results go in `results/` (gitignored, won't be committed)

## Prompt Inventory

| # | File | Service | What it does |
|---|------|---------|-------------|
| 1 | `deepsearch/supervisor.yaml` | DeepSearch | Query classification, report generation (6 templates), conflict detection |
| 2 | `deepsearch/confluence_agent.yaml` | DeepSearch | Confluence CQL search strategy + synthesis |
| 3 | `deepsearch/jira_agent.yaml` | DeepSearch | Jira JQL search strategy + synthesis |
| 4 | `deepsearch/elasticsearch_agent.yaml` | DeepSearch | Elasticsearch search + German technical docs |
| 5 | `deepsearch/websearch_agent.yaml` | DeepSearch | Web search via SearXNG |
| 6 | `deepsearch/retriever.yaml` | DeepSearch | Answer generation + confidence scoring |
| 7 | `deepsearch/query_reformulator.yaml` | DeepSearch | Query optimization + German compound words |
| 8 | `deepgram/evidence_evaluation.yaml` | Deepgram | Speaker identification from transcript evidence |
| 9 | `deepgram/patterns.yaml` | Deepgram | Regex patterns for speaker name deduplication |
| 10 | `workflow/prompt_builder.yaml` | Workflow | Meeting protocol generation (extracted from Python) |
