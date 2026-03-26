# Meeting Protocol — Prompt Experiments

Improve the LLM prompts that generate meeting protocols from transcripts.

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/norizon/norizon-ai-experiments.git
cd norizon-ai-experiments

# 2. Create the conda environment and install dependencies
conda create -n norizon-experiments python=3.11 -y
conda activate norizon-experiments
pip install -r requirements.txt

# 3. Register the Jupyter kernel
python -m ipykernel install --user --name norizon-experiments --display-name "Norizon Experiments"

# 4. Add your API keys
cp .env.example .env
# Fill in OPENAI_API_KEY (required) and MISTRAL_API_KEY (optional)

# 5. Open the notebook
jupyter notebook notebooks/prompt_testing.ipynb
# Make sure the kernel is set to "Norizon Experiments"
```

## How It Works

When a meeting is processed on the platform, the system sends a **system prompt + transcript** to the LLM and gets back a **meeting protocol** (JSON with title, summary, action items, decisions, etc.).

The system prompt is assembled from **blocks** in `prompts/workflow/prompt_builder.yaml`:

| Block | What it does |
|-------|-------------|
| `base_protocol_system` | System preamble (use real names, output JSON) |
| `extraction_from_outline` | Main instructions for generating the protocol |
| `specificity_rules` | Quality rules (min counts, no duplicates, concrete dates) |
| `client_meeting_rules` | Extra rules for client meetings (optional) |
| `json_formatting_open_source` | Tells the model to output only valid JSON |

All blocks exist in `_de` and `_en` variants.

## Workflow

### 1. Run a meeting on the platform

Process a meeting through mangowater as normal. Verify speakers and generate the protocol.

### 2. Check the production output

Open the notebook and run **Section 0**. This fetches the prompt logs from production so you can see:
- What system prompt was sent
- What protocol the model returned
- Which model was used

### 3. Save the transcript locally

Copy the transcript from the platform UI and save it as a `.txt` file in `test_cases/` (e.g. `meeting_02.txt`).

The transcript is plain text without speaker labels — that's fine. Speaker names are passed separately in the prompt.

There's a sample file `test_cases/meeting_01.txt` you can use to verify the notebook works before using real data.

### 4. Run the baseline

In **Section 1**, set your transcript file, speaker names, and language. Run **Section 2** to generate a protocol with the current prompts. This is your baseline.

### 5. Check against your quality checklist

Compare the baseline output to your AI Quality Checklist. Note what's wrong:
- Action items too vague or missing? -> `specificity_rules`
- Missing topics or decisions? -> `extraction_from_outline`
- Wrong language or format? -> `base_protocol_system`

### 6. Edit one block and re-run

In **Section 3**, copy the block you want to change, edit it, and run again. **Change only one block at a time** so you know what helped.

### 7. Compare

**Section 4** shows baseline vs modified side by side. Check the checklist again. If it improved, save the result (**Section 5**) and update `prompt_builder.yaml`.

## Tips

- The notebook uses the same model as production (`gpt-4o`). You can switch to `gpt-4o-mini` for faster/cheaper iteration while drafting, then confirm on `gpt-4o`.
- Each API call costs money. Don't re-run the baseline if nothing changed — only re-run when you've edited a prompt block.
- If the model returns broken JSON, check `json_formatting_open_source` — it may need stronger instructions.
- Real transcripts may contain sensitive info. They are gitignored by default (`test_cases/*.txt`), except the sample file.

## Project Structure

```
prompts/
├── deepgram/                  # Speaker identification
│   ├── patterns.yaml          # Regex patterns for name detection (EN/DE)
│   └── evidence_evaluation.yaml
└── workflow/
    └── prompt_builder.yaml    # All meeting protocol prompt blocks

test_cases/                    # Transcript files (.txt)
notebooks/
└── prompt_testing.ipynb       # Main workbench
utils/                         # API client, prompt loader
results/                       # Saved outputs (gitignored)
```

## Rules

- Change **one block at a time**
- Test on at least 3 different transcripts before considering a change done
- Save results to `results/` so you can compare later
- When a change is validated, update `prompt_builder.yaml` directly
