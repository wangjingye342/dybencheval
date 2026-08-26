import json
import os
import re
from pathlib import Path


def sanitize_filename(name):
    """
    清洗字符串，使其可以作为合法的文件名。
    将非法字符替换为下划线。
    """
    if not isinstance(name, str):
        name = str(name)
    # 替换掉非字母、数字、中文、下划线、连字符的字符
    return re.sub(r'[^\w\u4e00-\u9fa5\-]', '_', name)


def split_jsonl_by_fields(input_file, output_dir):
    """
    根据 target_scenario 和 target_task 字段将 jsonl 数据分组保存。

    Args:
        input_file (str): 输入的 .jsonl 文件路径
        output_dir (str): 输出目录路径
    """

    # 1. 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"📂 创建输出目录: {output_dir}")

    print(f"🚀 开始处理文件: {input_file} ...")

    count_dict = {}  # 用于统计每个分组的数据量
    processed_count = 0

    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # 2. 获取分组字段，如果不存在则使用默认值 'unknown'
                    scenario = data.get('target_scenario', 'unknown')
                    task = data.get('target_task', 'unknown')

                    # 3. 生成合法的文件名
                    safe_scenario = sanitize_filename(scenario)
                    safe_task = sanitize_filename(task)

                    # 组合文件名，例如: math_calculation.jsonl
                    filename = f"{safe_scenario}__{safe_task}.jsonl"
                    output_path = os.path.join(output_dir, filename)

                    # 4. 追加写入文件 (mode='a')
                    # ensure_ascii=False 保证中文正常显示
                    with open(output_path, 'a', encoding='utf-8') as f_out:
                        f_out.write(json.dumps(data, ensure_ascii=False) + '\n')

                    # 统计数据
                    if filename not in count_dict:
                        count_dict[filename] = 0
                    count_dict[filename] += 1
                    processed_count += 1

                    # 每处理 5000 行打印一次进度（可选）
                    if processed_count % 5000 == 0:
                        print(f"⏳ 已处理 {processed_count} 行...")

                except json.JSONDecodeError:
                    print(f"⚠️ 跳过无效的 JSON 行: {line[:50]}...")
                except Exception as e:
                    print(f"❌ 写入时出错: {e}")

    except FileNotFoundError:
        print(f"❌ 找不到输入文件: {input_file}")
        return

    print("-" * 30)
    print(f"✅ 处理完成！共处理 {processed_count} 行数据。")
    print(f"📂 文件已保存至: {output_dir}")
    print("📊 分组统计:")

    # 按数据量从大到小打印前10个分组
    sorted_stats = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_stats[:10]:
        print(f"  - {name}: {count} 行")
    if len(sorted_stats) > 10:
        print(f"  ... 以及其他 {len(sorted_stats) - 10} 个文件")


# --- 使用示例 ---
if __name__ == "__main__":
    # 配置路径
    INPUT_FILE = 'D:/STUDY/2026-project1/project1/main_work/模型再评价/人工评价结果/最终数据集/merged_data.jsonl'  # 你的源文件路径
    OUTPUT_DIR = './split_results'  # 结果保存的文件夹

    split_jsonl_by_fields(INPUT_FILE, OUTPUT_DIR)