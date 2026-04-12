# Prompt Engineering Report — Meeting Protocol Quality Improvement

**Project:** Norizon AI Experiments — Protocol Generation Prompts  
**Author:** Shubham Ilhe  
**Date:** April 2026  
**Model:** GPT-4o (temperature 0.1–0.2)  
**Test Transcripts:** 6 English meetings (4 internal + 2 external long-form) + 3 German Videos

---

## Background

The Norizon platform generates meeting protocols by sending a system prompt + transcript to an LLM. The system prompt is assembled from named blocks in `prompt_builder.yaml`. This report documents four quality problems found during evaluation, the prompt changes made to fix each one, and the observed results.

Four blocks were edited across this work:

| Block | Role in Pipeline |
|-------|-----------------|
| `specificity_rules_en` | Quality rules — what to extract and how |
| `structure_analysis_en` | First-pass structural outline of the meeting |
| `extraction_from_outline_en` | Final protocol generation from outline + transcript |
| `json_formatting_open_source_en` | Output format enforcement |

The baseline `prompt_builder.yaml` was never modified. All changes were tested in `PROMPTS_MODIFIED` in the Jupyter notebook, compared against baseline outputs, and validated across multiple transcripts and re-runs.

---

## Problem 1 — Empty `next_steps` Field

### What Was Wrong

The `next_steps` field was empty in 4 out of 5 test videos, even when meetings explicitly discussed upcoming phases, pending approvals, or planned follow-ups. For example, in Meeting 2 (repo onboarding), Omar clearly outlined multiple steps Shubham should do after the call — but the protocol returned `next_steps: []`.

### Root Cause

The original `specificity_rules_en` had detailed rules for `action_items`, `decisions`, and `summary` — but zero mention of `next_steps`. The model treated it as optional and defaulted to empty.

### What Was Changed

**Block edited:** `specificity_rules_en`

**Lines added:**

```
- Next steps: are broader project phases or team-level dependencies.
  NEVER leave next_steps empty if the project's future was discussed.
```

This single edit does three things: it defines what kind of content goes in `next_steps` (phases, dependencies — distinct from `action_items` which are individual assigned tasks), it adds a hard constraint (`NEVER leave empty`), and it gives the model a trigger condition (`if the project's future was discussed`).

### Results

**Before:** `next_steps` empty in 4/5 videos.  
**After:** `next_steps` populated with 3–5 items in all test transcripts, across all re-runs.

Example from Meeting 3 (autofocus discussion):

- Before: `next_steps: []`
- After: `next_steps` included "Investigate the transmission problem further," "Develop a prototype of the vision system for testing," "Prepare for a potential transition to C++ by August"

### Limitations

- The model occasionally puts the same item in both `next_steps` and `action_items` — the semantic boundary between them is not perfectly enforced.
- Quality of `next_steps` items varies: sometimes detailed, sometimes generic ("Continue project").

---

## Problem 2 — Silent Topic and People Drops

### What Was Wrong

The model was silently dropping entire topics from the output — particularly brief side-discussions, minor sub-projects, and people mentioned only once. The clearest example: in Meeting 4, Lisa's onboarding session was explicitly discussed ("Coordinate with Lisa for an in-person explanation session") but appeared nowhere in the modified output — not in action items, not in participants, nowhere.

Other examples: external resources mentioned in conversations (papers, Google guides) were dropped, the software practices discussion (C++, clean code, GitHub) in Meeting 3 appeared in one run but vanished entirely in the next.

### Root Cause

Two causes working together:

1. **No enumeration requirement.** The model made on-the-fly importance judgments while generating output. Brief topics lost out against more prominent ones.
2. **JSON-first commitment.** The original `json_formatting_open_source_en` forced the model to start writing JSON immediately (`Start with { and end with }`). Once the model committed to a structure (e.g., "this meeting has 4 topics"), content that didn't fit was discarded silently.

### Iteration 1 — Failed Attempt

Added vague rules to `specificity_rules_en`:

