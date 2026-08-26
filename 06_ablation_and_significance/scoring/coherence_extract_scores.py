import json
import os
import re
from glob import glob
from collections import OrderedDict

# ================= 配置区域 =================
# 输入文件夹路径
INPUT_DIR = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/评估指标/2/results_coherence"

# 输出文件夹路径
OUTPUT_DIR = INPUT_DIR + "_processed"

# 候选 Key 列表
CANDIDATE_KEYS = [
    "eval_response",
]

# 【核心修改】：增强版正则表达式
# 解析说明：
# 1. ###FINAL_RESULT:\s* -> 匹配前缀和随后的空格
# 2. (?:\[\[|\[)?          -> 非捕获组，匹配 [[ 或 [，?表示该组可选（可有可无）
# 3. \s* -> 匹配数字前的空格（例如 [ 1 ]）
# 4. ([-\d\.]+)           -> 【捕获组】提取数字，支持整数、负数、小数
# 5. \s* -> 匹配数字后的空格
# 6. (?:\]\]|\])?         -> 非捕获组，匹配 ]] 或 ]，?表示该组可选
PATTERN = r"###FINAL_RESULT:\s*(?:\[\[|\[)?\s*([-\d\.]+)\s*(?:\]\]|\])?"


# ===========================================

def insert_at_position(original_dict, key, value, index=2):
    items = list(original_dict.items())
    items.insert(index, (key, value))
    return dict(items)


def smart_convert(value_str):
    try:
        # 去除可能残留的标点（以防万一）
        clean_str = value_str.strip()
        if '.' in clean_str:
            return float(clean_str)
        return int(clean_str)
    except ValueError:
        return value_str


def get_response_text(data_dict):
    """
    遍历候选Key列表，尝试获取非空的文本内容
    """
    for key in CANDIDATE_KEYS:
        if key in data_dict and data_dict[key]:
            return data_dict[key]
    return ""


def process_files():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 已创建输出目录: {OUTPUT_DIR}")

    jsonl_files = glob(os.path.join(INPUT_DIR, "*.jsonl"))

    if not jsonl_files:
        print("❌ 未在指定目录下找到 .jsonl 文件。")
        return

    print(f"🔍 发现 {len(jsonl_files)} 个文件，开始处理...")

    for file_path in jsonl_files:
        filename = os.path.basename(file_path)
        output_path = os.path.join(OUTPUT_DIR, filename.replace(".jsonl", "_scored.jsonl"))

        processed_count = 0
        match_count = 0

        with open(file_path, 'r', encoding='utf-8') as f_in, \
                open(output_path, 'w', encoding='utf-8') as f_out:

            for line in f_in:
                if not line.strip(): continue

                try:
                    data = json.loads(line)
                    processed_count += 1

                    response_text = get_response_text(data)

                    if not response_text:
                        # 没找到文本内容
                        eval_value = -1
                    else:
                        match = re.search(PATTERN, response_text)
                        if match:
                            raw_value = match.group(1)
                            eval_value = smart_convert(raw_value)
                            match_count += 1
                        else:
                            # 没匹配到正则
                            eval_value = -1

                    new_data = insert_at_position(data, "eval_result", eval_value, index=2)
                    f_out.write(json.dumps(new_data, ensure_ascii=False) + "\n")

                except json.JSONDecodeError:
                    print(f"⚠️ 文件 {filename} 解析错误，已跳过。")
                    continue

        print(f"✅ 处理完成: {filename}")
        print(f"   📊 提取成功率: {match_count}/{processed_count}")
        if processed_count > 0 and match_count == 0:
            print(f"   ❌ 注意：该文件没有任何数据被提取成功，请检查正则或内容格式！")

    print(f"\n🎉 所有任务完成！结果保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_files()