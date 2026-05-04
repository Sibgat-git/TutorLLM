"""
Accuracy Test — feeds each sampled question to Claude and checks if it picks
the correct answer. Scores per subject and labels difficulty.
"""
import json
import os
import random
import subprocess
from config import CLAUDE_BIN, ACCURACY_SAMPLE, SUBJECT_FILES, OUTPUT_DIR


def ask(prompt: str) -> str:
    result = subprocess.run(
        [CLAUDE_BIN, "-p", prompt],
        capture_output=True, text=True
    )
    raw = result.stdout.strip()
    # Strip leading "A) ", "B) " etc if model includes the letter prefix
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


def difficulty_label(score: float) -> str:
    if score >= 0.8:
        return "easy"
    elif score >= 0.5:
        return "medium"
    else:
        return "hard"


results = {}

for path in SUBJECT_FILES:
    subject = os.path.splitext(os.path.basename(path))[0]
    if subject == "info":
        continue

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    sample = random.sample(data, min(ACCURACY_SAMPLE, len(data)))
    subject_results = []

    for q in sample:
        prompt    = build_prompt(q)
        model_ans = ask(prompt)
        correct   = q["correct_answer"].strip()
        passed    = model_ans.strip().lower() == correct.lower()

        subject_results.append({
            "question_id":    q.get("question_id"),
            "question_text":  q["question_text"],
            "correct_answer": correct,
            "model_answer":   model_ans,
            "passed":         passed,
        })
        print(f"[{subject}] {'✓' if passed else '✗'}  model={model_ans!r}  correct={correct!r}")

    score = sum(r["passed"] for r in subject_results) / len(subject_results)
    results[subject] = {
        "sample_size": len(subject_results),
        "score":       round(score, 3),
        "difficulty":  difficulty_label(score),
        "questions":   subject_results,
    }
    print(f"  → {subject}: {score:.0%} ({difficulty_label(score)})\n")

out_path = os.path.join(OUTPUT_DIR, "accuracy_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved → {out_path}")
print("\nSummary:")
print(f"{'Subject':<20} {'Score':>6}  Difficulty")
print("-" * 40)
for subj, r in sorted(results.items()):
    print(f"{subj:<20} {r['score']:>6.0%}  {r['difficulty']}")
