import json
import random

# 定义文件路径
FILE_PATH_A = "api_results_claude-opus-4-5-20251101-thinking.jsonl"
FILE_PATH_B = "api_results_gpt-5_2-thinking.jsonl"

# 定义输出文件路径
group = "./group4/"
OUTPUT_PATH_A = group + "sampled_1.jsonl"
OUTPUT_PATH_B = group + "sampled_2.jsonl"


def count_lines(filepath):
    """计算文件总行数"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return sum(1 for _ in f)


def add_line_number_first(data_dict, line_idx):
    """
    创建一个新字典，将行号作为第一个字段，
    然后合并原有数据。
    """
    # 使用 1-based 索引 (第一行为 1)，如果需要 0-based 改为 line_idx 即可
    new_data = {"line_number": line_idx + 1}
    new_data.update(data_dict)
    return new_data


def main():
    print("正在计算文件行数...")
    try:
        total_lines = count_lines(FILE_PATH_A)
    except FileNotFoundError:
        print(f"错误：找不到文件 {FILE_PATH_A}")
        return

    print(f"文件总行数: {total_lines}")

    if total_lines < 30:
        print("错误：文件行数不足 30 行，无法抽取。")
        return

    # 1. 从 0 到 total_lines-1 中随机抽取 30 个不重复的数字并排序
    # 排序是为了在遍历文件时按顺序提取，提高效率
    target_indices = set(random.sample(range(total_lines), 30))

    print(f"已生成 30 个随机行号。正在提取数据...")

    extracted_count = 0

    # 2. 同时打开两个输入文件和两个输出文件
    with open(FILE_PATH_A, 'r', encoding='utf-8') as f_a, \
            open(FILE_PATH_B, 'r', encoding='utf-8') as f_b, \
            open(OUTPUT_PATH_A, 'w', encoding='utf-8') as out_a, \
            open(OUTPUT_PATH_B, 'w', encoding='utf-8') as out_b:

        # 使用 zip 同时遍历两个文件，idx 为当前行索引
        for idx, (line_a, line_b) in enumerate(zip(f_a, f_b)):
            if idx in target_indices:
                try:
                    # 解析原始 JSON
                    json_a = json.loads(line_a.strip())
                    json_b = json.loads(line_b.strip())

                    # 插入行号字段
                    processed_a = add_line_number_first(json_a, idx)
                    processed_b = add_line_number_first(json_b, idx)

                    # 写入新文件
                    out_a.write(json.dumps(processed_a, ensure_ascii=False) + '\n')
                    out_b.write(json.dumps(processed_b, ensure_ascii=False) + '\n')

                    extracted_count += 1

                    # 如果已经找齐了30个，可以提前结束循环
                    if extracted_count >= 30:
                        break
                except json.JSONDecodeError:
                    print(f"警告：第 {idx + 1} 行 JSON 解析失败，跳过。")

    print("--- 处理完成 ---")
    print(f"已保存 Claude 抽样数据至: {OUTPUT_PATH_A}")
    print(f"已保存 GPT 抽样数据至: {OUTPUT_PATH_B}")


if __name__ == "__main__":
    main()