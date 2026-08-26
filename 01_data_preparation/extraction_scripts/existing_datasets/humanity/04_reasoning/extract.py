import json
import random
import os

# 定义输入文件路径
input_path = "./external/ablation/evaluation_metrics/size_calculation/所有数据集/existing_datasets/Humanity/4_推理能力/train-3.json"

# 定义输出文件路径 (保存在当前目录下，文件名为 sampled_data.jsonl)
output_path = "sampled_data_20.jsonl"


def sample_and_save(input_file, output_file, sample_size=20):
    # 1. 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误：找不到文件 - {input_file}")
        return

    try:
        # 2. 读取 JSON 数据
        print(f"正在读取文件: {input_file} ...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 确认数据是一个列表
        if not isinstance(data, list):
            print("错误：源文件格式不是 JSON 列表（List），无法直接抽取。")
            return

        # 3. 随机抽取数据
        total_count = len(data)
        print(f"原始数据共 {total_count} 条。")

        if total_count < sample_size:
            print(f"警告：原始数据少于 {sample_size} 条，将导出所有数据。")
            sampled_data = data
        else:
            sampled_data = random.sample(data, sample_size)
            print(f"已随机抽取 {sample_size} 条数据。")

        # 4. 写入 JSONL 格式
        # JSONL 特点：每一行是一个独立的 JSON 对象
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for entry in sampled_data:
                # ensure_ascii=False 保证中文字符正常显示，不转义为 Unicode 编码
                json_line = json.dumps(entry, ensure_ascii=False)
                f_out.write(json_line + '\n')

        print(f"成功！数据已保存至: {output_file}")

    except json.JSONDecodeError:
        print("错误：文件不是有效的 JSON 格式。请检查源文件是否已经是 JSONL 或已损坏。")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    sample_and_save(input_path, output_path)