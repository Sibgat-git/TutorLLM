"""
Consistency Test — asks the same question multiple times and checks if Claude
gives the same answer each time. High variance = ambiguous question or guessing.
"""
import json
import os
import random
import subprocess
from config import CLAUDE_BIN, CONSISTENCY_SAMPLE, CONSISTENCY_RUNS, SUBJECT_FILES, OUTPUT_DIR


def ask(prompt: str) -> str:
    result = subprocess.run(
        [CLAUDE_BIN, "-p", prompt],
        capture_output=True, text=True
    )
    raw = result.stdout.strip()
    if len(raw) > 2 and raw[1] in (")", ".") and raw[0].isalpha():
        raw = raw[2:].strip()
    return raw


def build_prompt(q: dict) -> str:
    options_text = "\n".join(
        f"{chr(65+i)}) {opt}" for i, opt in enumerate(q["options"])
    )
    return (
        f"Answer the following multiple choice question. "
        f"Reply with ONLY the exact text of the correct option — nothing else.\n\n"
        f"Question: {q['question_text']}\n\n"
        f"Options:\n{options_text}"
    )


def consistency_label(rate: float) -> str:
    if rate == 1.0:
        return "stable"
    elif rate >= 0.6:
        return "mostly_stable"
    else:
        return "inconsistent"


results = {}

for path in SUBJECT_FILES:
    subject = os.path.splitext(os.path.basename(path))[0]
    if subject == "info":
        continue

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    sample = random.sample(data, min(CONSISTENCY_SAMPLE, len(data)))
    subject_results = []

    for q in sample:
        prompt  = build_prompt(q)
        correct = q["correct_answer"].strip()
        answers = [ask(prompt) for _ in range(CONSISTENCY_RUNS)]

        unique           = list(set(answers))
        majority         = max(set(answers), key=answers.count)
        correct_count    = sum(1 for a in answers if a.strip().lower() == correct.lower())
        consistency_rate = answers.count(majority) / CONSISTENCY_RUNS

        subject_results.append({
            "question_id":       q.get("question_id"),
            "question_text":     q["question_text"],
            "correct_answer":    correct,
            "all_answers":       answers,
            "unique_answers":    unique,
            "majority_answer":   majority,
            "correct_run_count": correct_count,
            "consistency_rate":  round(consistency_rate, 2),
            "label":             consistency_label(consistency_rate),
        })
        print(f"[{subject}] rate={consistency_rate:.0%} ({consistency_label(consistency_rate)})  answers={answers}")

    avg_consistency = sum(r["consistency_rate"] for r in subject_results) / len(subject_results)
    inconsistent    = sum(1 for r in subject_results if r["label"] == "inconsistent")

    results[subject] = {
        "sample_size":            len(subject_results),
        "runs_per_question":      CONSISTENCY_RUNS,
        "avg_consistency_rate":   round(avg_consistency, 3),
        "inconsistent_questions": inconsistent,
        "questions":              subject_results,
    }
    print(f"  → {subject}: avg consistency={avg_consistency:.0%}, {inconsistent} inconsistent questions\n")

out_path = os.path.join(OUTPUT_DIR, "consistency_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved → {out_path}")
print("\nSummary:")
print(f"{'Subject':<20} {'Avg Consistency':>16}  Inconsistent questions")
print("-" * 55)
for subj, r in sorted(results.items()):
    print(f"{subj:<20} {r['avg_consistency_rate']:>16.0%}  {r['inconsistent_questions']}/{r['sample_size']}")
