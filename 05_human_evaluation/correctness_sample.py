import os
import random
import glob


def extract_random_samples(input_dir, output_file, sample_size=60):
    """
    从指定目录下的所有jsonl文件中随机提取指定数量的数据行。
    """
    all_lines = []

    # 1. 寻找目录下所有的 jsonl 文件 (recursive=True 表示包含子文件夹)
    # 使用 glob 进行模式匹配查找
    search_pattern = os.path.join(input_dir, '**', '*.jsonl')
    files = glob.glob(search_pattern, recursive=True)

    print(f"正在扫描目录: {input_dir}")
    print(f"找到 {len(files)} 个 jsonl 文件。开始读取数据...")

    # 2. 读取所有数据行
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 去除首尾空白符后检查是否为空，确保只读取有效数据
                    if line.strip():
                        all_lines.append(line)
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")

    total_lines = len(all_lines)
    print(f"读取完成，共找到 {total_lines} 行数据。")

    # 3. 随机抽取
    if total_lines == 0:
        print("警告：没有找到任何数据行。")
        return

    # 如果总行数不足60行，则提取所有行；否则提取60行
    real_sample_size = min(sample_size, total_lines)
    selected_lines = random.sample(all_lines, real_sample_size)

    print(f"正在随机抽取 {real_sample_size} 行数据...")

    # 4. 保存到新文件
    try:
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for line in selected_lines:
                # write 原样写入，因为读取时保留了换行符，
                # 如果 line.strip() 过了，这里需要手动加 '\n'
                f_out.write(line)
        print(f"成功！数据已保存至: {output_file}")
    except Exception as e:
        print(f"写入文件时出错: {e}")


# --- 配置区域 ---
if __name__ == "__main__":
    # 输入目录路径 (请修改这里)
    INPUT_DIRECTORY = "./external/model_runs/Backup_datasets/small_models"

    # 输出文件路径 (请修改这里)
    OUTPUT_FILE = "sampled_dataset_小.jsonl"

    # 运行函数
    extract_random_samples(INPUT_DIRECTORY, OUTPUT_FILE, sample_size=60)