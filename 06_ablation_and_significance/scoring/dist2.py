import os
import json
import glob
import re

# ================= 配置区域 =================

# 输入目录（存放含有 response 的数据集）
INPUT_DIR = "./external/ablation/evaluation_metrics/3/results_correctness_processed_clean"
# 结果保存路径
OUTPUT_FILE = "./distinct2_scores_100.json"


# ================= 核心逻辑 =================

def tokenize(text):
    """
    简单的分词函数：
    1. 转小写
    2. 使用正则提取单词（忽略标点符号）
    """
    if not text:
        return []
    text = text.lower()
    # \w+ 匹配所有字母、数字和下划线，作为简单的分词依据
    # 这种方式对于英文和代码比较通用，中文环境下如果不分词则当作字符流处理
    tokens = re.findall(r'\w+', text)
    return tokens


def compute_corpus_distinct_2(responses):
    """
    计算整个语料库（当前文件所有response集合）的 Distinct-2
    公式: unique_bigrams / total_bigrams
    """
    all_bigrams = []

    for text in responses:
        tokens = tokenize(text)
        if len(tokens) < 2:
            continue
        # 生成二元组 (Bigrams)
        bigrams = list(zip(tokens, tokens[1:]))
        all_bigrams.extend(bigrams)

    if not all_bigrams:
        return 0.0

    unique_bigrams = set(all_bigrams)
    distinct_2 = len(unique_bigrams) / len(all_bigrams)

    return distinct_2


def process_distinct_calculation():
    if not os.path.exists(INPUT_DIR):
        print(f"错误: 输入目录不存在 {INPUT_DIR}")
        return

    jsonl_files = glob.glob(os.path.join(INPUT_DIR, "*.jsonl"))
    if not jsonl_files:
        print(f"在 {INPUT_DIR} 中未找到 .jsonl 文件")
        return

    results = {}
    print(f"开始计算 Distinct-2，共找到 {len(jsonl_files)} 个文件...\n")
    print(f"{'文件名':<60} | {'Distinct-2':<10}")
    print("-" * 75)

    for file_path in sorted(jsonl_files):
        file_name = os.path.basename(file_path)
        responses = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        data = json.loads(line)
                        # 提取 response 字段
                        if "original_response" in data and data["original_response"]:
                            responses.append(data["original_response"])
                    except json.JSONDecodeError:
                        continue

            # 计算该文件的 Distinct-2
            score = compute_corpus_distinct_2(responses)
            results[file_name] = score

            print(f"{file_name:<60} | {score:.5f}")

        except Exception as e:
            print(f"{file_name:<60} | Error: {e}")

    # 保存结果到文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print("-" * 75)
    print(f"\n计算完成！结果已保存至: {OUTPUT_FILE}")


if __name__ == "__main__":
    process_distinct_calculation()