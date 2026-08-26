import streamlit as st
import json
import os
import re

# ================= 配置路径 =================
FILE_PATH_A = "sample1_all_final.jsonl"
FILE_PATH_B = "sample2_all_final.jsonl"
OUTPUT_FILE = "annotation_results.jsonl"

st.set_page_config(layout="wide", page_title="模型对比评估平台")


# ================= 辅助函数 =================

@st.cache_data
def load_data(path):
    """加载原始数据"""
    data = []
    if not os.path.exists(path):
        st.error(f"文件不存在: {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return data


def load_existing_results():
    """
    加载已有的标注结果到字典中。
    返回格式: {line_number_value: {完整记录字典}, ...}
    """
    results_map = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    if "line_number" in record:
                        results_map[record["line_number"]] = record
                except:
                    continue
    return results_map


def save_unique_result(line_number, label, model_a_name, model_b_name, current_map):
    """
    保存结果：更新内存字典，并重写文件
    注意：这里的 model_a_name 和 model_b_name 应该是真实模型名，用于存入文件
    """
    new_record = {
        "line_number": line_number,
        "label": label,
        "model_a": model_a_name, # 保存真实名称
        "model_b": model_b_name  # 保存真实名称
    }

    current_map[line_number] = new_record

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for record in current_map.values():
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return current_map


def extract_seed_json(prompt_text):
    """从Prompt中提取Input Seed Data"""
    try:
        pattern = r"# Input Seed Data\s*(.*?)\s*# Action"
        match = re.search(pattern, prompt_text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
        else:
            return {"raw_prompt": prompt_text}
    except:
        return {"error": "无法解析Seed Data"}


def parse_response_json(response_str):
    """解析模型输出"""
    try:
        cleaned_str = response_str.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_str)
    except Exception as e:
        return {"raw_response": response_str}


# ================= 主程序逻辑 =================

# 1. 加载数据
data_a = load_data(FILE_PATH_A)
data_b = load_data(FILE_PATH_B)

if not data_a or not data_b:
    st.stop()

# 加载历史记录
if 'annotation_map' not in st.session_state:
    st.session_state.annotation_map = load_existing_results()

total_items = min(len(data_a), len(data_b))

# 2. 索引控制
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

# 获取当前数据
item_a = data_a[st.session_state.current_index]
item_b = data_b[st.session_state.current_index]

# 提取关键信息
current_line_num = item_a.get("line_number")
if current_line_num is None:
    current_line_num = item_a.get("original_data", {}).get("line_index", st.session_state.current_index)

# ----------------- 修改点 1: 分离真实名称与显示名称 -----------------
# 获取真实模型名称（用于保存数据，不展示给用户）
real_model_name_a = item_a.get("model", "Unknown Model A")
real_model_name_b = item_b.get("model", "Unknown Model B")

# 设置界面显示名称（用于展示，实现盲测）
display_name_a = "Model A"
display_name_b = "Model B"
# ------------------------------------------------------------------

# ================= 侧边栏与导航 =================

st.sidebar.title("控制面板")
st.sidebar.info(f"已标注数量: {len(st.session_state.annotation_map)}")
st.sidebar.progress((st.session_state.current_index + 1) / total_items)

jump_index = st.sidebar.number_input(
    "跳转到列表索引",
    min_value=0,
    max_value=total_items - 1,
    value=st.session_state.current_index
)

if jump_index != st.session_state.current_index:
    st.session_state.current_index = jump_index
    st.rerun()

# 检查历史状态
previous_record = st.session_state.annotation_map.get(current_line_num)
previous_label = previous_record["label"] if previous_record else None
status_icon = "✅ 已标注" if previous_label else "⏳ 未标注"

# ================= 页面主体 =================

st.title(f"🔍 数据对比 - Line Number: {current_line_num}")
st.caption(f"索引: {st.session_state.current_index}/{total_items} | 状态: {status_icon}")

if previous_label:
    # ----------------- 修改点 2: 隐藏历史记录中的真实模型名 -----------------
    # 只显示之前选了谁，不显示当时记录的具体模型名，防止泄露
    st.info(f"已保存结果: **{previous_label}**")
    # ---------------------------------------------------------------------

st.divider()

# 三栏布局
col_seed, col_model_a, col_model_b = st.columns(3)

# 1. 原始种子
with col_seed:
    st.subheader("1. 原始种子")
    prompt_content = item_a["original_data"]["prompt"]
    seed_json = extract_seed_json(prompt_content)
    with st.container(border=True):
        st.json(seed_json, expanded=True)

# 2. 模型 A (使用 display_name_a)
with col_model_a:
    st.subheader(f"2. {display_name_a}")
    resp_a_json = parse_response_json(item_a["response"])
    with st.container(border=True):
        st.json(resp_a_json, expanded=True)

# 3. 模型 B (使用 display_name_b)
with col_model_b:
    st.subheader(f"3. {display_name_b}")
    resp_b_json = parse_response_json(item_b["response"])
    with st.container(border=True):
        st.json(resp_b_json, expanded=True)

st.divider()

# ================= 评估区域 =================

st.header("📝 质量评估")

with st.form(key=f'eval_form_{current_line_num}'):
    # ----------------- 修改点 3: 选项中使用通用名称 -----------------
    options = [f"中间模型更好 ({display_name_a})", f"右侧模型更好 ({display_name_b})", "平局 (Tie)"]
    # -------------------------------------------------------------

    # 默认选中逻辑
    default_index = 0
    if previous_label == "model_a":
        default_index = 0
    elif previous_label == "model_b":
        default_index = 1
    elif previous_label == "tie":
        default_index = 2

    choice = st.radio("您的判断：", options, index=default_index, horizontal=True)

    submit_btn = st.form_submit_button(label="💾 保存并下一题", type="primary")

    if submit_btn:
        if "中间" in choice:
            label = "model_a"
        elif "右侧" in choice:
            label = "model_b"
        else:
            label = "tie"

        # ----------------- 修改点 4: 保存时传入真实名称 -----------------
        # 即使界面看不到，我们还是把真实模型名存入 JSONL，方便后续分析
        st.session_state.annotation_map = save_unique_result(
            current_line_num,
            label,
            real_model_name_a,  # 传入真实名
            real_model_name_b,  # 传入真实名
            st.session_state.annotation_map
        )
        # -------------------------------------------------------------

        st.toast(f"✅ Line {current_line_num} 保存成功")

        # 自动翻页
        if st.session_state.current_index < total_items - 1:
            st.session_state.current_index += 1
            st.rerun()
        else:
            st.success("所有数据浏览完毕！")