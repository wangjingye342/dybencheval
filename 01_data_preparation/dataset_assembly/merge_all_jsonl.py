import os


def merge_jsonl_recursive(source_dir, output_filepath):
    """
    递归合并指定目录下所有的 jsonl 文件，并报告每个文件的行数。
    """
    if not os.path.exists(source_dir):
        print(f"❌ 错误: 找不到目录 -> {source_dir}")
        return

    total_file_count = 0
    total_line_count = 0

    # 获取输出文件的绝对路径，防止死循环
    abs_output_path = os.path.abspath(output_filepath)

    print(f"📂 开始扫描目录: {source_dir}")
    print(f"💾 输出文件将保存为: {abs_output_path}")
    print("-" * 60)
    print(f"{'文件名':<40} | {'数据条数':<10}")  # 打印表头
    print("-" * 60)

    with open(output_filepath, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(source_dir):
            for filename in files:
                if filename.endswith('.jsonl'):
                    full_path = os.path.join(root, filename)

                    # 跳过输出文件本身
                    if os.path.abspath(full_path) == abs_output_path:
                        continue

                    current_file_lines = 0  # 初始化当前文件的行数计数器

                    try:
                        with open(full_path, 'r', encoding='utf-8') as infile:
                            for line in infile:
                                line = line.strip()
                                if line:
                                    outfile.write(line + '\n')
                                    current_file_lines += 1
                                    total_line_count += 1

                        total_file_count += 1
                        # 打印当前文件的统计信息，使用文件名（如果文件名太长则截断显示）
                        display_name = filename if len(filename) < 35 else filename[:32] + "..."
                        print(f"{display_name:<40} | {current_file_lines} 条")

                    except Exception as e:
                        print(f"⚠️ 读取出错 {filename}: {e}")

    print("-" * 60)
    print(f"🎉 合并完成!")
    print(f"📊 总计文件: {total_file_count} 个")
    print(f"📊 总计数据: {total_line_count} 条")
    print(f"📁 结果保存: {abs_output_path}")


if __name__ == "__main__":
    # --- 配置区域 ---
    input_directory = r"./external/ablation/evaluation_metrics/size_calculation/final_dataset/DyBenchEval"
    output_filename = "merged_all_dybenchy.jsonl"

    # --- 执行 ---
    merge_jsonl_recursive(input_directory, output_filename)