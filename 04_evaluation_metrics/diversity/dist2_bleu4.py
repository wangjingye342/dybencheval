import os
import json
import glob
import csv
from collections import defaultdict
import jieba
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from tqdm import tqdm

# ================= 配置区域 =================
# 输入目录路径
INPUT_DIR = "./external/metrics/0_final/final数据（指标2，3）/final"
# 输出目录路径
OUTPUT_DIR = "./output"
# 输出的 CSV 文件名
CSV_FILENAME = "all_metrics_summary.csv"

# 确保输出目录存在
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# NLTK BLEU 平滑函数
cc = SmoothingFunction()
smooth_fn = cc.method1


# ================= 工具函数 =================

def tokenize(text):
    """
    分词函数。
    """
    # 这里默认使用 jieba 精确模式，适用于中文
    # return list(jieba.cut(text))
    # 如果是纯英文，注释上面一行，使用下面一行：
    return text.strip().split()


def calculate_bleu4(seed_text, response_text):
    """
    计算单对文本的 BLEU-4 分数
    """
    ref_tokens = tokenize(seed_text)
    hyp_tokens = tokenize(response_text)

    try:
        score = sentence_bleu([ref_tokens], hyp_tokens, weights=(0.25, 0.25, 0.25, 0.25), smoothing_function=smooth_fn)
        return score
    except Exception:
        return 0.0


def calculate_distinct2(response_list):
    """
    计算一组回复的 Distinct-2 (Bigram) 值
    """
    if not response_list:
        return 0.0

    bigrams = []
    for text in response_list:
        tokens = tokenize(text)
        if len(tokens) < 2:
            continue
        # 生成 bigrams
        for i in range(len(tokens) - 1):
            bigrams.append((tokens[i], tokens[i + 1]))

    if len(bigrams) == 0:
        return 0.0

    unique_bigrams = set(bigrams)
    return len(unique_bigrams) / len(bigrams)


def compute_group_metrics(pairs_list):
    """
    通用函数：计算一组数据的指标 (BLEU4 Avg, Distinct-2, Count)
    """
    if not pairs_list:
        return {'avg_bleu4': 0.0, 'distinct2': 0.0, 'count': 0}

    # 计算 BLEU-4 (逐条计算后取平均)
    bleu_scores = [calculate_bleu4(s, r) for s, r in pairs_list]
    avg_bleu = sum(bleu_scores) / len(bleu_scores)

    # 计算 Distinct-2 (基于该组所有 response_text)
    all_responses = [r for s, r in pairs_list]
    dist2 = calculate_distinct2(all_responses)

    return {
        'avg_bleu4': round(avg_bleu, 6),
        'distinct2': round(dist2, 6),
        'count': len(pairs_list)
    }


def parse_file_data(file_path):
    """
    读取并解析单个文件，返回分类好的数据列表
    """
    file_name = os.path.basename(file_path)

    # 数据容器
    data_groups = {
        'overall': [],
        'scenario': defaultdict(list),
        'task': defaultdict(list)
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                item = json.loads(line)
                seed = item.get('seed_text', '')
                resp = item.get('response_text', '')
                scenario = item.get('scenario', 'unknown')
                task = item.get('task', 'unknown')

                pair = (seed, resp)

                data_groups['overall'].append(pair)
                data_groups['scenario'][scenario].append(pair)
                data_groups['task'][task].append(pair)

            except json.JSONDecodeError:
                print(f"Warning: {file_name} 中存在无法解析的行")
                continue

    return file_name, data_groups


# ================= 主程序 =================
def main():
    jsonl_files = glob.glob(os.path.join(INPUT_DIR, "*.jsonl"))

    if not jsonl_files:
        print(f"在目录 {INPUT_DIR} 下未找到 .jsonl 文件。")
        return

    print(f"共找到 {len(jsonl_files)} 个数据集文件。开始计算...")

    # 用于 CSV 存储的行列表
    csv_rows = []
    # CSV 表头
    header = ['Filename', 'Metric_Level', 'Category_Name', 'Count', 'Avg_BLEU4', 'Distinct2']

    # 用于计算全局平均（所有文件的总和）
    global_all_pairs = []

    for file_path in tqdm(jsonl_files):
        try:
            # 1. 解析文件数据
            file_name, data_groups = parse_file_data(file_path)

            # 2. 将该文件的数据加入全局池
            global_all_pairs.extend(data_groups['overall'])

            # 3. 计算该文件的 Overall 指标
            overall_res = compute_group_metrics(data_groups['overall'])
            csv_rows.append([file_name, 'File_Overall', 'All', overall_res['count'], overall_res['avg_bleu4'],
                             overall_res['distinct2']])

            # 4. 计算该文件的 Scenario 指标
            for sc, pairs in data_groups['scenario'].items():
                res = compute_group_metrics(pairs)
                csv_rows.append([file_name, 'Scenario', sc, res['count'], res['avg_bleu4'], res['distinct2']])

            # 5. 计算该文件的 Task 指标
            for tk, pairs in data_groups['task'].items():
                res = compute_group_metrics(pairs)
                csv_rows.append([file_name, 'Task', tk, res['count'], res['avg_bleu4'], res['distinct2']])

        except Exception as e:
            print(f"处理文件 {file_path} 时发生错误: {str(e)}")

    print("正在计算所有数据的全局平均指标 (Global Average)...")

    # 6. 计算所有数据的全局平均值
    # 注意：Distinct-2 是基于整个语料库计算的，因此这里是把所有文件的文本合在一起算，比简单的对平均值求平均更准确
    global_res = compute_group_metrics(global_all_pairs)

    # 添加一个空行或分隔符行方便阅读（可选）
    csv_rows.append([])
    # 添加全局汇总行
    csv_rows.append(
        ['TOTAL_SUMMARY', 'Global_Overall', 'All_Files_Combined', global_res['count'], global_res['avg_bleu4'],
         global_res['distinct2']])

    # 7. 写入 CSV 文件
    output_csv_path = os.path.join(OUTPUT_DIR, CSV_FILENAME)
    try:
        # 使用 utf-8-sig 编码，这样 Excel 打开中文不会乱码
        with open(output_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(csv_rows)

        print(f"\n========================================")
        print(f"计算完成！")
        print(f"所有文件的详细指标及全局平均值已保存至 CSV:")
        print(f"路径: {output_csv_path}")
        print(f"========================================")

    except Exception as e:
        print(f"保存 CSV 文件失败: {str(e)}")


if __name__ == "__main__":
    main()