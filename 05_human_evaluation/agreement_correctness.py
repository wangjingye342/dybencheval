import json
import os


def calculate_accuracy():
    # 1. 定义文件路径
    # 预测结果文件 (包含 eval_result)
    pred_file_path = '/main_work/计算指标/3/backup/response_processed/正确性120_seed_response_extracted_scored.jsonl_prompt_level3_response_scored.jsonl'
    # 标注结果文件 (包含 label)
    gold_file_path = 'D:/STUDY/2026-project1/project1/main_work/计算指标/3/annotation_results_pro.jsonl'

    # 定义输出错误案例的文件路径 (可选，方便查看)
    error_output_path = 'error_cases.jsonl'

    # 检查文件是否存在
    if not os.path.exists(pred_file_path) or not os.path.exists(gold_file_path):
        print("错误：找不到指定的文件路径，请检查路径是否正确。")
        return

    # 2. 加载标注数据 (Ground Truth) 到字典中
    gold_data = {}
    print(f"正在加载标注文件: {os.path.basename(gold_file_path)} ...")

    with open(gold_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                item = json.loads(line)
                gold_data[item['id']] = str(item.get('label', '')).strip()
            except json.JSONDecodeError:
                print(f"警告: 跳过标注文件中无法解析的行")

    print(f"标注数据加载完成，共 {len(gold_data)} 条。")

    # 3. 遍历预测文件并计算准确率
    total_matched = 0
    correct_count = 0
    missing_ids = 0

    # [新增] 用于存储错误信息的列表
    incorrect_details = []

    print(f"正在对比预测文件: {os.path.basename(pred_file_path)} ...")

    with open(pred_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                pred_item = json.loads(line)
                p_id = pred_item.get('id')
                p_eval = str(pred_item.get('eval_result', '')).strip()

                # 检查该 ID 是否存在于标注数据中
                if p_id in gold_data:
                    total_matched += 1
                    gold_label = gold_data[p_id]

                    # 对比逻辑
                    if p_eval == gold_label:
                        correct_count += 1
                    else:
                        # [新增] 如果不匹配，记录 ID 和详情
                        incorrect_details.append({
                            "id": p_id,
                            "pred": p_eval,
                            "gold": gold_label
                        })
                else:
                    missing_ids += 1

            except json.JSONDecodeError:
                print(f"警告: 跳过预测文件中无法解析的行")

    # 4. 输出结果
    print("-" * 50)
    print("计算结果统计:")
    print("-" * 50)

    if total_matched == 0:
        print("未找到任何 ID 匹配的数据，无法计算准确率。")
    else:
        accuracy = (correct_count / total_matched) * 100
        print(f"有效对比样本数 (Total Matched): {total_matched}")
        print(f"预测正确样本数 (Correct): {correct_count}")
        print(f"预测错误样本数 (Incorrect): {len(incorrect_details)}")
        print(f"缺失标注 ID 数 (Missing IDs): {missing_ids}")
        print("-" * 50)
        print(f"** 准确率 (Accuracy): {accuracy:.2f}% **")
        print("-" * 50)

        # [新增] 输出错误 ID 列表
        if incorrect_details:
            print(f"\n发现 {len(incorrect_details)} 个错误 ID (格式: ID | 预测 vs 标注):")
            print("-" * 50)

            # 打印到控制台
            for item in incorrect_details:
                print(f"ID: {item['id']} | Pred: {item['pred']} | Gold: {item['gold']}")

            # [可选] 将错误案例保存到文件，方便后续分析
            with open(error_output_path, 'w', encoding='utf-8') as f_err:
                for item in incorrect_details:
                    f_err.write(json.dumps(item, ensure_ascii=False) + '\n')
            print("-" * 50)
            print(f"错误详情已同时保存至文件: {error_output_path}")
        else:
            print("恭喜！所有匹配样本预测均正确。")


if __name__ == "__main__":
    calculate_accuracy()