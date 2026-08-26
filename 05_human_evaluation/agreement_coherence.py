import json


def load_data_to_dict(file_path):
    """
    读取 JSONL 文件并将其转换为以 id 为键的字典。
    """
    data_dict = {}
    print(f"正在加载文件: {file_path}")
    try:
        # 使用 utf-8-sig 防止 BOM 头
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    item = json.loads(line.strip())
                    obj_id = item.get('id')
                    # 严格判断 None，允许 id 为 0
                    if obj_id is not None:
                        data_dict[obj_id] = item
                    else:
                        print(f"警告: 第 {line_num} 行缺少 'id' 字段，已跳过。")
                except json.JSONDecodeError:
                    print(f"警告: 第 {line_num} 行 JSON 解析失败，已跳过。")
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return None
    return data_dict


def calculate_accuracy():
    # --- 1. 文件路径配置 ---
    file_path_a = "D:/STUDY/2026-project1/project1/main_work/计算指标/2/backup/level12_response_processed/sample1_prompt_level1_response_scored.jsonl"
    file_path_b = "D:/STUDY/2026-project1/project1/main_work/计算指标/2/backup/level12_response_processed/sample2_prompt_level1_response_scored.jsonl"
    file_path_label = "D:/STUDY/2026-project1/project1/main_work/计算指标/2/annotation_results_fixed_100.jsonl"

    # --- 2. 加载模型输出文件到内存 ---
    dict_a = load_data_to_dict(file_path_a)
    dict_b = load_data_to_dict(file_path_b)

    if dict_a is None or dict_b is None:
        print("由于文件读取失败，程序终止。")
        return

    total_count = 0
    correct_count = 0

    incorrect_ids = []  # 存储判断错误的 ID
    tie_score_ids = []  # 存储分数相同的 ID (用于统计)
    missing_ids_count = 0

    print("-" * 30)
    print(f"开始基于 ID 进行匹配和计算...")

    try:
        with open(file_path_label, 'r', encoding='utf-8-sig') as f_lbl:
            for line_num, line_lbl in enumerate(f_lbl, 1):
                try:
                    item_lbl = json.loads(line_lbl.strip())
                    current_id = item_lbl.get('id')
                    label = item_lbl.get('label')

                    if current_id is None:
                        print(f"Label文件第 {line_num} 行缺少 'id'，跳过。")
                        continue

                    # --- 4. 核心匹配逻辑 ---
                    if current_id not in dict_a or current_id not in dict_b:
                        missing_ids_count += 1
                        continue

                    item_a = dict_a[current_id]
                    item_b = dict_b[current_id]

                    # 转换为 float 进行比较
                    score_a = float(item_a.get('eval_result', 0))
                    score_b = float(item_b.get('eval_result', 0))

                    # --- 统计：检测分数是否相同 ---
                    if score_a == score_b:
                        tie_score_ids.append(current_id)

                    # --- 5. 判别正确率逻辑 (修改后) ---
                    if label == "model_a":
                        total_count += 1
                        if score_a > score_b:
                            correct_count += 1
                        else:
                            incorrect_ids.append(current_id)

                    elif label == "model_b":
                        total_count += 1
                        if score_b > score_a:
                            correct_count += 1
                        else:
                            incorrect_ids.append(current_id)

                    elif label == "tie":
                        # 【新增逻辑】处理 label 为 tie 的情况
                        total_count += 1
                        # 如果人类认为是平局，且模型打分也完全相等，则算正确
                        if score_a == score_b:
                            correct_count += 1
                        else:
                            # 人类认为是平局，但模型给出了高低分，算错误
                            incorrect_ids.append(current_id)

                except Exception as e:
                    print(f"Label文件第 {line_num} 行处理出错: {e}")
                    continue

        # --- 6. 输出统计结果 ---
        print("-" * 30)
        print(f"处理完成。")
        print(f"Label文件总行数 (已处理): {line_num}")
        print(f"因 ID 缺失未匹配到的样本数: {missing_ids_count}")
        print(f"有效参与评测样本数 (Label为 A/B/tie 且 ID匹配成功): {total_count}")
        print(f"判定正确数: {correct_count}")

        if total_count > 0:
            acc = (correct_count / total_count) * 100
            print(f"正确率: {acc:.2f}%")
        else:
            print("未找到有效的样本，无法计算正确率。")

        print("-" * 30)

        # --- 输出判定错误的 ID ---
        if incorrect_ids:
            print(f"以下 ID 判定错误 (共 {len(incorrect_ids)} 个):")
            print(incorrect_ids)
        else:
            print("太棒了，没有发现判定错误的样本！")
        print("-" * 30)

    except FileNotFoundError as e:
        print(f"Label文件未找到，请检查路径: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    calculate_accuracy()