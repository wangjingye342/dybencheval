import json
import os
from collections import OrderedDict

# ================= 配置区域 =================
# 1. 第一部分源目录
SOURCE_ROOT_DIR_1 = r"./data/raw_datasets/existing_datasets"

# 2. 第二部分源目录
SOURCE_ROOT_DIR_2 = r"./data/raw_datasets/generated_datasets"

# 3. 全集大文件路径
INPUT_BIG_FILE = r"./external/metrics/00/seed&response/qwen3-8b_seed_response_extracted.jsonl"

# 4. 输出结果文件路径
OUTPUT_FILE = r"./traced/qwen3-8b_seed_response_full.jsonl"


# ===========================================

def normalize_json_content(text_content):
    """
    【核心修复】标准化函数
    尝试将字符串解析为 JSON 对象，并按 Key 排序重新序列化。
    """
    if not isinstance(text_content, str):
        return str(text_content).strip()

    try:
        # 1. 尝试解析为 Python 对象
        obj = json.loads(text_content)
        # 2. 重新转回字符串：按 Key 排序，无空格紧凑格式，确保中文不乱码
        return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    except (json.JSONDecodeError, TypeError):
        # 如果不是 JSON 格式（比如只是普通文本），直接去空格返回
        return text_content.strip()


def build_source_index(root_dir, label="默认"):
    """
    建立索引：使用【标准化后】的字符串作为 Key
    """
    print(f"正在扫描[{label}]源目录: {root_dir} 建立索引...")
    source_map = {}
    file_count = 0

    for current_root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".jsonl"):
                file_path = os.path.join(current_root, file)
                path_parts = os.path.normpath(file_path).split(os.sep)

                # 路径解析逻辑：
                # root/.../Humanity/3_写作能力/file.jsonl
                # 倒数第2级是 Task, 倒数第3级是 Scenario
                try:
                    task_name = path_parts[-2]
                    scenario_name = path_parts[-3]
                except IndexError:
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            raw_line = line.strip()
                            if not raw_line: continue

                            # 标准化内容作为 Key
                            normalized_key = normalize_json_content(raw_line)

                            source_map[normalized_key] = {
                                "scenario": scenario_name,
                                "task": task_name,
                                "original_file": file
                            }
                    file_count += 1
                except Exception as e:
                    print(f"读取错误 {file}: {e}")

    print(f"[{label}] 索引建立完成。扫描文件: {file_count} 个，条目: {len(source_map)} 条。")
    return source_map


def insert_metadata_at_position(original_data, scenario, task):
    """
    将 scenario 和 task 插入到字典的第 2 和 第 3 位
    """
    new_data = OrderedDict()
    keys = list(original_data.keys())

    if keys:
        first_key = keys[0]
        new_data[first_key] = original_data[first_key]

    new_data["scenario"] = scenario
    new_data["task"] = task

    for k in keys[1:]:
        if k not in ["scenario", "task"]:
            new_data[k] = original_data[k]

    return new_data


def process_dataset(input_path, output_path, global_source_map):
    """
    处理数据集：不再区分界限，对每一行都在 global_source_map 中查找
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"开始处理大文件，目标输出路径: {output_path}")
    print(f"策略：全量搜索 (不再区分行号界限)")

    match_count = 0
    failed_ids = []

    with open(input_path, 'r', encoding='utf-8') as fin, \
            open(output_path, 'w', encoding='utf-8') as fout:

        for idx, line in enumerate(fin):
            if not line.strip(): continue

            data = json.loads(line)
            current_seed_content = data.get('seed_text', '')

            # 标准化目标内容
            normalized_target = normalize_json_content(current_seed_content)

            # ================= 全局查找逻辑 =================
            # 直接在合并后的大索引中查找
            source_info = global_source_map.get(normalized_target)
            # ===============================================

            if source_info:
                data = insert_metadata_at_position(
                    data,
                    source_info['scenario'],
                    source_info['task']
                )
                match_count += 1
            else:
                # 记录失败信息
                current_id = data.get('id', f"Line_{idx + 1}")
                failed_ids.append(f"Row {idx + 1} (ID: {current_id})")

            fout.write(json.dumps(data, ensure_ascii=False) + "\n")

    print("-" * 30)
    print(f"全集处理完毕！总共成功溯源: {match_count} 行。")

    if failed_ids:
        print(f"\n⚠️  注意：有 {len(failed_ids)} 条数据溯源失败。")
        print("失败的数据 ID 列表(前20个)：")
        print(failed_ids[:20])
        if len(failed_ids) > 20:
            print(f"...以及其他 {len(failed_ids) - 20} 条。")

        with open('./failed_log.txt', 'w', encoding='utf-8') as f:
            for fid in failed_ids:
                f.write(str(fid) + "\n")
        print("完整失败列表已保存至 ./failed_log.txt")
    else:
        print("\n✅ 完美！所有数据均已成功溯源。")


if __name__ == "__main__":
    # 1. 构建第一部分索引
    index1 = build_source_index(SOURCE_ROOT_DIR_1, label="Part 1 (不需要制造)")

    # 2. 构建第二部分索引
    index2 = build_source_index(SOURCE_ROOT_DIR_2, label="Part 2 (需要制造)")

    # 3. 合并索引 (将 index2 并入 index1，形成一个全集索引)
    # 这样对于大文件中的任意一条数据，都会在两个目录的总集合中查找
    print("正在合并两个目录的索引...")
    combined_index = {}
    combined_index.update(index1)
    combined_index.update(index2)

    print(f"索引合并完成。总计唯一条目数: {len(combined_index)}")

    # 4. 全量处理
    process_dataset(INPUT_BIG_FILE, OUTPUT_FILE, combined_index)