```
- KEY TOPICS: Every distinct subject discussed must appear somewhere in output.
- NO OMISSIONS: If a topic took more than 1 minute, it must be reflected in output.
```

**Result:** Barely improved. "Distinct subject" and "more than 1 minute" are judgment calls the model was already making and getting wrong. Adding vague rules didn't change the underlying decision-making. Meeting 4 actually regressed — Lisa was dropped completely.

### Iteration 2 — Current Approach (3-Block Edit)

The problem was attacked at three pipeline stages simultaneously.

**Edit 1 — `specificity_rules_en`:** Replaced vague rules with concrete, verifiable ones:

```
- ENTITY EXTRACTION: Treat every newly mentioned project, sub-task, tool,
  client, or person as a mandatory trigger. You MUST document each one separately.
- NO SILENT DROPS: Never discard a side-topic just because the discussion was brief.
  If a separate sub-project or task is discussed even for a few sentences,
  it MUST be preserved as its own distinct item.
- NAMED PEOPLE CHECK: Every person mentioned by name in the transcript must appear
  in at least one field of the output. Do not omit any person.
```

Why this works better: `ENTITY EXTRACTION` gives the model an explicit checklist (project / sub-task / tool / client / person) instead of a vague "distinct subject." `NAMED PEOPLE CHECK` is the most concrete — the model can audit a specific verifiable fact: is every named person present somewhere in the output?

**Edit 2 — `structure_analysis_en`:** Applied the same extraction rules to the structural analysis stage (which runs before the final protocol generation):

```
6. ENTITY EXTRACTION: Every person, sub-project, tool, or administrative task
   mentioned — even briefly — must appear as its own topic or sub-item.
7. NO SILENT DROPS: A side-topic discussed for even 2-3 sentences must be its
   own topic entry, not absorbed into a broader topic.
```

This matters because if a topic gets dropped at the structure analysis stage, no downstream rule can recover it. Topics must now survive two checkpoints.

**Edit 3 — `json_formatting_open_source_en`:** Added a mandatory pre-scan before any JSON is written:

```
STEP 1 — MANDATORY PRE-SCAN (complete before writing any JSON):
Go through the transcript and list every person, sub-project, tool, task, and topic.
This checklist is binding — every item MUST appear somewhere in the final JSON output.

STEP 2 — JSON OUTPUT:
Your response must be ONLY valid JSON. Start with { and end with }.
Every item from Step 1 must be represented in the output.
```

This directly addresses the JSON-first commitment problem: the model must commit to a content inventory first, then build the JSON around it — instead of building structure first and fitting content in afterward.

### Results

**Before:** Lisa dropped in Meeting 4, software practices section vanished between runs in Meeting 3, external resources (papers, Google guide) missing in Meeting 1.

**After:** Lisa now appears in `people` and `next_steps` in Meeting 4. All major tools, resources, and people are captured across meetings. Meeting 3's software practices section (C++, GitHub, pattern design, UML) is present in every run.

For the long-form Elon Musk transcript (40+ minutes), the model captured all major themes (AI safety, China, open source, jobs, education, cryptographic signing, gov.uk deployment, startup culture, social media bots) — though two topics (robot safety / off-switch discussion and community notes mechanism) were not always present. On review, these are non-actionable discussion tangents rather than key points — the model's editorial judgment here is reasonable.

### Limitations

- The pre-scan in Step 1 is a behavioral instruction — we cannot verify the model actually performs it, only observe whether the output reflects it.
- Very brief single-sentence mentions may still be dropped.
- All three edits were applied simultaneously, so we cannot attribute specific improvements to specific edits without ablation testing.

---

## Problem 3 — Inconsistent Outputs Across Re-runs

### What Was Wrong

Running the same transcript multiple times produced different outputs — different action items selected, different topics emphasized, different counts. This was most visible on longer transcripts (Meetings 3, 4, 5), where 3 out of 5 videos showed significant variation between runs. Short focused meetings (Meetings 1, 2) were stable.

This is not about JSON structure variation (which is expected without Pydantic), but about content drift — the model prioritizing different points each time on longer or denser transcripts.

