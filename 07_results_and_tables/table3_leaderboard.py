import os
import json
import pandas as pd
import glob
import numpy as np

# ================= 配置区域 =================
DATA_DIR = r'./external/metrics/0_final/final数据（指标2，3）/final'
OUTPUT_DIR = 'analysis_result'
# 输出文件名
TABLE_OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'final_formatted_leaderboard.csv')

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


# ================= 数据处理逻辑 =================

def get_top_3_detailed_data(df_subset):
    """
    输入：DataFrame子集
    输出：包含 Top 3 Coherence 和 Correctness 数据的字典
    """
    res = {
        'Coherence': [{'name': '', 'score': np.nan}] * 3,
        'Correctness': [{'name': '', 'score': np.nan}] * 3
    }

    if df_subset.empty:
        return res

    # 1. 计算 Coherence (Coherence > -1 且非空)
    coh_df = df_subset[(df_subset['coherence'].notna()) & (df_subset['coherence'] != -1)].copy()
    coh_df['coherence'] = pd.to_numeric(coh_df['coherence'])
    if not coh_df.empty:
        model_coh = coh_df.groupby('Model_Name')['coherence'].mean()
        top3_coh = model_coh.sort_values(ascending=False).head(3)
        for i, (name, score) in enumerate(top3_coh.items()):
            res['Coherence'][i] = {'name': name, 'score': score}

    # 2. 计算 Correctness (计算准确率)
    corr_df = df_subset.copy()
    corr_df['correctness'] = pd.to_numeric(corr_df['correctness'], errors='coerce')
    if not corr_df.empty:
        model_corr = corr_df.groupby('Model_Name')['correctness'].apply(
            lambda x: len(x[x == 1]) / len(x) if len(x) > 0 else 0
        )
        top3_corr = model_corr.sort_values(ascending=False).head(3)
        for i, (name, score) in enumerate(top3_corr.items()):
            res['Correctness'][i] = {'name': name, 'score': score}

    return res


# ================= 主执行流程 =================

print(f"正在扫描目录: {DATA_DIR}")
jsonl_files = glob.glob(os.path.join(DATA_DIR, '*.jsonl'))

if not jsonl_files:
    print("错误：目录下未找到任何 .jsonl 文件。")
    exit()

all_data_frames = []

# 1. 读取数据并映射名称
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
            all_data_frames.append(df)
            # print(f"已加载: {file_name_clean} -> {display_name}") # 减少日志输出

    except Exception as e:
        print(f"读取失败 {file_name_clean}: {e}")

if not all_data_frames:
    print("无有效数据。")
    exit()

big_df = pd.concat(all_data_frames, ignore_index=True)

# ================= 构建表头与排序 =================
print("\n正在构建表格结构...")

# --- 1. 处理列顺序 (Columns: Scenarios) ---
# 获取数据中所有存在的 scenario
unique_scenarios = list(set([s for s in big_df['scenario'].unique() if pd.notna(s)]))

# 定义目标排序列表 (核心要求 2)
target_order = ['STEM', 'Humanity', 'Social Science', 'Other']

# 排序逻辑：
# 1. 先把 target_order 里有的挑出来，按 target_order 顺序排
ordered_scenarios = [s for s in target_order if s in unique_scenarios]
# 2. 把剩下的（不在 target_order 里的）按字母序排在后面
remaining_scenarios = sorted([s for s in unique_scenarios if s not in target_order])
# 3. 最后加上总计
final_scenarios = ordered_scenarios + remaining_scenarios + ['ALL_SCENARIOS']

print(f"列顺序已调整为: {final_scenarios}")

# 构建列索引: Scenario -> Detail (Model Name/Score)
col_tuples = []
for sc in final_scenarios:
    col_tuples.append((sc, 'Model Name'))
    col_tuples.append((sc, 'Score'))
col_index = pd.MultiIndex.from_tuples(col_tuples, names=['Scenario', 'Detail'])

# --- 2. 处理行结构 (Rows: Task -> Metric -> Rank) ---
tasks = sorted([t for t in big_df['task'].unique() if pd.notna(t)], key=str)
tasks.append('ALL_TASKS')

row_tuples = []
metrics = ['Coherence', 'Correctness']
ranks = [1, 2, 3]

# 构建类似于图 3 的行结构
for task in tasks:
    for metric in metrics:
        for rank in ranks:
            # Row Index: (Task名, 指标名, 排名)
            row_tuples.append((task, metric, rank))

row_index = pd.MultiIndex.from_tuples(row_tuples, names=['Task', 'Metric', 'Rank'])

# ================= 填充数据 =================
print("正在填充数据...")
result_df = pd.DataFrame(index=row_index, columns=col_index)

for task in tasks:
    for scenario in final_scenarios:

        # 筛选数据
        temp_df = big_df.copy()
        if task != 'ALL_TASKS':
            temp_df = temp_df[temp_df['task'] == task]
        if scenario != 'ALL_SCENARIOS':
            temp_df = temp_df[temp_df['scenario'] == scenario]

        # 获取 Top 3 数据
        data = get_top_3_detailed_data(temp_df)

        # 填入表格
        # 我们的行索引现在是 (Task, Metric, Rank)
        for i, rank in enumerate(ranks):  # i=0->rank1, i=1->rank2...

            # --- 填入 Coherence ---
            coh_item = data['Coherence'][i]
            # 定位: Row=(Task, 'Coherence', rank), Col=(Scenario, 'Model Name'/'Score')
            result_df.at[(task, 'Coherence', rank), (scenario, 'Model Name')] = coh_item['name']
            result_df.at[(task, 'Coherence', rank), (scenario, 'Score')] = coh_item['score']

            # --- 填入 Correctness ---
            corr_item = data['Correctness'][i]
            # 定位: Row=(Task, 'Correctness', rank), Col=(Scenario, 'Model Name'/'Score')
            result_df.at[(task, 'Correctness', rank), (scenario, 'Model Name')] = corr_item['name']
            result_df.at[(task, 'Correctness', rank), (scenario, 'Score')] = corr_item['score']

# ================= 导出 =================
print("\n正在导出...")
# 使用 utf-8-sig 以兼容 Excel 中文显示
result_df.to_csv(TABLE_OUTPUT_FILE, encoding='utf_8_sig', float_format='%.4f')

print("=" * 50)
print(f"表格生成完毕！")
print(f"输出文件: {TABLE_OUTPUT_FILE}")
print("建议使用 Excel 打开查看效果：")
print("1. Task 列和 Metric 列会自动根据层级显示（类似合并单元格）。")
print("2. 列顺序已强制调整为: STEM -> Humanity -> Social Science -> Other。")
print("=" * 50)