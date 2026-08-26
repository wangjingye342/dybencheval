import os
import json
import pandas as pd
import tiktoken  # 必须先 pip install tiktoken

# =================配置区域=================
# 1. 设置根目录路径
ROOT_PATH = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/评估指标/计算size/final数据集/DyBenchEval"

# 2. 初始化 Tokenizer
# 使用 cl100k_base (GPT-4/ChatGPT 标准)
# 如果你需要计算 Llama 的 token，可以使用 transformers 的 AutoTokenizer
try:
    ENC = tiktoken.get_encoding("cl100k_base")
    print("成功加载 tiktoken (cl100k_base)")
except Exception as e:
    print("错误: 无法加载 tiktoken。请确保已安装: pip install tiktoken")
    exit()

# 3. 映射定义
DOMAIN_MAPPING = {
    "STEM": "STEM",
    "Humanity": "Humanity",
    "SocialScience": "Social Science",
    "Other": "Others"
}

TASK_MAPPING = {
    "1_基本NLP任务": "Fundamental Language Ability",
    "2_开放问答": "Open-Domain QA",
    "3_写作能力": "Writing Ability",
    "4_推理能力": "Reasoning Ability",
    "5_角色扮演": "Task-Oriented Role Play",
    "6_专业知识": "Professional Knowledge",
    "7_代码生成": "Code Generation"
}
# =========================================

final_results_map = {}

# 统计字典
stats_overall = {"Overall": {"count": 0, "q_len_sum": 0, "a_len_sum": 0}}
stats_domain = {}
stats_task = {}

def get_token_count(text):
    """使用 tiktoken 计算字符串的 token 数量"""
    try:
        # encode 普通模式，disallowed_special='all'防止特殊token报错
        return len(ENC.encode(text, disallowed_special=()))
    except Exception:
        return 0

def update_stats(stats_dict, key, q_len, a_len):
    if key not in stats_dict:
        stats_dict[key] = {"count": 0, "q_len_sum": 0, "a_len_sum": 0}
    stats_dict[key]["count"] += 1
    stats_dict[key]["q_len_sum"] += q_len
    stats_dict[key]["a_len_sum"] += a_len

print(f"开始处理目录: {ROOT_PATH} ...")

# 4. 遍历目录
for root, dirs, files in os.walk(ROOT_PATH):
    rel_path = os.path.relpath(root, ROOT_PATH)
    if rel_path == ".": continue

    path_parts = rel_path.split(os.sep)
    jsonl_files = [f for f in files if f.endswith('.jsonl')]

    if not jsonl_files: continue

    if len(path_parts) >= 2:
        raw_domain_folder = path_parts[0]
        raw_task_folder = path_parts[1]

        current_domain = DOMAIN_MAPPING.get(raw_domain_folder, raw_domain_folder)
        current_task = TASK_MAPPING.get(raw_task_folder, raw_task_folder)
    else:
        continue

    # 5. 读取文件并统计
    for file in jsonl_files:
        file_path = os.path.join(root, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        # 确保转换为字符串
                        q_text = str(data.get('question', ''))
                        a_text = str(data.get('answer', ''))

                        # === 修改点：计算 Token 长度 ===
                        q_len = get_token_count(q_text)
                        a_len = get_token_count(a_text)
                        # ============================

                        update_stats(stats_overall, "Overall", q_len, a_len)
                        update_stats(stats_domain, current_domain, q_len, a_len)
                        update_stats(stats_task, current_task, q_len, a_len)

                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"Error reading {file_path}: {e}")


# 6. 计算平均值
def process_to_map(stats_dict):
    for category, data in stats_dict.items():
        count = data["count"]
        if count == 0:
            avg_q, avg_a = 0, 0
        else:
            avg_q = data["q_len_sum"] / count
            avg_a = data["a_len_sum"] / count

        final_results_map[category] = {
            "Size": count,
            "Len-Q": avg_q,
            "Len-A": avg_a
        }

process_to_map(stats_overall)
process_to_map(stats_domain)
process_to_map(stats_task)

# ==========================================
# 7. 生成 LaTeX 代码
# ==========================================

def get_tex_line(category_name):
    if category_name in final_results_map:
        res = final_results_map[category_name]
        return f"{category_name} & {res['Size']} & {res['Len-Q']:.2f} & {res['Len-A']:.2f} \\\\"
    else:
        return f"{category_name} & 0 & 0.00 & 0.00 \\\\"

latex_template = f"""
\\begin{{table}}[!t]
    \\centering
    \\footnotesize
    \\setlength{{\\tabcolsep}}{{1.8mm}}{{
    \\begin{{tabular}}{{lccc}}
\\toprule
% \\textbf{{Category}} & \\textbf{{Nesting Depth}} & \\textbf{{\\#Inst.}} & \\textbf{{Len.}} & \\textbf{{\\#Ques.}} & \\textbf{{\\#Con.}} \\\\
Category & Size & Len-Q & Len-A \\\\
\\midrule
{get_tex_line("Overall")}
\\midrule
\\multicolumn{{4}}{{l}}{{\\textit{{Domain}}}} \\\\
{get_tex_line("STEM")}
{get_tex_line("Humanity")}
{get_tex_line("Social Science")}
{get_tex_line("Others")}
\\midrule
\\multicolumn{{4}}{{l}}{{\\textit{{Task}}}} \\\\
{get_tex_line("Fundamental Language Ability")}
{get_tex_line("Open-Domain QA")}
{get_tex_line("Writing Ability")}
{get_tex_line("Reasoning Ability")}
{get_tex_line("Task-Oriented Role Play")}
{get_tex_line("Professional Knowledge")}
{get_tex_line("Code Generation")}
\\bottomrule
\\end{{tabular}}}}
    \\caption{{Statistics of DyBenchEval including the dataset size (\\textbf{{Size}}) and the average tokens of questions (\\textbf{{Len-Q}}) / answers (\\textbf{{Len-A}}).}}
    \\label{{tab:stat}}
\\end{{table}}
"""

print("\n" + "=" * 20 + " LaTeX Output " + "=" * 20)
print(latex_template)
print("=" * 54 + "\n")

# ==========================================
# 8. 保存文件
# ==========================================

with open("table_stat.tex", "w", encoding="utf-8") as f:
    f.write(latex_template)

csv_rows = []
for cat, data in final_results_map.items():
    csv_rows.append(
        {"Category": cat, "Size": data["Size"], "Len-Q": f"{data['Len-Q']:.2f}", "Len-A": f"{data['Len-A']:.2f}"})
df = pd.DataFrame(csv_rows)

desired_order = ["Overall", "STEM", "Humanity", "Social Science", "Others"] + list(TASK_MAPPING.values())
df['sort_cat'] = pd.Categorical(df['Category'], categories=desired_order, ordered=True)
df = df.sort_values('sort_cat').drop('sort_cat', axis=1)

df.to_csv("dataset_stats.csv", index=False)
print("文件已保存: table_stat.tex 和 dataset_stats.csv")