import json
import os


def process_and_merge_jsonl():
    # 1. 定义文件路径
    name = "gemini3pro"
    path_coherence = "./external/metrics/2/response_level3_backup3_processed/" + name + "_seed_response_extracted_prompt_level3_response_scored.jsonl"
    path_correctness = "./external/metrics/3/response_processed_final/" + name + "_seed_response_extracted_prompt_level3_response_scored.jsonl"
    path_main_source = "./external/metrics/00/traced/" + name + "_seed_response_full.jsonl"

    output_dir = "./final"
    output_filename = name + "_all.jsonl"
    output_path = os.path.join(output_dir, output_filename)

    # 2. 读取辅助数据建立查找字典 (Hash Map)
    coherence_map = {}
    correctness_map = {}

    print("正在读取 Coherence 数据...")
    try:
        with open(path_coherence, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                # 提取 id 和 eval_result (重命名为 coherence)
                if 'id' in data:
                    coherence_map[data['id']] = data.get('eval_result')
    except FileNotFoundError:
        print(f"错误: 找不到文件 {path_coherence}")
        return

    print("正在读取 Correctness 数据...")
    try:
        with open(path_correctness, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                # 提取 id 和 eval_result (重命名为 correctness)
                if 'id' in data:
                    correctness_map[data['id']] = data.get('eval_result')
    except FileNotFoundError:
        print(f"错误: 找不到文件 {path_correctness}")
        return

    # 3. 处理主文件并插入数据
    print("正在合并数据并写入新文件...")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    processed_count = 0

    try:
        with open(path_main_source, 'r', encoding='utf-8') as f_in, \
                open(output_path, 'w', encoding='utf-8') as f_out:

            for line in f_in:
                if not line.strip(): continue
                data = json.loads(line)

                record_id = data.get('id')

                # 获取对应的分数，如果没有找到则为 None
                val_coherence = coherence_map.get(record_id)
                val_correctness = correctness_map.get(record_id)

                # --- 核心逻辑：插入到第4和第5位 ---
                # Python 3.7+ 字典是有序的。我们将字典转为 list(items) 进行切片重组
                items = list(data.items())

                # 取前3个元素 (位置 1, 2, 3)
                new_items = items[:3]

                # 插入 coherence (位置 4)
                new_items.append(("coherence", val_coherence))

                # 插入 correctness (位置 5)
                new_items.append(("correctness", val_correctness))

                # 接上剩余的元素
                new_items.extend(items[3:])

                # 重建字典
                new_data = dict(new_items)

                # 写入文件，ensure_ascii=False 保证中文正常显示
                f_out.write(json.dumps(new_data, ensure_ascii=False) + "\n")
                processed_count += 1

        print(f"处理完成！成功处理了 {processed_count} 条数据。")
        print(f"文件已保存至: {output_path}")

    except FileNotFoundError:
        print(f"错误: 找不到主源文件 {path_main_source}")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    process_and_merge_jsonl()