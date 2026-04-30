import json
import os
import re
from glob import glob

subjects_dir  = "subjects"
flagged_dir   = "flagged"
gold_dir      = "gold_standard"

os.makedirs(flagged_dir, exist_ok=True)
os.makedirs(gold_dir, exist_ok=True)

OCR_PATTERN = re.compile(
    r"�"
    r"|\?{3,}"
    r"|_{20,}"
    r"|[Ѐ-ӿ]"
    r"|[一-鿿]"
    r"|[؀-ۿ]{1}[ঀ-৿]"
)


def get_flags(q: dict) -> list[str]:
    flags = []
    answer  = q.get("correct_answer", "")
    options = q.get("options") or []
    idx     = q.get("correct_option_index")
    text    = q.get("question_text", "").strip()

    if not answer:
        flags.append("empty_answer")

    if len(options) < 2:
        flags.append("too_few_options")

    if len(options) != len(set(options)):
        flags.append("duplicate_options")

    if idx is None or idx < 0 or idx >= len(options):
        flags.append("out_of_range")
    elif answer and options[idx].strip() != answer.strip():
        flags.append("index_mismatch")

    if answer and options:
        if answer.strip() not in [o.strip() for o in options]:
            flags.append("answer_not_in_opts")

    if len(text) < 15:
        flags.append("short_question")

    if OCR_PATTERN.search(text):
        flags.append("ocr_artifacts")

    return flags


files = sorted(glob(os.path.join(subjects_dir, "*.json")))

print(f"{'subject':<20} {'total':>6} {'flagged':>8} {'gold':>6}")
print("-" * 44)

total_all = total_flagged = total_gold = 0

for path in files:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    name = os.path.splitext(os.path.basename(path))[0]
    flagged = []
    gold    = []

    for q in data:
        flags = get_flags(q)
        if flags:
            q["quality_flags"] = flags
            flagged.append(q)
        else:
            gold.append(q)

    with open(os.path.join(flagged_dir, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(flagged, f, ensure_ascii=False, indent=2)

    with open(os.path.join(gold_dir, f"{name}.json"), "w", encoding="utf-8") as f:
        json.dump(gold, f, ensure_ascii=False, indent=2)

    print(f"{name:<20} {len(data):>6} {len(flagged):>8} {len(gold):>6}")
    total_all     += len(data)
    total_flagged += len(flagged)
    total_gold    += len(gold)

print("-" * 44)
print(f"{'TOTAL':<20} {total_all:>6} {total_flagged:>8} {total_gold:>6}")
print(f"\nFlagged   -> {flagged_dir}/")
print(f"Gold      -> {gold_dir}/")
