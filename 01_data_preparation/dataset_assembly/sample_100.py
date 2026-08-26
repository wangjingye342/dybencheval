import os
import json
import itertools


def get_line_at_index(file_path, target_index):
    """
    辅助函数：读取指定文件的第 target_index 行。
    如果行不存在（文件太短），返回 None。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for current_index, line in enumerate(f):
                if current_index == target_index:
                    return line.strip()
    except Exception:
        return None
    return None


def sample_diverse_data(source_root, output_dir, target_samples=3):
    """
    遍历目录，在每个最小子目录中，尽可能从不同的jsonl文件中抽取数据。
    采用轮询策略：先取每个文件的第1条，再取第2条...直到凑够3条。
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file_path = os.path.join(output_dir, "combined_diverse_sampled.jsonl")

    total_folders_processed = 0
    total_lines_extracted = 0

    print(f"开始扫描根目录: {source_root}")

    with open(output_file_path, 'w', encoding='utf-8') as outfile:

        for root, dirs, files in os.walk(source_root):
            # 1. 获取当前目录下所有的 jsonl 文件路径
            jsonl_files = [os.path.join(root, f) for f in files if f.endswith('.jsonl')]

            if jsonl_files:
                collected_in_folder = 0

                # 2. 开始轮询抽取 (Round-Robin)
                # line_idx 代表我们要取文件的第几行 (0=第一行, 1=第二行...)
                # 我们假设只需要在前几行就能凑够数据，设置一个安全上限比如10，防止死循环
                for line_idx in range(10):
                    if collected_in_folder >= target_samples:
                        break

                    # 标记这一轮循环（扫描所有文件）是否有收获
                    data_found_in_pass = False

                    # 遍历每一个文件
                    for file_path in jsonl_files:
                        if collected_in_folder >= target_samples:
                            break

                        # 尝试读取该文件的第 line_idx 行
                        line_content = get_line_at_index(file_path, line_idx)

                        if line_content:
                            try:
                                # 校验并写入
                                json_obj = json.loads(line_content)
                                # (可选) 写入来源信息方便调试
                                # json_obj['_source_file'] = os.path.basename(file_path)
                                outfile.write(json.dumps(json_obj, ensure_ascii=False) + '\n')

                                collected_in_folder += 1
                                total_lines_extracted += 1
                                data_found_in_pass = True
                            except json.JSONDecodeError:
                                continue  # 格式错误忽略

                    # 如果遍历了一遍所有文件，一行数据都没读到（说明所有文件都读完了），强制结束当前目录
                    if not data_found_in_pass:
                        break

                if collected_in_folder > 0:
                    total_folders_processed += 1

    print("-" * 30)
    print("处理完成！")
    print(f"共处理子目录数: {total_folders_processed}")
    print(f"共抽取数据条数: {total_lines_extracted}")
    print(f"结果已保存在: {output_file_path}")


if __name__ == "__main__":
    # === 配置路径 ===
    SOURCE_ROOT = "./external/ablation/evaluation_metrics/size_calculation/final_dataset/DyBenchEval"
    OUTPUT_DIR = "./external/ablation/evaluation_metrics/size_calculation/final_dataset/DyBenchEval_Sampled"

    # 执行
    sample_diverse_data(SOURCE_ROOT, OUTPUT_DIR, target_samples=3)