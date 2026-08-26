import os
import json
import pandas as pd
import glob
import numpy as np

# ================= 配置区域 =================
DATA_DIR = r'./external/metrics/0_final/final数据（指标2，3）/final'
OUTPUT_DIR = 'analysis_result_ranks'  # 修改输出目录以免覆盖旧文件
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- 模型名称映射字典 ---
MODEL_NAME_MAPPING = {
    "gpt-5_2_all": "GPT-5.2-thinking",
    "gemini3pro_all": "Gemini-3-pro-preview",
    "claude_all": "Claude-opus-4-5-20251101-thinking",
    "GLM-4_6_all": "GLM-4.6",
    "qwen3-max_all": "Qwen-Max",
    "deepseek_all": "DeepSeek-v3.2",
    "qwen3-235b_all": "Qwen3-235b-a22b-instruct-2507",
    "qwen3-30b_all": "Qwen3-30b-a3b-instruct-2507",
    "qwen3-8b_all": "Qwen3-8b",
    "llama-31-70b_all": "Llama-3.1-70b-instruct",
    "llama-31-8b_all": "Llama-3.1-8b-instruct"
}


def get_display_name(filename_clean):
    return MODEL_NAME_MAPPING.get(filename_clean, filename_clean)


# ================= 数据读取逻辑 (复用原代码) =================

print(f"正在扫描目录: {DATA_DIR}")
jsonl_files = glob.glob(os.path.join(DATA_DIR, '*.jsonl'))

if not jsonl_files:
    print("错误：目录下未找到任何 .jsonl 文件。")
    exit()

all_data_frames = []

for file_path in jsonl_files:
    file_name_full = os.path.basename(file_path)
    file_name_clean = os.path.splitext(file_name_full)[0]
    display_name = get_display_name(file_name_clean)

    try:
        current_data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    current_data.append(json.loads(line))

        if current_data:
            df = pd.DataFrame(current_data)
            df['Model_Name'] = display_name
            # 预处理数据类型
            df['coherence'] = pd.to_numeric(df['coherence'], errors='coerce')
            df['correctness'] = pd.to_numeric(df['correctness'], errors='coerce')
            all_data_frames.append(df)
    except Exception as e:
        print(f"读取失败 {file_name_clean}: {e}")

if not all_data_frames:
    print("无有效数据。")
    exit()

big_df = pd.concat(all_data_frames, ignore_index=True)

# ================= 核心计算逻辑 =================
print("\n正在计算排名...")

# 1. 准备 Scenario 和 Task 的列表（包含 'ALL'）
unique_scenarios = list(big_df['scenario'].dropna().unique())
unique_tasks = list(big_df['task'].dropna().unique())

# 定义想要遍历的所有组合 (Scenario, Task)
# 我们需要覆盖四种情况:
# 1. 具体 Scenario, 具体 Task
# 2. 具体 Scenario, ALL Tasks
# 3. ALL Scenarios, 具体 Task
# 4. ALL Scenarios, ALL Tasks

# 制作组合列表
combinations = []
# (Scenario值, Task值, 过滤条件标签)
for s in unique_scenarios:
    for t in unique_tasks:
        combinations.append((s, t))
    combinations.append((s, 'ALL_TASKS'))

for t in unique_tasks:
    combinations.append(('ALL_SCENARIOS', t))

combinations.append(('ALL_SCENARIOS', 'ALL_TASKS'))

# 2. 计算每个组合下的得分并排名
rank_records = []

for scenario, task in combinations:
    # 筛选数据
    temp_df = big_df.copy()
    if scenario != 'ALL_SCENARIOS':
        temp_df = temp_df[temp_df['scenario'] == scenario]
    if task != 'ALL_TASKS':
        temp_df = temp_df[temp_df['task'] == task]

    if temp_df.empty:
        continue

    # --- 计算该组合下每个模型的得分 ---

    # Coherence: 过滤掉 -1 和空值求均值
    coh_df = temp_df[(temp_df['coherence'].notna()) & (temp_df['coherence'] != -1)]
    if not coh_df.empty:
        coh_scores = coh_df.groupby('Model_Name')['coherence'].mean()
    else:
        coh_scores = pd.Series(dtype=float)

    # Correctness: 准确率 (1的数量 / 总数量)
    corr_df = temp_df[temp_df['correctness'].notna()]
    if not corr_df.empty:
        corr_scores = corr_df.groupby('Model_Name')['correctness'].apply(
            lambda x: (x == 1).sum() / len(x) if len(x) > 0 else 0
        )
    else:
        corr_scores = pd.Series(dtype=float)

    # --- 计算排名 (数值越大排名越靠前) ---
    # method='min': 并列第1，下一个是第3
    coh_ranks = coh_scores.rank(ascending=False, method='min')
    corr_ranks = corr_scores.rank(ascending=False, method='min')

    # 将结果存入列表
    # 找出涉及的所有模型
    all_models_in_batch = set(coh_scores.index) | set(corr_scores.index)

    for model in all_models_in_batch:
        c_rank = coh_ranks.get(model, np.nan)
        acc_rank = corr_ranks.get(model, np.nan)

        # 格式化单元格内容: "Coh:#1, Corr:#2"
        # 如果是整数排名，转为int显示，否则显示nan
        c_str = str(int(c_rank)) if pd.notna(c_rank) else "-"
        a_str = str(int(acc_rank)) if pd.notna(acc_rank) else "-"

        cell_value = f"Coh: #{c_str}\nCorr: #{a_str}"

        rank_records.append({
            'Model_Name': model,
            'Scenario': scenario,
            'Task': task,
            'Display_Value': cell_value,
            # 保留原始排名以便排序或调试
            'Coh_Rank': c_rank,
            'Corr_Rank': acc_rank
        })

rank_df = pd.DataFrame(rank_records)

# ================= 输出文件生成 =================
print("\n正在生成每个模型的表格...")

# 定义行和列的排序顺序
# Scenario 排序 (保留你之前的逻辑: STEM -> Humanity -> Social -> Other -> ALL)
target_scenario_order = ['STEM', 'Humanity', 'Social Science', 'Other']
remaining_scenarios = sorted([s for s in unique_scenarios if s not in target_scenario_order])
final_scenario_order = target_scenario_order + remaining_scenarios + ['ALL_SCENARIOS']

# Task 排序 (字母序 + ALL)
final_task_order = sorted([t for t in unique_tasks], key=str) + ['ALL_TASKS']

# 获取所有模型列表
all_models = rank_df['Model_Name'].unique()

for model_name in all_models:
    # 1. 筛选当前模型数据
    model_data = rank_df[rank_df['Model_Name'] == model_name]

    if model_data.empty:
        continue

    # 2. 创建透视表 (行=Scenario, 列=Task)
    pivot_table = model_data.pivot(index='Scenario', columns='Task', values='Display_Value')

    # 3. 重新索引以保证顺序和完整性 (缺失值填 "-")
    pivot_table = pivot_table.reindex(index=final_scenario_order, columns=final_task_order, fill_value="-")

    # 4. 导出 CSV
    # 清理文件名中的非法字符
    safe_model_name = "".join([c for c in model_name if c.isalnum() or c in (' ', '-', '_')]).strip()
    filename = f"RankTable_{safe_model_name}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    pivot_table.to_csv(filepath, encoding='utf_8_sig')
    print(f"已生成: {filepath}")

print("=" * 50)
print(f"处理完成！所有文件已保存在: {OUTPUT_DIR}")
print("每个单元格格式为: 'Coh: #排名 [换行] Corr: #排名'")
print("=" * 50)