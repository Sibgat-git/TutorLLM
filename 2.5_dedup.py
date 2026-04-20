import json


def dedup_by_recent_year(questions):
    """Keep one entry per unique question_text, favouring the most recent exam_year."""
    seen = {}  # normalized_text -> question dict
    for q in questions:
        key = q.get("question_text", "").strip()
        if not key:
            continue
        existing = seen.get(key)
        if existing is None:
            seen[key] = q
        else:
            if int(q.get("exam_year") or 0) > int(existing.get("exam_year") or 0):
                seen[key] = q
    return list(seen.values())


files = [
    ("satt_academy_mcq_no_diagram.json",  "satt_academy_mcq_no_diagram_dedup.json"),
    ("satt_academy_mcq_diagram_only.json", "satt_academy_mcq_diagram_only_dedup.json"),
]

for input_file, output_file in files:
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    deduped = dedup_by_recent_year(data)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)

    print(f"{input_file}")
    print(f"  Before : {len(data)}")
    print(f"  After  : {len(deduped)}  (removed {len(data) - len(deduped)} duplicates)")
    print(f"  Output : {output_file}")
