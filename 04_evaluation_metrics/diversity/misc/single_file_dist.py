import json
from collections import defaultdict


def calculate_distinct_ngrams(file_path):
    """
    计算 Distinct-1, Distinct-2, Distinct-3, Distinct-4 指标
    """
    # 用于存储所有样本的 n-gram，计算全局 Distinct
    # 也可以改为计算平均 Intra-Distinct，这里采用标准的全局 Distinct 计算方式
    ngrams_all = {1: [], 2: [], 3: [], 4: []}

    line_count = 0

    print(f"正在处理文件: {file_path} ...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    # 提取 response_text
                    response_text = data.get("response_text", "")

                    if not response_text:
                        continue

                    # 【可选预处理】
                    # 如果 response_text 本身是一个 JSON 字符串（如你的示例所示），
                    # 且你只希望计算其中 dialogue 或 summary 的多样性，而非 JSON 语法的多样性，
                    # 可以取消下面几行的注释：
                    # try:
                    #     inner_json = json.loads(response_text)
                    #     # 只提取对话内容和摘要作为文本
                    #     response_text = inner_json.get('dialogue', '') + " " + inner_json.get('summary', '')
                    # except:
                    #     pass # 如果解析失败，保留原字符串

                    # 简单的分词处理：转小写 + 按空格分割
                    # 对于中文数据，建议替换为 jieba.lcut(response_text)
                    tokens = response_text.lower().split()

                    if not tokens:
                        continue

                    # 生成 n-grams
                    for n in [1, 2, 3, 4]:
                        # 生成当前行的 n-gram 列表
                        current_ngrams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
                        ngrams_all[n].extend(current_ngrams)

                    line_count += 1

                except json.JSONDecodeError:
                    print(f"Skipping invalid JSON line: {line[:50]}...")
                    continue

    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return

    print(f"处理完成，共处理有效行数: {line_count}")
    print("-" * 30)

    # 计算并打印结果
    results = {}
    for n in [1, 2, 3, 4]:
        total_count = len(ngrams_all[n])
        unique_count = len(set(ngrams_all[n]))

        if total_count > 0:
            score = unique_count / total_count
        else:
            score = 0.0

        results[f'distinct_{n}'] = score
        print(f"Distinct-{n}: {score:.5f} (Unique: {unique_count} / Total: {total_count})")

    return results


if __name__ == "__main__":
    target_file = "D:/STUDY/2026-project1/project1/main_work/计算指标/0_final/final数据（指标2，3）/final/claude_all.jsonl"
    calculate_distinct_ngrams(target_file)