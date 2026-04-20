import json

input_file = "satt_academy_admission_questions.jsonl"
output_file = "satt_academy_mcq_questions.json"

mcq_questions = []

with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        if record.get("question_type") == "mcq":
            mcq_questions.append(record)

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(mcq_questions, f, ensure_ascii=False, indent=2)

print(f"Filtered {len(mcq_questions)} MCQ questions -> {output_file}")
