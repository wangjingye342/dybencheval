import json
import re

# =========================
# 1. 路径配置
# =========================
INPUT_PATH = "./external/human_evaluation/correctness_review/correctness_120_final.jsonl"
OUTPUT_PATH = "correctness_120_seed_response_extracted.jsonl"

# =========================
# 2. Seed 提取正则
# =========================
SEED_PATTERN = re.compile(
    r"#\s*Input\s*Seed\s*Data\s*\n([\s\S]*?)(?:\n# |\Z)",
    re.IGNORECASE
)

# =========================
# 3. 主处理逻辑
# =========================
total_lines = 0
json_lines = 0
skipped_lines = 0
seed_found_cnt = 0
used_eval_cnt = 0

with open(INPUT_PATH, "r", encoding="utf-8") as fin, \
     open(OUTPUT_PATH, "w", encoding="utf-8") as fout:

    for raw_line in fin:
        total_lines += 1
        line = raw_line.strip()

        # -------------------------
        # 3.1 跳过明显不是 JSON 的行
        # -------------------------
        if not line.startswith("{"):
            skipped_lines += 1
            continue

        try:
            item = json.loads(line)
            json_lines += 1
        except json.JSONDecodeError:
            skipped_lines += 1
            continue

        # -------------------------
        # 3.2 处理 used_prompt
        # -------------------------
        used_prompt = item.get("used_prompt", "")
        prompt_text = used_prompt

        if isinstance(used_prompt, str) and "constructed_prompt" in used_prompt:
            try:
                # 注意：eval 存在安全风险，仅在确保数据源可信时使用
                tmp = eval(used_prompt)
                if isinstance(tmp, dict) and "constructed_prompt" in tmp:
                    prompt_text = tmp["constructed_prompt"]
                    used_eval_cnt += 1
            except Exception:
                prompt_text = used_prompt

        # -------------------------
        # 3.3 提取 Seed
        # -------------------------
        seed_match = SEED_PATTERN.search(prompt_text)
        seed_text = seed_match.group(1).strip() if seed_match else ""
        seed_found = seed_match is not None

        if seed_found:
            seed_found_cnt += 1

        # -------------------------
        # 3.4 提取其他字段 (新增 model)
        # -------------------------
        response_text = item.get("response", "")
        # 获取 model 字段，如果没有则默认为空字符串或 None
        model_name = item.get("model", "")

        # -------------------------
        # 3.5 写输出
        # -------------------------
        # Python 3.7+ 字典保持插入顺序，将 model 放在第一个位置
        out_item = {
            "model": model_name,           # <--- 新增字段，且在第一位
            "seed_text": seed_text,
            "response_text": response_text,
            "seed_found": seed_found
        }

        fout.write(json.dumps(out_item, ensure_ascii=False) + "\n")

# =========================
# 4. 统计信息
# =========================
print("Total raw lines:", total_lines)
print("Valid JSON lines:", json_lines)
print("Skipped lines:", skipped_lines)
print("Seed extracted:", seed_found_cnt)
print("Used eval (constructed_prompt):", used_eval_cnt)
print("Output written to:", OUTPUT_PATH)