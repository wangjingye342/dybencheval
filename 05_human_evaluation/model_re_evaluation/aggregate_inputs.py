import json
from pathlib import Path

# ======================
# 1. 路径配置
# ======================
INPUT_DIR = Path("./external/generated_outputs")
OUTPUT_FILE = Path("./external/model_re_evaluation/inputs.jsonl")

# ======================
# 2. 主处理逻辑
# ======================
def merge_jsonl_files(input_dir: Path, output_file: Path):
    jsonl_files = list(input_dir.rglob("*.jsonl"))
    print(f"Found {len(jsonl_files)} jsonl files.")

    total_written = 0

    with output_file.open("w", encoding="utf-8") as fout:
        for file_path in jsonl_files:
            with file_path.open("r", encoding="utf-8") as fin:
                for line_num, line in enumerate(fin, start=1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        print(f"[Warning] JSON decode error in {file_path} line {line_num}")
                        continue

                    # 检查字段是否存在
                    if not all(k in data for k in ("target_scenario", "target_task", "generated_response")):
                        continue

                    merged_item = {
                        "target_scenario": data["target_scenario"],
                        "target_task": data["target_task"],
                        "generated_response": data["generated_response"],
                    }

                    fout.write(json.dumps(merged_item, ensure_ascii=False) + "\n")
                    total_written += 1

    print(f"Done. Total records written: {total_written}")
    print(f"Output saved to: {output_file}")


# ======================
# 3. 执行
# ======================
if __name__ == "__main__":
    merge_jsonl_files(INPUT_DIR, OUTPUT_FILE)
