import json
import os
import re
from glob import glob

subjects_dir = "subjects"
files = sorted(glob(os.path.join(subjects_dir, "*.json")))

all_data: dict[str, list] = {}
for path in files:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    all_data[os.path.splitext(os.path.basename(path))[0]] = data

# OCR artifact detector — only genuine corruption signals
OCR_PATTERN = re.compile(
    r"\ufffd"             # Unicode replacement character (broken encoding)
    r"|\?{3,}"            # runs of ??? (unrecognised characters)
    r"|_{20,}"            # very long runs of ___ (missing text, not fill-in-the-blank)
    r"|[\u0400-\u04FF]"   # Cyrillic mid-text (wrong encoding)
    r"|[\u4E00-\u9FFF]"   # CJK characters (wrong encoding)
    r"|[\u0600-\u06FF]{1}[\u0980-\u09FF]"  # Arabic immediately next to Bengali (encoding mixup)
)

HEADERS = [
    "file", "total",
    "empty_answer",       # metric 1
    "index_mismatch",     # metric 2
    "answer_not_in_opts", # metric 6
    "out_of_range",
    "duplicate_options",  # metric 3
    "too_few_options",    # metric 3
    "short_question",     # metric 5
    "ocr_artifacts",      # metric 8
]

rows = []

for name, data in sorted(all_data.items()):
    total              = len(data)
    empty_answer       = 0
    index_mismatch     = 0
    answer_not_in_opts = 0
    out_of_range       = 0
    duplicate_options  = 0
    too_few_options    = 0
    short_question     = 0
    ocr_artifacts      = 0

    for q in data:
        answer  = q.get("correct_answer", "")
        options = q.get("options") or []
        idx     = q.get("correct_option_index")
        text    = q.get("question_text", "").strip()

        if not answer:
            empty_answer += 1

        if len(options) < 2:
            too_few_options += 1
        if len(options) != len(set(options)):
            duplicate_options += 1

        if idx is None or idx < 0 or idx >= len(options):
            out_of_range += 1
        elif answer and options[idx].strip() != answer.strip():
            index_mismatch += 1

        if answer and options:
            if answer.strip() not in [o.strip() for o in options]:
                answer_not_in_opts += 1

        if len(text) < 15:
            short_question += 1

        if OCR_PATTERN.search(text):
            ocr_artifacts += 1

    rows.append([
        name, total,
        empty_answer, index_mismatch, answer_not_in_opts,
        out_of_range, duplicate_options, too_few_options,
        short_question, ocr_artifacts,
    ])

output_file = "mcq_quality.txt"

col_widths = [max(len(str(r[i])) for r in rows + [HEADERS]) for i in range(len(HEADERS))]
sep        = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
header_row = "| " + " | ".join(str(h).ljust(col_widths[i]) for i, h in enumerate(HEADERS)) + " |"
totals     = ["TOTAL", sum(r[1] for r in rows)] + [sum(r[i] for r in rows) for i in range(2, len(HEADERS))]

lines = [
    sep, header_row, sep,
    *["| " + " | ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(row)) + " |" for row in rows],
    sep,
    "| " + " | ".join(str(v).ljust(col_widths[i]) for i, v in enumerate(totals)) + " |",
    sep,
    "",
    "Note: metric 7 (ambiguous questions) requires human/AI evaluation — skipped.",
]

output = "\n".join(lines)
print(output)

with open(output_file, "w", encoding="utf-8") as f:
    f.write(output + "\n")

print(f"\nReport saved to {output_file}")
