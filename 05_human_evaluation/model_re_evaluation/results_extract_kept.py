import json
import re
from collections import OrderedDict

input_jsonl = "human_reviewed_0-129.jsonl"
output_jsonl = "最终数据集/保留part1.jsonl"

# 1. ```json ... ```
JSON_BLOCK = re.compile(
    r"```json\s*(\{.*?\})\s*```",
    re.DOTALL | re.IGNORECASE
)

# 2. ``` ... ```（不标语言）
GENERIC_BLOCK = re.compile(
    r"```\s*(\{.*?\})\s*```",
    re.DOTALL
)

def extract_json_candidates(text):
    """
    按优先级返回可能的 JSON 字符串
    """
    candidates = []

    # 优先级 1
    candidates.extend(JSON_BLOCK.findall(text))

    # 优先级 2
    candidates.extend(GENERIC_BLOCK.findall(text))

    # 优先级 3：启发式最大 JSON
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(text[start:end + 1])

    return candidates


with open(input_jsonl, "r", encoding="utf-8") as fin, \
     open(output_jsonl, "w", encoding="utf-8") as fout:

    for line in fin:
        if not line.strip():
            continue

        data = json.loads(line)

        # 1. 过滤 Keep
        if data.get("human_review", {}).get("human_decision") != "Keep (保留)":
            continue

        original_id = data.get("original_id")

        original_data = data.get("original_data", {})
        target_scenario = original_data.get("target_scenario")
        target_task = original_data.get("target_task")

        text = original_data.get("generated_response", "")
        if not text:
            continue

        candidates = extract_json_candidates(text)

        extracted_json = None
        for cand in candidates:
            try:
                extracted_json = json.loads(cand)
                break
            except json.JSONDecodeError:
                continue

        if extracted_json is None:
            continue

        # 2. 构造输出 JSON，控制字段顺序
        output_item = OrderedDict()
        output_item["my_generated_id"] = original_id
        output_item["target_scenario"] = target_scenario
        output_item["target_task"] = target_task

        for k, v in extracted_json.items():
            output_item[k] = v

        fout.write(json.dumps(output_item, ensure_ascii=False) + "\n")
