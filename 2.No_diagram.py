import json
import re

input_file = "satt_academy_mcq_questions.json"
output_no_diagram = "satt_academy_mcq_no_diagram.json"
output_diagram_only = "satt_academy_mcq_diagram_only.json"

# Patterns that indicate the question requires a diagram/image to solve.
# English patterns use specific contextual phrases to avoid false positives
# like "figure of speech" or "figured".
DIAGRAM_PATTERNS = re.compile(
    # Bengali referential patterns
    r"নিচের চিত্র"
    r"|উপরের চিত্র"
    r"|চিত্র অনুযায়ী"
    r"|চিত্র থেকে"
    r"|চিত্রে দেখানো"
    r"|চিত্রটিতে"
    r"|চিত্রটি দেখ"
    r"|নিচের ছবি"
    r"|উপরের ছবি"
    # English: only phrases that mean a visual figure must be seen
    r"|\bdiagram\b"
    r"|in the figure"
    r"|the figure below"
    r"|the figure above"
    r"|the figure on the"
    r"|the figure at the"
    r"|figure given below"
    r"|figure given above"
    r"|figure shown"
    r"|shown in the figure"
    r"|the following figure",
    re.IGNORECASE
)

with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

no_diagram = []
diagram_only = []

for q in data:
    has_image = q.get("question_image") is not None
    text = q.get("question_text", "")
    mentions_diagram = bool(DIAGRAM_PATTERNS.search(text))

    if has_image or mentions_diagram:
        diagram_only.append(q)
    else:
        no_diagram.append(q)

with open(output_no_diagram, "w", encoding="utf-8") as f:
    json.dump(no_diagram, f, ensure_ascii=False, indent=2)

with open(output_diagram_only, "w", encoding="utf-8") as f:
    json.dump(diagram_only, f, ensure_ascii=False, indent=2)

print(f"Total MCQs       : {len(data)}")
print(f"No diagram       : {len(no_diagram)}  -> {output_no_diagram}")
print(f"Diagram/image    : {len(diagram_only)}  -> {output_diagram_only}")
