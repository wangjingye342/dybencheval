import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import re

# ================= 配置区域 =================
DATA_DIR = r'./external/metrics/0_final/final数据（指标2，3）/final'
OUTPUT_DIR = 'analysis_result'
PLOT_ROOT = os.path.join(OUTPUT_DIR, 'plots')

# 确保输出总目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 设置通用英文字体，避免方块乱码
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
sns.set_style("whitegrid")

# --- 任务名中英文映射字典 ---
TASK_TRANSLATION = {
    "1_基本NLP任务": "1_Basic_NLP_Tasks",
    "2_开放问答": "2_Open_QA",
    "3_写作能力": "3_Writing_Ability",
    "4_推理能力": "4_Reasoning_Ability",
    "5_角色扮演": "5_Role_Playing",
    "6_专业知识": "6_Domain_Knowledge",
    "7_代码生成": "7_Code_Generation"
}


# ================= 辅助函数 =================

def get_english_name(raw_name, group_type):
    """获取对应的英文名称，优先查字典，否则正则去中文"""
    raw_str = str(raw_name)
    if group_type == 'Task' and raw_str in TASK_TRANSLATION:
        return TASK_TRANSLATION[raw_str]

    # 正则移除非ASCII字符
    safe_text = re.sub(r'[^\x00-\x7F]+', '', raw_str)
    safe_text = re.sub(r'\W+', '_', safe_text).strip('_')

    if not safe_text:
        safe_text = f"Unknown_{group_type}"
    return safe_text


def analyze_and_plot(sub_df, group_type, group_name, file_name, current_plot_dir):
    """
    核心处理函数：metrics并画图
    :param sub_df: 数据子集
    :param group_type: 类型 (File_Total / Scenario / Task)
    :param group_name: 具体名称
    :param file_name: 当前处理的文件名（用于记录）
    :param current_plot_dir: 当前文件的图片保存目录
    """
    # 获取英文显示名
    if group_type == 'File_Total':
        display_name = "Total_Score_Distribution"
    else:
        display_name = get_english_name(group_name, group_type)

    # --- 1. 计算 Coherence (并绘图) ---
    # 筛选有效数据：非空 且 不等于 -1
    valid_coherence_df = sub_df[
        (sub_df['coherence'].notna()) &
        (sub_df['coherence'] != -1)
        ].copy()

    # 确保转为整数
    valid_coherence_df['coherence'] = valid_coherence_df['coherence'].astype(int)

    avg_coherence = None
    if len(valid_coherence_df) > 0:
        avg_coherence = valid_coherence_df['coherence'].mean()

        # 绘图
        plt.figure(figsize=(8, 5))
        try:
            sns.countplot(
                data=valid_coherence_df,
                x='coherence',
                hue='coherence',
                legend=False,
                order=list(range(1, 11)),
                palette='viridis'
            )

            plt.title(f'{display_name} ({group_type})\nSource: {file_name}')
            plt.xlabel('Score (1-10)')
            plt.ylabel('Count')

            # 保存图片到对应文件夹
            save_name = f"{group_type}_{display_name}.png"
            save_path = os.path.join(current_plot_dir, save_name)
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
        except Exception as e:
            print(f"  [绘图警告] {file_name} - {display_name}: {e}")
            plt.close()

    # --- 2. 计算 Correctness ---
    correctness_prob = 0
    if len(sub_df) > 0:
        corr_series = pd.to_numeric(sub_df['correctness'], errors='coerce')
        correctness_prob = len(corr_series[corr_series == 1]) / len(sub_df)

    # 返回统计结果字典
    return {
        'Source_File': file_name,
        'Type': group_type,
        'Name_Original': str(group_name),
        'Name_English': display_name,
        'Total_Count': len(sub_df),
        'Valid_Coherence_Count': len(valid_coherence_df),
        'Avg_Coherence': avg_coherence,
        'Correctness_Prob': correctness_prob
    }


# ================= 主执行逻辑 =================

print(f"正在扫描目录: {DATA_DIR}")
jsonl_files = glob.glob(os.path.join(DATA_DIR, '*.jsonl'))

if not jsonl_files:
    print("错误：目录下未找到任何 .jsonl 文件。")
    exit()

all_results_list = []

for file_path in jsonl_files:
    # 获取文件名（不带路径）和文件名（不带扩展名，用于创建文件夹）
    file_name_full = os.path.basename(file_path)
    file_name_clean = os.path.splitext(file_name_full)[0]

    print(f"\n正在处理文件: {file_name_full}")

    # 1. 读取单文件数据
    current_data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    current_data.append(json.loads(line))
    except Exception as e:
        print(f"  读取失败，跳过: {e}")
        continue

    if not current_data:
        print("  文件为空，跳过。")
        continue

    df = pd.DataFrame(current_data)

    # 2. 数据清洗 (关键修复：转数字)
    df['coherence'] = pd.to_numeric(df['coherence'], errors='coerce')

    # 3. 创建该文件的专属图片目录
    # 结构: analysis_result/plots/dataset_name/
    current_plot_dir = os.path.join(PLOT_ROOT, file_name_clean)
    os.makedirs(current_plot_dir, exist_ok=True)

    # --- 维度 1: 该文件整体情况 ---
    res = analyze_and_plot(df, 'File_Total', 'All_Data', file_name_full, current_plot_dir)
    all_results_list.append(res)

    # --- 维度 2: 按 Scenario ---
    if 'scenario' in df.columns:
        scenarios = df['scenario'].unique()
        for sc in scenarios:
            sub_df = df[df['scenario'] == sc]
            res = analyze_and_plot(sub_df, 'Scenario', sc, file_name_full, current_plot_dir)
            all_results_list.append(res)

    # --- 维度 3: 按 Task ---
    if 'task' in df.columns:
        tasks = df['task'].unique()
        for t in tasks:
            sub_df = df[df['task'] == t]
            res = analyze_and_plot(sub_df, 'Task', t, file_name_full, current_plot_dir)
            all_results_list.append(res)

# ================= 保存最终总表 =================
if all_results_list:
    result_df = pd.DataFrame(all_results_list)

    # 调整列顺序，让文件名排在最前
    cols = ['Source_File', 'Type', 'Name_Original', 'Name_English', 'Total_Count', 'Valid_Coherence_Count',
            'Avg_Coherence', 'Correctness_Prob']
    result_df = result_df[cols]

    output_csv_path = os.path.join(OUTPUT_DIR, 'metrics_report_per_file.csv')
    result_df.to_csv(output_csv_path, index=False, float_format='%.4f')

    print("\n" + "=" * 40)
    print("全部处理完成！")
    print(f"1. 统计总表已保存至: {output_csv_path}")
    print(f"2. 图片已按文件名分类保存至: {PLOT_ROOT}/<文件名>/")
    print("=" * 40)
else:
    print("未生成任何有效结果。")