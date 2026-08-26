import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import re

# ================= 配置区域 =================
DATA_DIR = r'./external/metrics/0_final/final数据（指标2，3）/final'
OUTPUT_DIR = 'analysis_result_all'
PLOT_DIR = os.path.join(OUTPUT_DIR, 'plots')

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(PLOT_DIR, 'global'), exist_ok=True)
os.makedirs(os.path.join(PLOT_DIR, 'scenario'), exist_ok=True)
os.makedirs(os.path.join(PLOT_DIR, 'task'), exist_ok=True)

# 设置通用英文作为默认字体，彻底避免方块乱码
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans', 'Bitstream Vera Sans']
sns.set_style("whitegrid")

# --- 核心定义：任务名中英文映射字典 ---
TASK_TRANSLATION = {
    "1_基本NLP任务": "1_Basic_NLP_Tasks",
    "2_开放问答": "2_Open_QA",
    "3_写作能力": "3_Writing_Ability",
    "4_推理能力": "4_Reasoning_Ability",
    "5_角色扮演": "5_Role_Playing",
    "6_专业知识": "6_Domain_Knowledge",
    "7_代码生成": "7_Code_Generation"
}

# ================= 1. 数据加载 =================
print(f"正在从目录读取数据: {DATA_DIR}")
jsonl_files = glob.glob(os.path.join(DATA_DIR, '*.jsonl'))

all_data = []
for file_path in jsonl_files:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    all_data.append(json.loads(line))
    except Exception as e:
        print(f"读取文件 {file_path} 出错: {e}")

if not all_data:
    print("错误：未找到任何数据。")
    exit()

df = pd.DataFrame(all_data)

# ----------------- 关键修复：数据清洗 -----------------
print("正在清洗数据类型...")
# 1. 强制将 coherence 转为数字，处理空图问题的关键！
df['coherence'] = pd.to_numeric(df['coherence'], errors='coerce')

# 2. 打印一下转换后的情况
print(f"有效Coherence数据量: {df['coherence'].notna().sum()}")
# ----------------------------------------------------

# ================= 2. 定义计算与绘图函数 =================

results_list = []


def get_english_name(raw_name, group_type):
    """
    获取对应的英文名称：
    1. 如果是 Task，优先查字典翻译。
    2. 如果字典里没有，或者不是 Task，使用正则去除中文，防止乱码。
    """
    raw_str = str(raw_name)

    # 优先匹配字典（针对 Task）
    if group_type == 'Task' and raw_str in TASK_TRANSLATION:
        return TASK_TRANSLATION[raw_str]

    # 如果字典匹配不到（或者是 Scenario），则使用正则暴力移除中文
    # 移除所有非ASCII字符
    safe_text = re.sub(r'[^\x00-\x7F]+', '', raw_str)
    # 将特殊符号替换为下划线
    safe_text = re.sub(r'\W+', '_', safe_text).strip('_')

    # 如果处理完是空的（例如纯中文名且不在字典里），给一个默认名
    if not safe_text:
        safe_text = f"Unknown_{group_type}"

    return safe_text


def process_and_plot(sub_df, group_type, group_name):
    # 获取用于显示的英文名
    display_name = get_english_name(group_name, group_type)

    # 筛选有效数据：非空 且 不等于 -1
    valid_coherence_df = sub_df[
        (sub_df['coherence'].notna()) &
        (sub_df['coherence'] != -1)
        ].copy()

    # 转换为整数以便绘图对齐 x 轴
    valid_coherence_df['coherence'] = valid_coherence_df['coherence'].astype(int)

    if len(valid_coherence_df) > 0:
        avg_coherence = valid_coherence_df['coherence'].mean()

        # --- 绘图 ---
        plt.figure(figsize=(8, 5))
        try:
            sns.countplot(
                data=valid_coherence_df,
                x='coherence',
                hue='coherence',
                legend=False,
                order=list(range(1, 11)),  # 固定 x 轴 1-10
                palette='viridis'
            )

            # 使用翻译后的 display_name 作为标题
            plt.title(f'{display_name} ({group_type})')
            plt.xlabel('Score (1-10)')
            plt.ylabel('Count')

            # 保存图片
            save_path = os.path.join(PLOT_DIR, group_type.lower(), f'{display_name}.png')
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
        except Exception as e:
            print(f"绘图出错 ({display_name}): {e}")
            plt.close()
    else:
        avg_coherence = None

    # 计算 Correctness
    if len(sub_df) > 0:
        corr_series = pd.to_numeric(sub_df['correctness'], errors='coerce')
        correctness_prob = len(corr_series[corr_series == 1]) / len(sub_df)
    else:
        correctness_prob = 0

    results_list.append({
        'Type': group_type,
        'Name_Original': str(group_name),  # 结果CSV保留原始中文名
        'Name_English': display_name,  # 结果CSV增加英文名列
        'Count': len(sub_df),
        'Valid_Coherence_Count': len(valid_coherence_df),
        'Avg_Coherence': avg_coherence,
        'Correctness_Prob': correctness_prob
    })


# ================= 3. 执行统计分析 =================

print("开始统计分析...")

# 1. Global
process_and_plot(df, 'Global', 'All_Data')

# 2. Scenario (自动移除中文防止乱码)
if 'scenario' in df.columns:
    scenarios = df['scenario'].unique()
    print(f"处理 Scenario ({len(scenarios)}种)...")
    for sc in scenarios:
        sub_df = df[df['scenario'] == sc]
        process_and_plot(sub_df, 'Scenario', sc)

# 3. Task (应用翻译字典)
if 'task' in df.columns:
    tasks = df['task'].unique()
    print(f"处理 Task ({len(tasks)}种)...")
    for t in tasks:
        sub_df = df[df['task'] == t]
        process_and_plot(sub_df, 'Task', t)

# ================= 4. 保存结果 =================
result_df = pd.DataFrame(results_list)
output_csv_path = os.path.join(OUTPUT_DIR, 'metrics_report.csv')
result_df.to_csv(output_csv_path, index=False, float_format='%.4f')

print("-" * 30)
print("处理完成！")
print(f"1. 报表已保存: {output_csv_path}")
print(f"2. 图片已保存至: {PLOT_DIR}/task/ (文件名已转为英文)")
print("-" * 30)