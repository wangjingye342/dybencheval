import os
import json
import glob
import openpyxl
from openpyxl.styles import Alignment

# ================= 配置区域 =================

# 1. JSON 结果目录
JSON_DIR = "./output"

# 2. Excel 模板路径
TEMPLATE_PATH = "domain表p1.xlsx"

# 3. 输出 Excel 路径
OUTPUT_PATH = "final_domain表p1.xlsx"

# ================= 模型名称映射字典 =================
MODEL_FILE_MAP = {
    "GPT-5.2-thinking": "gpt-5_2",
    "Gemini-3-pro-preview": "gemini3pro",
    "Claude-opus-4-5-20251101-thinking": "claude",
    "GLM-4.6": "GLM-4_6",
    "Qwen-Max": "qwen3-max",
    "DeepSeek-v3.2": "deepseek",
    "Qwen3-235b-a22b-instruct-2507": "qwen3-235b",
    "Qwen3-30b-a3b-instruct-2507": "qwen3-30b",
    "Qwen3-8b": "qwen3-8b",
    "Llama-3.1-70b-instruct": "llama-31-70b",
    "Llama-3.1-8b-instruct": "llama-31-8b"
}

# ================= 列映射配置 (修正了 Other) =================
# JSON scenario key (小写) -> Excel Column Index
# 为了保险，我们将 other 和 others 都指向第7列 (G列)
COLUMN_MAPPING = {
    "stem": 4,  # D列
    "humanity": 5,  # E列
    "social science": 6,  # F列
    "social sciences": 6,  # 容错
    "other": 7,  # G列 (修正点：匹配 Excel 表头 "Other")
    "others": 7,  # G列 (容错：防止 JSON 数据里写的是 "Others")
    "overall": 8  # H列 (All)
}


# ================= 工具函数 =================

def load_all_json_files(json_dir):
    loaded_files = []
    file_paths = glob.glob(os.path.join(json_dir, "*.json"))
    print(f"正在加载 {len(file_paths)} 个 JSON 文件...")
    for path in file_paths:
        try:
            filename = os.path.basename(path)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                loaded_files.append({'filename': filename, 'data': data})
        except Exception as e:
            print(f"Error reading {path}: {e}")
    return loaded_files


def find_data_for_model(excel_model_name, loaded_files):
    keyword = MODEL_FILE_MAP.get(excel_model_name.strip())
    if not keyword:
        return None
    for file_obj in loaded_files:
        if keyword in file_obj['filename']:
            return file_obj['data']
    return None


def fill_report(template_path, output_path, loaded_files):
    if not os.path.exists(template_path):
        print(f"错误: 找不到模板 {template_path}")
        return

    wb = openpyxl.load_workbook(template_path)
    ws = wb.active

    print("开始填写数据...")
    print("规则: Internal -> distinct2, External -> avg_bleu4")
    print(f"列映射修正: Other/Others -> 第7列")

    current_category = None
    current_subcategory = None

    for row in ws.iter_rows(min_row=2):
        cell_a = row[0]
        cell_b = row[1]
        cell_c = row[2]

        # 1. 识别区域
        if cell_a.value:
            current_category = str(cell_a.value).strip()

        if cell_b.value:
            current_subcategory = str(cell_b.value).strip()
        elif cell_a.value and not cell_b.value:
            current_subcategory = None

            # 2. 匹配模型
        if not cell_c.value:
            continue

        matched_data = find_data_for_model(str(cell_c.value), loaded_files)
        if not matched_data:
            continue

        # 3. 确定指标
        metric_key = None
        if current_category == "Diversity":
            if current_subcategory == "Internal":
                metric_key = "distinct2"
            elif current_subcategory == "External":
                metric_key = "avg_bleu4"
        elif current_category == "Coherence":
            metric_key = "avg_bleu4"
        else:
            continue

        # 4. 写入数据
        metrics_scenario = matched_data['metrics']['by_scenario']
        metrics_overall = matched_data['metrics']['overall']

        for scenario_key, col_idx in COLUMN_MAPPING.items():
            val = None
            if scenario_key == "overall":
                val = metrics_overall.get(metric_key)
            else:
                # 遍历 JSON 数据寻找匹配的 scenario
                for k, v in metrics_scenario.items():
                    if k.lower() == scenario_key:
                        val = v.get(metric_key)
                        break

            if val is not None:
                cell = row[col_idx - 1]
                cell.value = val
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.number_format = '0.0000'

    wb.save(output_path)
    print(f"写入完成! 文件已保存至: {output_path}")


if __name__ == "__main__":
    all_files = load_all_json_files(JSON_DIR)
    if all_files:
        fill_report(TEMPLATE_PATH, OUTPUT_PATH, all_files)