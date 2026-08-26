import json
import os


def filter_jsonl_by_id(input_dir, output_dir, ids_to_remove):
    """
    读取 input_dir 中的 jsonl 文件，剔除 ids_to_remove 中的 id，
    并将结果保存到 output_dir。
    """

    # 1. 检查并创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"已创建输出目录: {output_dir}")

    # 2. 将要删除的 ID 列表转换为集合 (Set)
    # 这一步非常重要：在集合中查找元素的时间复杂度是 O(1)，而在列表中是 O(n)。
    # 如果数据量大，使用 Set 会显著提升速度。
    remove_set = set(ids_to_remove)

    # 3. 遍历输入目录中的所有文件
    files_processed = 0
    for filename in os.listdir(input_dir):
        if not filename.endswith(".jsonl"):
            continue

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        print(f"正在处理: {filename} ...")

        try:
            with open(input_path, 'r', encoding='utf-8') as f_in, \
                    open(output_path, 'w', encoding='utf-8') as f_out:

                kept_count = 0
                removed_count = 0

                for line in f_in:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 获取当前条目的 ID
                        current_id = data.get("id")

                        # 核心逻辑：如果 ID 在排除集合中，则跳过（删除）；否则写入新文件
                        if current_id in remove_set:
                            removed_count += 1
                        else:
                            # ensure_ascii=False 保证中文字符正常显示，而不是显示为 \uXXXX
                            f_out.write(json.dumps(data, ensure_ascii=False) + "\n")
                            kept_count += 1

                    except json.JSONDecodeError:
                        print(f"  [警告] 文件 {filename} 中存在无法解析的 JSON 行，已跳过。")

            print(f"  - 完成: 保留 {kept_count} 条，删除 {removed_count} 条")
            files_processed += 1

        except Exception as e:
            print(f"  [错误] 处理文件 {filename} 时发生错误: {e}")

    print(f"\n全部处理完毕。共处理 {files_processed} 个文件。")


# --- 配置区域 ---

# 1. 输入包含 jsonl 文件的文件夹路径
source_directory = "./results_coherence_processed"

# 2. 输出结果的文件夹路径 (会自动创建)
target_directory = "./results_coherence_processed_clean"

# 3. 你想要删除的 ID 列表 (数组)
# 这里填写你的实际 ID 数据，可以是字符串或数字，取决于你的 JSON 结构
ids_to_block = [
    78,
    1,
    2,
    104,
    24,
    25,
    6,
    7,
    8,
    9,
    10,
    11,
    103,
    33,
    71,
    101,
    102,
    17,
    111,
    19,
]

# --- 运行主函数 ---
if __name__ == "__main__":
    # 为了防止误操作，建议确保输入和输出目录不一致
    if source_directory == target_directory:
        print("错误：输入目录和输出目录不能相同，以防止覆盖原始数据。")
    else:
        filter_jsonl_by_id(source_directory, target_directory, ids_to_block)