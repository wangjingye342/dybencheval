import json
import os
import glob
from collections import defaultdict


def calculate_json_averages(folder_path):
    # 使用 defaultdict 构建一个嵌套字典，用于存储所有文件中的数值列表
    data_store = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    # 获取目录下所有的 json 文件
    json_pattern = os.path.join(folder_path, '*.json')
    files = glob.glob(json_pattern)

    if not files:
        print(f"在目录 '{folder_path}' 中未找到 JSON 文件。")
        return None

    print(f"正在读取并计算 {len(files)} 个文件...")

    # 1. 读取所有文件并收集数据
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                metrics = data.get('metrics', {})

                # --- 处理 overall (整体) ---
                if 'overall' in metrics:
                    for key, value in metrics['overall'].items():
                        if isinstance(value, (int, float)):
                            data_store['overall']['overall'][key].append(value)

                # --- 处理 by_scenario (按场景) ---
                if 'by_scenario' in metrics:
                    for scenario, values in metrics['by_scenario'].items():
                        for key, value in values.items():
                            if isinstance(value, (int, float)):
                                data_store['by_scenario'][scenario][key].append(value)

                # --- 处理 by_task (按任务) ---
                if 'by_task' in metrics:
                    for task, values in metrics['by_task'].items():
                        for key, value in values.items():
                            if isinstance(value, (int, float)):
                                data_store['by_task'][task][key].append(value)

        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {e}")

    # 2. 计算平均值
    final_result = {"metrics": {}}

    for main_cat, sub_cats in data_store.items():
        final_result["metrics"][main_cat] = {}

        for sub_cat, indicators in sub_cats.items():
            target_dict = {}
            for key, val_list in indicators.items():
                if val_list:
                    # 计算平均值，保留6位小数
                    avg_val = sum(val_list) / len(val_list)
                    target_dict[key] = round(avg_val, 6)

            if main_cat == 'overall':
                final_result["metrics"][main_cat] = target_dict
            else:
                final_result["metrics"][main_cat][sub_cat] = target_dict

    return final_result


if __name__ == "__main__":
    # 输入文件夹路径
    target_directory = 'output'
    # 输出文件名
    output_filename = 'averaged_metrics.json'

    if os.path.exists(target_directory):
        averages = calculate_json_averages(target_directory)

        if averages:
            # === 保存结果到文件 ===
            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    json.dump(averages, f, indent=4, ensure_ascii=False)

                print("-" * 30)
                print(f"✅ 成功！结果已保存至: {output_filename}")
                print("-" * 30)

            except Exception as e:
                print(f"❌ 保存文件时出错: {e}")
    else:
        print(f"❌ 错误: 找不到目录 '{target_directory}'，请确保代码与 output 文件夹在同一级目录。")