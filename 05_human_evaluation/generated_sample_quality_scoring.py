import json
import random
from pathlib import Path
from typing import Any

DATA_PATH = Path(
    "./external/generated_outputs/generated_data_Humanity_Code_Generation.jsonl"
)
REVIEW_PATH = Path(
    "./external/review_results.jsonl"
)

MAX_STR_LEN = 800   # 防止单字段刷屏


# ========= 通用递归打印 =========

def pretty_print(obj: Any, indent=0, max_depth=4):
    prefix = " " * indent

    if indent // 2 >= max_depth:
        print(prefix + "... (depth truncated)")
        return

    if isinstance(obj, dict):
        for k, v in obj.items():
            print(f"{prefix}- {k} ({type(v).__name__})")
            pretty_print(v, indent + 2, max_depth)

    elif isinstance(obj, list):
        print(f"{prefix}[list] len={len(obj)}")
        for i, v in enumerate(obj[:5]):
            print(f"{prefix}  [{i}] ({type(v).__name__})")
            pretty_print(v, indent + 4, max_depth)
        if len(obj) > 5:
            print(prefix + "  ... (list truncated)")

    elif isinstance(obj, str):
        content = obj[:MAX_STR_LEN]
        print(prefix + repr(content))
        if len(obj) > MAX_STR_LEN:
            print(prefix + "... (string truncated)")

    else:
        print(prefix + repr(obj))


# ========= 主审核逻辑 =========

def review(mode="random"):
    with DATA_PATH.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    indices = list(range(len(lines)))
    if mode == "random":
        random.shuffle(indices)

    for idx in indices:
        raw_line = lines[idx].strip()

        print("\n" + "=" * 90)
        print(f"[样本索引] {idx}")

        try:
            data = json.loads(raw_line)
            print("[JSON 解析成功]")
        except Exception as e:
            print("[❌ JSON 解析失败]")
            print(raw_line[:1000])
            data = None

        print("\n[结构展开]")
        if data is not None:
            pretty_print(data)
        else:
            print("原始文本：")
            print(raw_line[:2000])

        print("\n[人工质量评估]")
        print("1 = 高质量（Humanity + Code Generation 明确成立）")
        print("2 = 中等（可修复 / 有偏差）")
        print("3 = 低质量（任务或内容不成立）")
        print("4 = 垃圾 / 崩坏输出")

        rating = input("请选择 (1/2/3/4): ").strip()
        comment = input("人工备注（可留空）: ").strip()

        record = {
            "index": idx,
            "rating": rating,
            "comment": comment,
            "raw_json_valid": data is not None,
            "raw_text": raw_line  # 保留原始生成，极其重要
        }

        with REVIEW_PATH.open("a", encoding="utf-8") as wf:
            wf.write(json.dumps(record, ensure_ascii=False) + "\n")

        cont = input("\n继续？(y/n): ").strip().lower()
        if cont != "y":
            break


if __name__ == "__main__":
    review()