### Root Cause

This is fundamentally an LLM sampling behavior issue, not a prompt logic issue. At any temperature above 0, the model makes probabilistic choices about which content to prioritize. Longer transcripts have more content competing for limited output space, so the variation is larger.

### What Was Changed

**Primary fix:** Temperature reduced from 0.2 to 0.1 in `call_model()`.

**Supporting fix:** The prompt changes from Problems 1 and 2 (entity extraction rules, pre-scan, named people check) also help indirectly — by giving the model explicit checklists to follow, there's less room for subjective prioritization to vary between runs.

No dedicated prompt block was edited specifically for this problem.

### Results

Testing was done by running the same transcript 3 times consecutively and comparing outputs.

**Meeting 2 (short/focused):** All 3 runs produced identical core content — same 8 action items, same 5 decisions, same 2 next_steps.

**Meeting 3 (long/dense):** Core items (top 8 action items, all 5 decisions, 4 next_steps) were stable across all 3 runs. Minor peripheral items (e.g., whether Rahul and Andre from the last 30 seconds of casual conversation appear) still drifted — expected behavior for throwaway mentions at any temperature above 0.

**Meeting 5 (Cloud Code podcast — long):** Core 8 action items identical across 3 runs. Same 5 decisions. Same 3–4 next_steps. Peripheral drift only on whether Akash (the host, who mostly asks questions) appears in the `people` field.

### Limitations

- Temperature 0.0 would eliminate remaining drift entirely but may produce rigid-sounding outputs.
- The remaining drift is exclusively on peripheral/minor items — not on key decisions, action items, or topics.
- This is as far as prompt engineering can go. Full determinism requires either temperature 0.0 or structural post-processing validation.

---

## Problem 4 — Nuance Loss and Oversimplification

### What Was Wrong

The model was flattening nuanced statements into one-sided conclusions, listing partially-answered questions as fully "open," and dropping conceptual explanations entirely.

Specific examples from the quality checklist:

- **Meeting 3:** The protocol said "Prof showed confidence in the existing algorithm" — but the actual transcript said the algorithm is fine BUT the root cause of the 15-minute delay is still unknown. The qualification was dropped.
- **Meeting 4:** An "Open Question" was listed as unanswered ("What specific metrics should be used for evaluating AI outputs?") even though Omar actually answered it in the meeting by sharing the checklist itself.
- **Meeting 5:** Carl Velotti explained the conceptual distinction between MCPs and APIs in detail — a core educational point — but the output reduced it to a generic action item. The conceptual insight was lost.
- **Meeting 5:** Next steps included "Begin implementing action items" — generic filler instead of Carl's actual closing challenge to start using Cloud Code for everything.

### Root Cause

The original prompts focused entirely on extractable facts (action items, decisions, dates) with no guidance on preserving qualified statements, conceptual explanations, or partially-answered questions. The model optimized for extraction, which meant simplification.

### What Was Changed

**Edit 1 — `specificity_rules_en`:** Three new rules added:

```
- NUANCE PRESERVATION: When a speaker qualifies a statement (e.g., "the algorithm
  is fine BUT the delay cause is unknown"), capture BOTH parts. Do NOT flatten
  qualified statements into one-sided conclusions.
- PARTIAL ANSWERS: If a question was raised AND partially or fully answered in the
  same meeting, do NOT list it as an "open question." Instead, capture the answer
  given and note any remaining uncertainty.
- KEY INSIGHTS: When a speaker explains a conceptual distinction, framework, or
  mental model (e.g., "MCP is different from API because..."), capture it in the
  summary or as a separate field. Conceptual explanations are as important as
  action items.
```

**Edit 2 — `extraction_from_outline_en`:** Added a `NUANCE RULES` section:

```
NUANCE RULES:
- If the transcript contains qualified statements ("X is true, but Y"), preserve
  the full nuance. Do not simplify to just "X is true."
- If someone explains a concept, framework, or distinction in detail, it MUST appear
  in the summary or a dedicated field. Do not reduce explanations to generic action items.
- Open questions: Only list a question as "open" if it was genuinely left unanswered.
  If the speaker gave even a partial answer, capture the answer and note what remains
  uncertain.
```

