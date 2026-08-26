import json
import random


def sample_json_data(input_path, output_path, sample_size=20):
    try:
        # 1. 读取数据
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 检查数据是否为列表
        if not isinstance(data, list):
            print("错误：JSON文件的根节点不是列表，无法直接抽取。")
            return

        # 2. 随机抽取
        # 如果数据总量少于20条，则全部取出，防止报错
        real_sample_size = min(sample_size, len(data))
        sampled_data = random.sample(data, real_sample_size)

        print(f"原数据共 {len(data)} 条，已随机抽取 {real_sample_size} 条。")

        # 3. 保存结果
        with open(output_path, 'w', encoding='utf-8') as f:
            # ensure_ascii=False 保证中文字符正常显示
            # indent=4 保证输出格式美观易读
            json.dump(sampled_data, f, ensure_ascii=False, indent=4)

        print(f"抽取的数据已保存至: {output_path}")

    except FileNotFoundError:
        print(f"错误：找不到文件 {input_path}")
    except json.JSONDecodeError:
        print(f"错误：文件 {input_path} 不是有效的JSON格式")


# --- 使用示例 ---
# 请将文件名替换为你实际的文件路径
input_file = 'D:/STUDY/2026-project1/project1/main_work/通用模型实验/api_results_qwen3-max_readable.json'  # 源文件
output_file = 'sampled_20.json'  # 输出文件

sample_json_data(input_file, output_file)