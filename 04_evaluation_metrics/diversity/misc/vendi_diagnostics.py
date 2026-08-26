import os
import json
from collections import Counter

# ================= 配置区域 =================
# 将这里替换为你的 llama-31-8b 数据集的完整或相对路径
FILE_PATH = "./results/ALL_api_results_llama-31-8b.jsonl"


# ============================================

def load_responses(filepath):
    """复用之前健壮的读取逻辑"""
    responses = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        raw_resp = item.get("response")
                        if isinstance(raw_resp, str) and raw_resp.strip():
                            responses.append(raw_resp.strip())
                    return responses
            except json.JSONDecodeError:
                f.seek(0)

            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        raw_resp = data.get("response")
                        if isinstance(raw_resp, str) and raw_resp.strip():
                            responses.append(raw_resp.strip())
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"读取文件时出错: {e}")
    return responses


def analyze_responses(responses):
    if not responses:
        print("未找到有效数据！")
        return

    total_count = len(responses)

    # 1. 计算平均长度 (以字符数为准)
    avg_length = sum(len(r) for r in responses) / total_count

    # 2. 统计完全相同的回复
    exact_match_counter = Counter(responses)
    top_exact_matches = exact_match_counter.most_common(5)

    # 3. 统计常见开头 (取前 5 个词)
    prefix_counter = Counter()
    for r in responses:
        words = r.split()
        if len(words) >= 5:
            prefix = " ".join(words[:5])
        else:
            prefix = r
        prefix_counter[prefix] += 1
    top_prefixes = prefix_counter.most_common(5)

    # 打印诊断报告
    print("=" * 50)
    print(f"📊 Llama-3.1-8b 诊断报告")
    print("=" * 50)
    print(f"总有效回复数: {total_count}")
    print(f"平均回复字符数: {avg_length:.1f} 字符\n")

    print("🚨 Top 5 最常出现的【完整回复】:")
    for text, count in top_exact_matches:
        percentage = (count / total_count) * 100
        # 截断过长的文本以方便显示
        display_text = text if len(text) < 60 else text[:57] + "..."
        print(f"[{count} 次, 占比 {percentage:.1f}%] {display_text}")

    print("\n🚩 Top 5 最常出现的【开头短语 (前5个词)】:")
    for prefix, count in top_prefixes:
        percentage = (count / total_count) * 100
        print(f"[{count} 次, 占比 {percentage:.1f}%] {prefix}")
    print("=" * 50)


if __name__ == "__main__":
    if not os.path.exists(FILE_PATH):
        print(f"找不到文件: {FILE_PATH}，请检查路径。")
    else:
        print(f"正在分析文件: {FILE_PATH} ...")
        responses = load_responses(FILE_PATH)
        analyze_responses(responses)