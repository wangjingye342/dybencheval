import json

input_jsonl = "human_reviewed_130-259.jsonl"
output_jsonl = "human_reviewed_130-259_dedup.jsonl"

latest_records = {}

with open(input_jsonl, "r", encoding="utf-8") as fin:
    for line in fin:
        if not line.strip():
            continue

        data = json.loads(line)
        original_id = data.get("original_id")

        # 若 original_id 相同，后出现的直接覆盖
        latest_records[original_id] = data

with open(output_jsonl, "w", encoding="utf-8") as fout:
    for record in latest_records.values():
        fout.write(json.dumps(record, ensure_ascii=False) + "\n")
