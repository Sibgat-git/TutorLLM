# TutorLLM Filter Pipeline — Documentation

## Overview

This pipeline takes a raw dataset of Bangladeshi university admission test questions and produces a clean, subject-organized, quality-verified gold standard dataset suitable for LLM training.

---

## Source Data

**File:** `satt_academy_admission_questions.jsonl`
- Format: JSONL (one JSON object per line)
- Total questions: ~37,039
- Fields: `university`, `exam_name`, `exam_year`, `question_id`, `question_text`, `options`, `correct_answer`, `correct_option_index`, `subject`, `tags`, `question_type`, `question_image`

---

## Pipeline Steps

### Step 1 — MCQ Filter (`1_MCQ_filter.py`)
Reads the raw JSONL and filters to only MCQ-type questions.

- **Input:** `satt_academy_admission_questions.jsonl`
- **Output:** `satt_academy_mcq_questions.json`
- **Result:** 17,653 MCQ questions extracted out of 37,039 total

---

### Step 2 — Diagram/Image Filter (`2.No_diagram.py`)
Removes questions that require a diagram or image to answer. Detection uses:
- Non-null `question_image` field
- Bengali referential phrases in question text: `নিচের চিত্র`, `উপরের চিত্র`, `চিত্র অনুযায়ী`, etc.
- English contextual phrases: `in the figure`, `the figure below`, `diagram`, etc.

Note: Broad terms like "figure of speech" are intentionally excluded to avoid false positives.

- **Input:** `satt_academy_mcq_questions.json`
- **Outputs:**
  - `satt_academy_mcq_no_diagram.json` — 17,638 questions (no diagram needed)
  - `satt_academy_mcq_diagram_only.json` — 15 questions (require a diagram)

---

### Step 3 — Deduplication (`3_dedup.py`)
Removes duplicate questions (same `question_text`) that appeared across multiple exam years. Keeps the version from the most recent `exam_year`.

- **Input:** `satt_academy_mcq_no_diagram.json`, `satt_academy_mcq_diagram_only.json`
- **Outputs:**
  - `satt_academy_mcq_no_diagram_dedup.json` — 16,782 questions (864 duplicates removed)
  - `satt_academy_mcq_diagram_only_dedup.json` — 7 questions

---

### Step 4 — Subject Organization (`3.subject_organize.py`)
Classifies each question into a broad subject category using regex pattern matching on the `subject` field. Creates one JSON file per subject inside the `subjects/` folder.

- **Input:** `satt_academy_mcq_no_diagram_dedup.json`
- **Output:** `subjects/` folder with 10 files:

| Subject | Count |
|---|---|
| bangla | 6,244 |
| english | 4,075 |
| physics | 1,410 |
| mathematics | 1,077 |
| biology | 829 |
| general_knowledge | 726 |
| other | 1,665 |
| chemistry | 352 |
| accounting | 316 |
| ict | 88 |
| **Total** | **16,782** |

---

### Step 5 — Quality Report (`4_quality_report.py`)
Runs automated quality checks across all subject files and outputs a report to `mcq_quality.txt`. Re-running the script overwrites the report with fresh results.

**Metrics checked:**

| Metric | Description |
|---|---|
| `empty_answer` | `correct_answer` field is empty |
| `index_mismatch` | `options[correct_option_index]` doesn't match `correct_answer` |
| `answer_not_in_opts` | `correct_answer` text not found anywhere in the options list |
| `out_of_range` | `correct_option_index` points outside the options list |
| `duplicate_options` | Two or more identical choices in the same question |
| `too_few_options` | Fewer than 2 options |
| `short_question` | `question_text` under 15 characters (likely truncated) |
| `ocr_artifacts` | Unicode replacement chars, Cyrillic/CJK in Bengali text |

**Results (`mcq_quality.txt`):**

```
file               | total | empty_answer | index_mismatch | answer_not_in_opts | out_of_range | duplicate_options | too_few_options | short_question | ocr_artifacts
accounting         |   316 |            9 |              0 |                  0 |            9 |                 3 |               0 |              2 |             0
bangla             |  6244 |           18 |              0 |                  0 |           18 |                51 |               0 |             95 |             1
biology            |   829 |            1 |              0 |                  0 |            1 |                 4 |               0 |             12 |             0
chemistry          |   352 |            6 |              0 |                  0 |            1 |                 8 |               3 |              8 |             0
english            |  4075 |           28 |              0 |                  0 |           27 |                39 |              12 |             83 |             2
general_knowledge  |   726 |            3 |              0 |                  0 |            3 |                 4 |               0 |             14 |             0
ict                |    88 |            2 |              0 |                  0 |            2 |                 2 |               0 |              2 |             0
mathematics        |  1077 |           18 |              0 |                  0 |           15 |                48 |              67 |             31 |             0
other              |  1665 |           13 |              0 |                  0 |            8 |                22 |              15 |             31 |             0
physics            |  1410 |            8 |              0 |                  0 |            7 |                20 |              21 |              8 |             0
TOTAL              | 16782 |          106 |              0 |                  0 |           91 |               201 |             118 |            286 |             3
```

