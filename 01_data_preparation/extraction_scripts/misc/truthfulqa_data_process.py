import pandas as pd
import json

data_dir = "./data/raw_sources/data_files/"
category = "Science"

# 1. 读取 CSV
df = pd.read_csv("TruthfulQA.csv")

# 2. 筛选 Category = Education
df_edu = df[df["Category"] == category]

# 3. 选取需要的字段
df_selected = df_edu[["Question", "Correct Answers", "Best Answer"]]

# 4. 转换成字典列表并写入 JSON
data = df_selected.to_dict(orient="records")

with open(data_dir + category + "/TruthfulQA.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("数据集已生成")
