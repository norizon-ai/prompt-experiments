# Norizon AI — Prompt Experiments

Improve the LLM prompts that power the meeting documentation pipeline:
- **Protocol generation** — transcript → meeting protocol (title, summary, action items, decisions)
- **Speaker inference** — transcript + speaker IDs → real names

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

# 5. Open a notebook
jupyter notebook notebooks/prompt_testing.ipynb          # protocol generation
jupyter notebook notebooks/speaker_inference_testing.ipynb  # speaker inference
# Make sure the kernel is set to "Norizon Experiments"
```

## Two Notebooks, Two Pipelines

| Notebook | Prompt file | What it tests |
|----------|------------|---------------|
| `prompt_testing.ipynb` | `prompts/workflow/prompt_builder.yaml` | Meeting protocol generation |
| `speaker_inference_testing.ipynb` | `prompts/deepgram/speaker_inference.yaml` | Speaker name identification |

Both notebooks follow the same flow:
1. **Section 0** — check what production actually sent/received
2. **Section 1** — load a transcript
3. **Section 2** — run the baseline (current prompt)
4. **Section 3** — edit a prompt block and re-run
5. **Section 4** — compare baseline vs modified
6. **Section 5** — save results

---

## 1. Protocol Generation (`prompt_testing.ipynb`)

When a meeting is processed on the platform, the system sends a **system prompt + transcript** to the LLM and gets back a **meeting protocol** (JSON with title, summary, action items, decisions).

The system prompt is assembled from **blocks** in `prompts/workflow/prompt_builder.yaml`:

| Block | What it does |
|-------|-------------|
| `base_protocol_system` | System preamble (use real names, output JSON) |
| `extraction_from_outline` | Main instructions for generating the protocol |
| `specificity_rules` | Quality rules (min counts, no duplicates, concrete dates) |
| `client_meeting_rules` | Extra rules for client meetings (optional) |
| `json_formatting_open_source` | Tells the model to output only valid JSON |

All blocks exist in `_de` and `_en` variants.

### Which block to edit, based on what's wrong

- Action items too vague or missing? -> `specificity_rules`
- Missing topics or decisions? -> `extraction_from_outline`
- Wrong language or format? -> `base_protocol_system`

---

## 2. Speaker Inference (`speaker_inference_testing.ipynb`)

Takes a transcript with `Speaker 0`/`Speaker 1` labels and a list of speaker IDs, then returns each speaker's real name with an evidence quote and confidence score.

The prompt lives in `prompts/deepgram/speaker_inference.yaml` as a single `system` key.

### Common issues

- Wrong person assigned ("Hi Elon" -> marks the greeter as Elon)? -> Strengthen the BEING vs ADDRESSING rule
- Hallucinated names? -> Strengthen the NO HALLUCINATIONS rule
- Guessed names instead of "Unknown"? -> Make the Unknown fallback more explicit

---

## General Workflow

### 1. Run a meeting on the platform

Process a meeting through mangowater as normal. Verify speakers and generate the protocol.

### 2. Check the production output

Open the relevant notebook and run **Section 0**. This fetches the prompt logs from production so you can see what was sent and what came back.

### 3. Save the transcript locally

Copy the transcript from the platform UI and save it as a `.txt` file in `test_cases/` (e.g. `meeting_02.txt`).

For **protocol generation**, the transcript can be plain text without speaker labels — speaker names are passed separately.
For **speaker inference**, the transcript must have `Speaker 0`/`Speaker 1` labels.

There's a sample file `test_cases/meeting_01.txt` to verify the notebooks work.

### 4. Run the baseline and compare to your quality checklist

In Section 1, set your transcript. Run Section 2 for the baseline. Check the output against your AI Quality Checklist.

### 5. Edit one block and re-run

In Section 3, copy the block you want to change, edit it, and run again. **Change only one block at a time** so you know what helped.

### 6. Compare

Section 4 shows baseline vs modified side by side. If it improved, save the result (Section 5) and update the YAML file directly.

## Tips

- The notebooks default to `gpt-4o`. Switch to `gpt-4o-mini` for faster/cheaper iteration, then confirm on `gpt-4o`.
- Each API call costs money. Don't re-run the baseline if nothing changed.
- If the model returns broken JSON, check the formatting instructions in the prompt.
- Real transcripts may contain sensitive info. They are gitignored (`test_cases/*.txt`), except the sample file.

## Project Structure

```
prompts/
├── deepgram/
│   └── speaker_inference.yaml     # Speaker identification prompt
└── workflow/
    └── prompt_builder.yaml        # Meeting protocol prompt blocks

test_cases/                        # Transcript files (.txt, gitignored)
notebooks/
├── prompt_testing.ipynb           # Protocol generation workbench
└── speaker_inference_testing.ipynb  # Speaker inference workbench
utils/                             # API client, prompt loader
results/                           # Saved experiment outputs (gitignored)
```

## Rules

- Change **one block at a time**
- Test on at least 3 different transcripts before considering a change done
- Save results to `results/` so you can compare later
- When a change is validated, update the YAML file directly
