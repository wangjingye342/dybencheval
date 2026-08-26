import os


def merge_two_jsonl(file_path_1, file_path_2, output_path):
    """
    将两个 jsonl 文件合并保存到一个新文件中。
    支持限制读取文件的行数。
    """

    # 定义一个内部函数来处理单个文件的读取和写入
    # 新增参数 max_lines: 如果不为 None，则只读取前 max_lines 行
    def append_file_content(source_file, target_handle, max_lines=None):
        if not os.path.exists(source_file):
            print(f"警告: 文件不存在 -> {source_file}")
            return

        print(f"正在读取: {os.path.basename(source_file)} ...")
        count = 0  # 计数器

        with open(source_file, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                # 如果设置了最大行数，且当前计数已达到上限，则停止读取
                if max_lines is not None and count >= max_lines:
                    print(f"  -> 已达到限制行数 {max_lines}，停止读取该文件。")
                    break

                line = line.strip()  # 去除首尾空白符（包括换行）
                if line:  # 确保不写入空行
                    target_handle.write(line + '\n')  # 统一加上换行符写入
                    count += 1  # 成功写入一行数据后，计数器+1

        print(f"  -> 实际写入: {count} 行")

    # 主逻辑
    print(f"开始合并...")
    try:
        with open(output_path, 'w', encoding='utf-8') as f_out:
            # 写入第一个文件，限制前 645 行
            append_file_content(file_path_1, f_out, max_lines=645)

            # 写入第二个文件，没有限制 (max_lines 默认为 None)
            append_file_content(file_path_2, f_out)

        print(f"合并成功！文件已保存至: {output_path}")

    except Exception as e:
        print(f"合并过程中发生错误: {e}")


# --- 使用示例 ---
if __name__ == "__main__":
    # 替换为你的实际文件路径
    FILE_A = "D:/STUDY/2026-project1/project1/main_work/测评_人工检验/sampled_dataset_大.jsonl"
    FILE_B = "D:/STUDY/2026-project1/project1/main_work/测评_人工检验/sampled_dataset_小.jsonl"
    RESULT_FILE = "D:/STUDY/2026-project1/project1/main_work/测评_人工检验/正确性120.jsonl"

    merge_two_jsonl(FILE_A, FILE_B, RESULT_FILE)