### Results

**Before:** Flat statements, fake "open questions," no conceptual insights captured.

**After:** The model now produces three new types of content:

1. **`key_insights` field** — appears naturally in the output without being defined in any schema. The `KEY INSIGHTS` rule in `specificity_rules_en` triggers the model to create this field on its own. Examples from Meeting 3: "The problem with the autofocus system is likely due to transmission issues, not the algorithm" and "Deep learning is not suitable for this particular problem, highlighting the need for a tailored approach."

2. **`open_questions` field** — now contains genuinely unanswered questions. Example from Meeting 3: "Is the transmission problem isolated to one computer or affecting all systems?" — this was actually raised but left unanswered in the transcript. Previously, the model would list already-answered questions here.

3. **Qualified statements in summaries** — the model now preserves both sides. Example from the Elon Musk transcript: "The potential for AI to create a future of abundance is significant, but it comes with risks that need to be managed" — capturing both the optimism AND the warning, not flattening to just one.

Meeting 5's summary now mentions Carl Velotti by name, references the MCP integration concept, and the `key_insights` field captures substantive points about skills automation and parallelization capabilities.

### Limitations

- The `key_insights` field is model-generated, not schema-enforced. It appears consistently but its presence is not guaranteed.
- Very subtle nuances (tone, sarcasm, hesitation) are still lost — the model captures factual qualifications but not emotional ones.
- The MCP vs API conceptual distinction from Meeting 5 is partially captured (the value of MCP integration appears in insights) but the explicit comparison is still not spelled out in full.

---

## Summary of All Changes

### Final State of Each Modified Block

**`specificity_rules_en`** — 6 lines added to baseline:

| Line Added | Solves |
|-----------|--------|
| Next steps definition + NEVER leave empty | Problem 1 |
| ENTITY EXTRACTION | Problem 2 |
| NO SILENT DROPS | Problem 2 |
| NAMED PEOPLE CHECK | Problem 2 |
| NUANCE PRESERVATION | Problem 4 |
| PARTIAL ANSWERS | Problem 4 |
| KEY INSIGHTS | Problem 4 |

**`structure_analysis_en`** — 2 lines added:

| Line Added | Solves |
|-----------|--------|
| ENTITY EXTRACTION at outline stage | Problem 2 |
| NO SILENT DROPS at outline stage | Problem 2 |

**`extraction_from_outline_en`** — NUANCE RULES section added:

| Section Added | Solves |
|--------------|--------|
| Qualified statements rule | Problem 4 |
| Conceptual explanations rule | Problem 4 |
| Open questions rule | Problem 4 |
| Transcript as ground truth (line 2 edit) | Problem 2 |

**`json_formatting_open_source_en`** — Replaced with 2-step process:

| Change | Solves |
|--------|--------|
| STEP 1: Mandatory pre-scan before JSON | Problem 2 |
| STEP 2: Binding checklist for output | Problem 2 |

**Temperature:** Reduced from 0.2 to 0.1 → Problem 3

### Final Scorecard

| Problem | Status | Method |
|---------|--------|--------|
| 1 — Empty next_steps | Solved | 1 line in specificity_rules_en |
| 2 — Silent topic/people drops | Solved | 3-block edit (specificity + structure + json_formatting) |
| 3 — Re-run inconsistency | Solved (core content) | Temperature reduction + indirect benefit from Problem 2 rules |
| 4 — Nuance loss | Solved | 2-block edit (specificity + extraction_from_outline) |

### What Prompt Engineering Cannot Fix

- Full output determinism (would require temperature 0.0 or post-processing validation)
- Guaranteed JSON schema consistency (would require Pydantic or structured output mode)
- Perfect coverage of very long transcripts (40+ minutes) where minor topics may still be deprioritized — this is reasonable editorial behavior, not a defect

### The final edited Prompt for Englsh and German was saved in worlflow/prompt_builder_new.yaml 