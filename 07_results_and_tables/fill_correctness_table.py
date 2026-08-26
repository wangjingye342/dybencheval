import pandas as pd

# 读取文件
# 注意：domain表通常有复杂的表头，这里不作为header读取，以便保留原始结构
metrics_df = pd.read_csv('metrics_report_per_file.csv')
domain_df = pd.read_csv('domain表p1.csv', header=None)

# 1. 建立模型名称映射 (Domain表名称 -> Metrics文件名称)
# 注意：Domain表中的名称可能包含空格，代码中会进行去除空格处理
model_map = {
    'GPT-5.2-thinking': 'gpt-5_2_all.jsonl',
    'Gemini-3-pro-preview': 'gemini3pro_all.jsonl',
    'Claude-opus-4-5-20251101-thinking': 'claude_all.jsonl',
    'GLM-4.6': 'GLM-4_6_all.jsonl',
    'Qwen-Max': 'qwen3-max_all.jsonl',
    'DeepSeek-v3.2': 'deepseek_all.jsonl',
    'Qwen3-235b-a22b-instruct-2507': 'qwen3-235b_all.jsonl',
    'Qwen3-30b-a3b-instruct-2507': 'qwen3-30b_all.jsonl',
    'Qwen3-8b': 'qwen3-8b_all.jsonl',
    'Llama-3.1-70b-instruct': 'llama-31-70b_all.jsonl',
    'Llama-3.1-8b-instruct': 'llama-31-8b_all.jsonl'
}

# 2. 定义列索引 (根据 domain表p1 的第0行结构)
# Header: domain, nan, nan, STEM, Humanity, Social Science, Other, All
# 对应的索引: 3, 4, 5, 6, 7
col_indices = {
    'STEM': 3,
    'Humanity': 4,
    'Social Science': 5,  # 对应metrics中的 Social_Science
    'Other': 6,
    'All': 7  # 对应metrics中的 Type='File_Total'
}

# 3. 遍历并填充数据
# 从第1行开始（跳过表头）
for index, row in domain_df.iloc[1:].iterrows():
    # 获取模型名称 (位于第2列)
    model_name_raw = row[2]

    if pd.isna(model_name_raw):
        continue

    # 去除首尾空格以匹配字典键值
    model_name = str(model_name_raw).strip()

    # 查找对应的源文件
    source_file = model_map.get(model_name)

    if source_file:
        # 在metrics表中筛选该文件的数据
        file_metrics = metrics_df[metrics_df['Source_File'] == source_file]

        if file_metrics.empty:
            continue


        # 定义内部函数：根据条件提取 Correctness_Prob
        def get_prob(condition):
            val = file_metrics[condition]['Correctness_Prob'].values
            return val[0] if len(val) > 0 else None


        # 填充各个维度
        # STEM
        val = get_prob(file_metrics['Name_English'] == 'STEM')
        if val is not None: domain_df.iat[index, col_indices['STEM']] = val

        # Humanity
        val = get_prob(file_metrics['Name_English'] == 'Humanity')
        if val is not None: domain_df.iat[index, col_indices['Humanity']] = val

        # Social Science (注意metrics中是 Social_Science)
        val = get_prob(file_metrics['Name_English'] == 'Social_Science')
        if val is not None: domain_df.iat[index, col_indices['Social Science']] = val

        # Other
        val = get_prob(file_metrics['Name_English'] == 'Other')
        if val is not None: domain_df.iat[index, col_indices['Other']] = val

        # All (对应 Type=File_Total)
        val = get_prob(file_metrics['Type'] == 'File_Total')
        if val is not None: domain_df.iat[index, col_indices['All']] = val

# 4. 保存结果
output_file = 'domain_filled_result.csv'
domain_df.to_csv(output_file, index=False, header=False)
print(f"处理完成，结果已保存至 {output_file}")