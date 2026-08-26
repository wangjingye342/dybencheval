import json
from pathlib import Path

name = "Humanity_Code_Generation"

INPUT_PATH = Path(
    "./external/generated_outputs/generated_data_" + name + ".jsonl"
)

OUTPUT_PATH = Path(
    "./external/cleaned_data/cleaned_" + name + ".json"
)


def extract_outer_json(text: str):
    """
    从任意文本中提取最外层 JSON 对象（{ ... }）
    若失败，返回 None
    """
    if not isinstance(text, str):
        return None

    start = text.find("{")
    if start == -1:
        return None

    stack = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            stack += 1
        elif text[i] == "}":
            stack -= 1
            if stack == 0:
                candidate = text[start:i + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    return None
    return None


def main():
    cleaned_results = []
    stats = {
        "total": 0,
        "has_generated_response": 0,
        "json_extracted": 0,
        "json_failed": 0
    }

    with INPUT_PATH.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            stats["total"] += 1
            line = line.strip()

            try:
                data = json.loads(line)
            except Exception:
                continue

            if "generated_response" not in data:
                continue

            stats["has_generated_response"] += 1
            gr = data["generated_response"]

            extracted_json = extract_outer_json(gr)

            if extracted_json is not None:
                stats["json_extracted"] += 1
                cleaned_results.append({
                    "index": idx,
                    "generated_json": extracted_json
                })
            else:
                stats["json_failed"] += 1
                cleaned_results.append({
                    "index": idx,
                    "generated_json": None,
                    "raw_generated_response": gr
                })

    with OUTPUT_PATH.open("w", encoding="utf-8") as wf:
        json.dump(cleaned_results, wf, ensure_ascii=False, indent=2)

    print("===== 处理完成 =====")
    for k, v in stats.items():
        print(f"{k}: {v}")
    print(f"\n输出文件: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
