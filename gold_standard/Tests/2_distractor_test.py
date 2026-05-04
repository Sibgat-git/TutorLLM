"""
Distractor Quality Test — asks Claude to rate each wrong option as
'tempting' or 'weak' and explain why. Weak distractors = poor training signal.
"""
import json
import os
import random
import subprocess
from config import CLAUDE_BIN, DISTRACTOR_SAMPLE, SUBJECT_FILES, OUTPUT_DIR


def ask(prompt: str) -> str:
    result = subprocess.run(
        [CLAUDE_BIN, "-p", prompt],
        capture_output=True, text=True
    )
    return result.stdout.strip()


def build_prompt(q: dict) -> str:
    options_text = "\n".join(
        f"{chr(65+i)}) {opt}" for i, opt in enumerate(q["options"])
    )
    return (
        f"You are evaluating MCQ distractor quality.\n\n"
        f"Question: {q['question_text']}\n\n"
        f"Options:\n{options_text}\n\n"
        f"Correct answer: {q['correct_answer']}\n\n"
        f"For each WRONG option, rate it as either 'tempting' (plausible, could fool someone) "
        f"or 'weak' (easily eliminated). Give a one-line reason for each.\n\n"
        f"Respond in this exact JSON format:\n"
        f'[{{"option": "...", "rating": "tempting/weak", "reason": "..."}}]'
    )


def parse_response(text: str) -> list:
    try:
        start = text.index("[")
        end   = text.rindex("]") + 1
        return json.loads(text[start:end])
    except Exception:
        return [{"raw": text}]


results = {}

for path in SUBJECT_FILES:
    subject = os.path.splitext(os.path.basename(path))[0]
    if subject == "info":
        continue

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    sample = random.sample(data, min(DISTRACTOR_SAMPLE, len(data)))
    subject_results = []

    for q in sample:
        prompt   = build_prompt(q)
        raw      = ask(prompt)
        ratings  = parse_response(raw)

        all_weak     = all(r.get("rating") == "weak"     for r in ratings if "rating" in r)
        all_tempting = all(r.get("rating") == "tempting" for r in ratings if "rating" in r)
        weak_count   = sum(1 for r in ratings if r.get("rating") == "weak")

        subject_results.append({
            "question_id":           q.get("question_id"),
            "question_text":         q["question_text"],
            "correct_answer":        q["correct_answer"],
            "distractor_ratings":    ratings,
            "weak_distractor_count": weak_count,
            "all_distractors_weak":  all_weak,
        })
        status = "ALL WEAK" if all_weak else ("ALL TEMPTING" if all_tempting else "MIXED")
        print(f"[{subject}] {status}  weak={weak_count}/{len(ratings)}")

    weak_questions = sum(1 for r in subject_results if r["all_distractors_weak"])
    results[subject] = {
        "sample_size":              len(subject_results),
        "questions_all_weak":       weak_questions,
        "distractor_quality_score": round(1 - weak_questions / len(subject_results), 3),
        "questions":                subject_results,
    }
    print(f"  → {subject}: {weak_questions}/{len(subject_results)} questions have all-weak distractors\n")

out_path = os.path.join(OUTPUT_DIR, "distractor_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"\nSaved → {out_path}")
print("\nSummary (distractor quality score — higher = stronger distractors):")

print(f"{'Subject':<20} {'Score':>6}  All-weak questions")
print("-" * 50)
for subj, r in sorted(results.items()):
    print(f"{subj:<20} {r['distractor_quality_score']:>6.0%}  {r['questions_all_weak']}/{r['sample_size']}")
