import json
import pprint

with open('satt_academy_mcq_questions.json','r',encoding='utf-8') as f:
    data = json.load(f)

    pprint.pprint(len(data))

