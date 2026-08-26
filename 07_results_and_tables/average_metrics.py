import pandas as pd

# 读取CSV文件
file_path = 'metrics_report_per_file.csv'
df = pd.read_csv(file_path)

# 指定需要计算均值的 Name_Original 列表
target_names = [
    'STEM',
    'Other',
    'Social Science',
    'Humanity',
    '1_基本NLP任务',
    '2_开放问答',
    '6_专业知识',
    '4_推理能力',
    '7_代码生成',
    '5_角色扮演',
    '3_写作能力'
]

# 筛选出包含上述名称的行
filtered_df = df[df['Name_Original'].isin(target_names)]

# 按 Name_Original 分组并计算所有数值列的均值
# numeric_only=True 确保只对数字列进行平均计算
result = filtered_df.groupby('Name_Original').mean(numeric_only=True)

# 按照指定列表的顺序重新排列结果（可选，方便查看）
result = result.reindex(target_names)

# 打印结果
print(result)

# 保存结果到新的CSV文件
output_file = 'calculated_means.csv'
result.to_csv(output_file)
print(f"结果已保存至 {output_file}")