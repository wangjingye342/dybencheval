import json
import os
import re
from glob import glob
from collections import OrderedDict

# ================= 配置区域 =================
# 输入文件夹路径
INPUT_DIR = "./response-gemini"

# 输出文件夹路径
OUTPUT_DIR = INPUT_DIR + "_processed"

# 候选 Key 列表
CANDIDATE_KEYS = [
    "eval_response",
]

# 【核心修改 1】：正则保持不变，支持捕获字母（单词）和数字
# 解析说明：
# 1. ([a-zA-Z]+|[-\d\.]+) -> 捕获组支持：
#       a. [a-zA-Z]+   : 纯字母单词（匹配 Pass, PASS, Incorrect, INCORRECT 等）
#       b. [-\d\.]+    : 数字（匹配 0, 1, -1.5 等）
PATTERN = r"###\s*FINAL_RESULT:\s*(?:\[\[|\[)?\s*([a-zA-Z]+|[-\d\.]+)\s*(?:\]\]|\])?"


# ===========================================

def insert_at_position(original_dict, key, value, index=2):
    items = list(original_dict.items())
    items.insert(index, (key, value))
    return dict(items)


def smart_convert(value_str):
    """
    【核心修改 2】：关键词映射逻辑（不区分大小写）
    """
    # 1. 去除首尾空格
    clean_str = value_str.strip()

    # 2. 统一转为小写进行比较 (这样 Pass, PASS, pass 都会变成 'pass')
    lower_str = clean_str.lower()

    # === 关键词映射区域 ===
    if lower_str == "pass":  # 匹配 [[Pass]], [[PASS]], [[pass]]
        return 1
    if lower_str == "incorrect":  # 匹配 [[Incorrect]], [[INCORRECT]]
        return 0
    # ====================

    # 3. 尝试匹配数字
    try:
        if '.' in clean_str:
            return float(clean_str)
        return int(clean_str)
    except ValueError:
        # 如果既不是关键词也不是数字，返回原字符串
        return clean_str


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
                            # 智能转换（含 Pass->1, Incorrect->0）
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