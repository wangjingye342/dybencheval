import json
from pathlib import Path

# =========================
# 路径配置
# =========================
input_path = Path(
    "D:/STUDY/2026-project1/project1/main_work/output_problems/generated_data_Humanity_Code_Generation.jsonl"
)
output_path = Path(
    "D:/STUDY/2026-project1/project1/main_work/generated_response_only/Humanity_Code_Generation.jsonl"
)

# =========================
# 主处理逻辑
# =========================
with input_path.open("r", encoding="utf-8") as fin, \
     output_path.open("w", encoding="utf-8") as fout:

    for line_idx, line in enumerate(fin, start=1):
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            print(f"[Warning] Line {line_idx}: JSON decode failed, skipped.")
            continue

        if "generated_response" not in data:
            print(f"[Warning] Line {line_idx}: 'generated_response' not found, skipped.")
            continue

        output_item = {
            "generated_response": data["generated_response"]
        }

        fout.write(
            json.dumps(output_item, ensure_ascii=False) + "\n"
        )

print(f"Extraction finished. Output saved to:\n{output_path}")