**Key findings:**
- Zero index mismatches — every valid index points to the right answer
- Zero answer-not-in-options — every non-empty answer exists somewhere in the options
- 688 questions total flagged across all checks

---

### Step 6 — Gold Standard Separation (`remove_flagged.py`)
Splits each subject file into clean (gold standard) and flagged questions. Flagged questions have a `quality_flags` field added listing the reasons they were removed.

- **Input:** `subjects/*.json`
- **Outputs:**
  - `gold_standard/` — clean questions ready for training
  - `flagged/` — removed questions with reasons attached

| Subject | Total | Flagged | Gold |
|---|---|---|---|
| accounting | 316 | 14 | 302 |
| bangla | 6,244 | 165 | 6,079 |
| biology | 829 | 17 | 812 |
| chemistry | 352 | 20 | 332 |
| english | 4,075 | 164 | 3,911 |
| general_knowledge | 726 | 21 | 705 |
| ict | 88 | 6 | 82 |
| mathematics | 1,077 | 153 | 924 |
| other | 1,665 | 75 | 1,590 |
| physics | 1,410 | 53 | 1,357 |
| **TOTAL** | **16,782** | **688** | **16,094** |

---

## Gold Standard Quality Tests

Three test scripts are in `gold_standard/Tests/`. They use Claude Code's built-in authentication (no API key required) and call the Claude CLI directly.

**Configuration:** `gold_standard/Tests/config.py`
- `ACCURACY_SAMPLE = 20` — questions per subject for accuracy test
- `DISTRACTOR_SAMPLE = 10` — questions per subject for distractor test
- `CONSISTENCY_SAMPLE = 10` — questions per subject for consistency test
- `CONSISTENCY_RUNS = 5` — how many times each question is asked in consistency test

---

### Test 1 — Accuracy & Difficulty (`1_accuracy_test.py`)
Feeds each sampled question to Claude and checks if it picks the correct answer. Scores each subject and labels it easy / medium / hard.

- easy ≥ 80%, medium ≥ 50%, hard < 50%
- **Output:** `accuracy_results.json`

**Results:**

| Subject | Score | Difficulty |
|---|---|---|
| mathematics | 95% | easy |
| biology | 85% | easy |
| chemistry | 80% | easy |
| other | 75% | medium |
| english | 70% | medium |
| general_knowledge | 70% | medium |
| ict | 70% | medium |
| accounting | 65% | medium |
| bangla | 60% | medium |
| physics | 60% | medium |

---

### Test 2 — Distractor Quality (`2_distractor_test.py`)
Asks Claude to rate each wrong option as `tempting` (plausible) or `weak` (easily eliminated). Questions where all distractors are weak are poor training signal.

- Score = proportion of questions with at least one tempting distractor
- **Output:** `distractor_results.json`

**Results:**

| Subject | Score | All-weak questions |
|---|---|---|
| accounting | 100% | 0/10 |
| bangla | 100% | 0/10 |
| biology | 100% | 0/10 |
| chemistry | 100% | 0/10 |
| english | 100% | 0/10 |
| general_knowledge | 100% | 0/10 |
| ict | 90% | 1/10 |
| mathematics | 90% | 1/10 |
| other | 100% | 0/10 |
| physics | 100% | 0/10 |

---

### Test 3 — Consistency (`3_consistency_test.py`)
Asks the same question 5 times and checks if Claude gives the same answer each run. High variance signals ambiguous questions.

- stable = 100% agreement, mostly_stable ≥ 60%, inconsistent < 60%
- **Output:** `consistency_results.json`

**Results:**

| Subject | Avg Consistency | Inconsistent questions |
|---|---|---|
| accounting | 100% | 0/10 |
| english | 100% | 0/10 |
| ict | 100% | 0/10 |
| other | 100% | 0/10 |
| bangla | 92% | 0/10 |
| general_knowledge | 90% | 1/10 |
| biology | 96% | 0/10 |
| chemistry | 96% | 0/10 |
| physics | 96% | 0/10 |
| mathematics | 98% | 0/10 |

---

## Overall Assessment

The gold standard dataset of **16,094 questions** is high quality:

- **Structurally clean** — zero label mismatches, zero missing answers in gold set
- **Strong distractors** — 98% of questions have at least one tempting wrong option
- **Highly consistent** — Claude gives the same answer 96%+ of the time across subjects
- **Well-calibrated difficulty** — math/biology/chemistry are easy for Claude; bangla/physics are medium, suggesting they test genuine domain knowledge

**Recommended next steps:**
1. Hold out 10–15% of each subject file as a test set before any training
2. Subject expert spot-check on physics and chemistry (numerical questions)
3. Fine-tune a smaller model and re-evaluate accuracy scores to measure improvement
