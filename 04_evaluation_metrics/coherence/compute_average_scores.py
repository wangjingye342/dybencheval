import os
import json
import glob


def calculate_per_file_average_eval_result(directory_path, output_filename="model_eval_results_summary.txt"):
    """
    遍历指定目录下的所有 .jsonl 文件，分别计算每个文件中 'eval_result' 的平均值，
    并计算总平均值，最后将结果保存。
    """
    # 用于统计所有文件的总数据
    total_eval_sum = 0.0
    total_valid_record_count = 0

    # 存储每个文件的统计结果
    file_results = {}

    file_pattern = os.path.join(directory_path, "*.jsonl")
    jsonl_files = glob.glob(file_pattern)

    if not jsonl_files:
        print(f"在目录 '{directory_path}' 中没有找到 .jsonl 文件。")
        return

    print(f"找到 {len(jsonl_files)} 个文件，开始逐个分析...\n")

    for file_path in jsonl_files:
        filename = os.path.basename(file_path)
        file_sum = 0.0
        file_valid_count = 0

        with open(file_path, 'r', encoding='utf-8') as file:
            for line_number, line in enumerate(file, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    if 'eval_result' in data:
                        eval_value = float(data['eval_result'])
                        file_sum += eval_value
                        file_valid_count += 1

                        # 累加到总计中
                        total_eval_sum += eval_value
                        total_valid_record_count += 1
                except json.JSONDecodeError:
                    pass  # 忽略解析错误，保持输出整洁
                except (ValueError, TypeError):
                    pass  # 忽略非数字错误

        # 计算当前文件的平均值
        if file_valid_count > 0:
            file_average = file_sum / file_valid_count
            file_results[filename] = {
                'average': file_average,
                'count': file_valid_count
            }
        else:
            file_results[filename] = {
                'average': None,
                'count': 0
            }

    # 准备输出内容
    output_lines = []
    output_lines.append("=== 各模型 (文件) 评估结果平均值 ===\n")

    # 按文件名排序，方便查看
    for filename in sorted(file_results.keys()):
        stats = file_results[filename]
        if stats['count'] > 0:
            line_str = f"文件: {filename:<65} | 平均分: {stats['average']:.4f} (基于 {stats['count']} 条数据)"
        else:
            line_str = f"文件: {filename:<65} | 无有效的 'eval_result' 数据"

        print(line_str)
        output_lines.append(line_str + "\n")

    # 计算并添加总计信息
    output_lines.append("\n" + "=" * 80 + "\n")
    if total_valid_record_count > 0:
        overall_average = total_eval_sum / total_valid_record_count
        summary_str = f"【总体统计】共处理 {len(jsonl_files)} 个文件, 有效数据总计: {total_valid_record_count} 条, 总体平均分: {overall_average:.4f}"
        print("\n" + summary_str)
        output_lines.append(summary_str + "\n")
    else:
        print("\n未在任何文件中找到有效的 'eval_result' 数据。")
        output_lines.append("未在任何文件中找到有效的 'eval_result' 数据。\n")

    # 保存到文件
    output_path = os.path.join(directory_path, output_filename)
    with open(output_path, 'w', encoding='utf-8') as out_file:
        out_file.writelines(output_lines)

    print(f"\n详细统计结果已保存至: {output_path}")


if __name__ == "__main__":
    # 替换为你的实际路径
    target_directory = "response_gpt_re_ori_processed"
    calculate_per_file_average_eval_result(target_directory)