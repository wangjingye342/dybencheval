import streamlit as st
import json
import os
import re
import ast

# --- 页面配置 ---
st.set_page_config(page_title="数据正确性校验工具", layout="wide")

# --- 自定义 CSS ---
st.markdown(
    """
    <style>
    code { white-space: pre-wrap !important; word-break: break-word !important; }
    .stCodeBlock pre { white-space: pre-wrap !important; }
    .status-box {
        padding: 15px; border-radius: 8px; margin-bottom: 20px;
        font-size: 1.1em; font-weight: bold; text-align: center;
    }
    .status-correct { background-color: #d1e7dd; color: #0f5132; border: 1px solid #badbcc; }
    .status-wrong { background-color: #f8d7da; color: #842029; border: 1px solid #f5c2c7; }
    .status-none { background-color: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; }
    .id-display { font-size: 1.5em; font-weight: bold; color: #0d6efd; margin-bottom: 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📂 模型生成题目校验工具 (自动保存版)")

# --- 路径配置 ---
# 输入文件路径
INPUT_FILE_PATH = "./external/human_evaluation/correctness_120_final.jsonl"
# 输出保存路径 (结果将保存到这里)
OUTPUT_FILE_PATH = "annotation_results.jsonl"


# --- 核心工具函数 ---

def extract_json_substring(s):
    if not isinstance(s, str): return s
    s = s.strip()
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL | re.IGNORECASE)
    if match: return match.group(1)
    start = s.find('{')
    end = s.rfind('}')
    if start != -1 and end != -1 and end > start: return s[start:end + 1]
    return s


def safe_parse_json(content):
    if isinstance(content, (dict, list)): return content, True
    if not isinstance(content, str): return str(content), False
    cleaned = extract_json_substring(content)
    try:
        return json.loads(cleaned, strict=False), True
    except:
        pass
    try:
        return ast.literal_eval(cleaned), True
    except:
        pass
    try:
        cleaned_fix = cleaned.replace('\n', '\\n')
        return json.loads(cleaned_fix, strict=False), True
    except:
        pass
    try:
        cleaned_fix = cleaned.replace('\n', '\\n')
        return ast.literal_eval(cleaned_fix), True
    except:
        pass
    return content, False


def load_data(file_path):
    data_list = []
    if not os.path.exists(file_path):
        st.error(f"找不到输入文件: {file_path}")
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if line:
                try:
                    data_list.append(json.loads(line))
                except:
                    st.warning(f"无法解析第 {i + 1} 行")
    return data_list


# --- 保存与读取逻辑 (核心修改) ---

def load_saved_progress(output_path):
    """
    程序启动时加载已保存的进度，恢复到 session_state
    返回一个字典: { str(id): "正确"/"错误" } 用于UI显示
    """
    saved_status = {}
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        # 将保存的 1/0 转换为 UI 需要的状态字符串
                        r_id = str(record.get("id"))
                        label = record.get("label")
                        if label == 1:
                            saved_status[r_id] = "正确"
                        elif label == 0:
                            saved_status[r_id] = "错误"
                    except:
                        pass
    return saved_status


def save_record(item_data, label_value, output_path):
    """
    保存单条记录到文件 (覆盖旧记录)
    item_data: 原始数据对象
    label_value: 1 (正确) 或 0 (错误)
    """
    # 1. 读取现有所有记录到字典中 (key=id)
    existing_records = {}
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rec = json.loads(line)
                        existing_records[str(rec["id"])] = rec
                    except:
                        pass

    # 2. 构造当前这条的保存数据 (包含元数据)
    current_id = str(item_data.get("id", "unknown"))
    new_record = {
        "id": item_data.get("id"),
        "model": item_data.get("model"),
        # 如果需要更多元数据，可以在这里添加，例如:
        # "original_source": item_data.get("original_data", {}).get("source_file"),
        "label": label_value,  # 1 或 0
        "timestamp": str(os.path.getmtime(INPUT_FILE_PATH))  # 可选
    }

    # 3. 更新字典 (如果ID已存在，直接覆盖)
    existing_records[current_id] = new_record

    # 4. 全量写回文件 (确保唯一性)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            for _, rec in existing_records.items():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        st.error(f"保存失败: {e}")
        return False


# --- 初始化 Session State ---
if 'data' not in st.session_state:
    st.session_state['data'] = load_data(INPUT_FILE_PATH)

# 加载已保存的进度
if 'annotations' not in st.session_state:
    st.session_state.annotations = load_saved_progress(OUTPUT_FILE_PATH)

if 'current_index' not in st.session_state:
    st.session_state.current_index = 0

data = st.session_state['data']

if data:
    total_items = len(data)
    if st.session_state.current_index >= total_items:
        st.session_state.current_index = total_items - 1

    current_item = data[st.session_state.current_index]
    raw_id = current_item.get('id', 'No ID')
    current_key = str(raw_id)

    # --- 侧边栏 ---
    with st.sidebar:
        st.header("控制台")
        progress = (st.session_state.current_index + 1) / total_items
        st.progress(progress)
        st.write(f"进度: **{st.session_state.current_index + 1}** / {total_items}")

        c1, c2 = st.columns(2)
        if c1.button("⬅️ 上一条"):
            st.session_state.current_index = max(0, st.session_state.current_index - 1)
            st.rerun()
        if c2.button("下一条 ➡️"):
            st.session_state.current_index = min(total_items - 1, st.session_state.current_index + 1)
            st.rerun()

        target_idx = st.number_input("跳转到索引", 1, total_items, st.session_state.current_index + 1) - 1
        if target_idx != st.session_state.current_index:
            st.session_state.current_index = target_idx
            st.rerun()

        st.divider()
        st.write(f"已标注(本地保存): **{len(st.session_state.annotations)}**")
        st.info(f"结果已自动保存至:\n`{OUTPUT_FILE_PATH}`")

    # --- 主界面 ---
    col_id, col_status = st.columns([1, 2])
    with col_id:
        st.markdown(f'<div class="id-display">ID: {raw_id}</div>', unsafe_allow_html=True)
        st.caption(f"Model: {current_item.get('model', 'Unknown')}")

    with col_status:
        current_status = st.session_state.annotations.get(current_key)
        if current_status == "正确":
            st.markdown(f'<div class="status-box status-correct">✅ 已存：正确 (1)</div>', unsafe_allow_html=True)
        elif current_status == "错误":
            st.markdown(f'<div class="status-box status-wrong">❌ 已存：错误 (0)</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-box status-none">⚪ 未标记</div>', unsafe_allow_html=True)

    st.subheader("📝 Response")
    raw_response = current_item.get("response", "")
    parsed_content, is_valid_json = safe_parse_json(raw_response)

    display_text = json.dumps(parsed_content, indent=4, ensure_ascii=False) if is_valid_json else (
        raw_response.replace("\\n", "\n") if isinstance(raw_response, str) else str(raw_response))
    st.code(display_text, language="json" if is_valid_json else "text")
    st.markdown("---")

    # --- 判定区 ---
    st.subheader("请进行判定：")
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])


    def process_decision(label_code, status_text):
        # 1. 更新内存状态
        st.session_state.annotations[current_key] = status_text
        # 2. 立即保存到磁盘 (JSONL)
        save_record(current_item, label_code, OUTPUT_FILE_PATH)
        # 3. 自动跳转
        if st.session_state.current_index < total_items - 1:
            st.session_state.current_index += 1
        else:
            st.success("已是最后一条！")


    with btn_col1:
        if st.button("✅ 正确", type="primary", use_container_width=True, key=f"yes_{raw_id}"):
            process_decision(1, "正确")
            st.rerun()

    with btn_col2:
        if st.button("❌ 错误", type="secondary", use_container_width=True, key=f"no_{raw_id}"):
            process_decision(0, "错误")
            st.rerun()

    with st.expander("🔍 原始数据"):
        st.json(current_item.get("original_data", {}))

else:
    st.error("无法加载数据，请检查路径。")