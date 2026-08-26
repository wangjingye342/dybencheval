import json
from pathlib import Path

# ======================
# 路径配置
# ======================

INPUT_FILE = Path(
    "D:/STUDY/2026-project1/project1/main_work/通用模型实验/results/api_results_qwen3-30b-a3b-instruct-2507.jsonl"
)

OUTPUT_FILE = Path(
    "D:/STUDY/2026-project1/project1/main_work/通用模型实验/api_results_qwen3-30b-a3b-instruct-2507_readable.json"
)

# ======================
# 转换逻辑
# ======================

def jsonl_to_readable_json(input_file: Path, output_file: Path):
    records = []

    with open(input_file, "r", encoding="utf-8") as fin:
        for line_num, line in enumerate(fin, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise RuntimeError(
                    f"JSON 解析失败，行号 {line_num}: {e}"
                )

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as fout:
        json.dump(
            records,
            fout,
            ensure_ascii=False,
            indent=2
        )

    print(f"[DONE] 共转换 {len(records)} 条记录")
    print(f"[DONE] 输出文件路径: {output_file}")

# ======================
# 运行入口
# ======================

if __name__ == "__main__":
    jsonl_to_readable_json(INPUT_FILE, OUTPUT_FILE)
