import streamlit as st
import json
import os
import html

# --- 1. 基础配置 ---
st.set_page_config(page_title="JSON 高级校验工具", layout="wide")

INPUT_FILE = "正确性120.jsonl"
OUTPUT_FILE = "labeled_120.jsonl"


# --- 2. 核心渲染函数 (移植自你提供的代码) ---
def render_colored_json(data, indent=0):
    """
    递归渲染 JSON 为 HTML:
    1. Key 显示为黄色。
    2. Value 中的 \n 转换为 <br> 实现换行。
    3. 长文本自动折行。
    """
    TAB = "&nbsp;&nbsp;&nbsp;&nbsp;"
    current_indent = TAB * indent
    next_indent = TAB * (indent + 1)
    value_indent = TAB * (indent + 2)

    # 样式定义
    STYLE_KEY = 'color: #FFFF00; font-weight: bold;'  # Key: 亮黄
    STYLE_SYMBOL = 'color: #F1C40F; font-weight: bold;'  # 符号: 金黄
    STYLE_STRING = 'color: #E0E0E0; word-break: break-word;'  # 字符串: 灰白，允许换行
    STYLE_NUMBER = 'color: #56B6C2;'  # 数字: 青色

    html_output = ""

    if isinstance(data, dict):
        html_output += f'<span style="{STYLE_SYMBOL}">{{</span><br>'
        items = list(data.items())
        for i, (key, val) in enumerate(items):
            key_html = f'<span style="{STYLE_KEY}">"{html.escape(str(key))}"</span>'
            colon_html = f'<span style="{STYLE_SYMBOL}">: </span>'
            val_html = render_colored_json(val, indent + 1)
            comma = f'<span style="{STYLE_SYMBOL}">,</span>' if i < len(items) - 1 else ''

            # 布局: 缩进Key -> 冒号 -> 值 -> 逗号 -> 换行
            # 注意：这里我们让 Value 紧跟 Key 显示，如果 Value 是复杂对象，它内部会有换行
            if isinstance(val, (dict, list)):
                # 如果值是对象/列表，另起一行显示值，保持层级清晰
                html_output += f'{next_indent}{key_html}{colon_html}<br>{next_indent}{val_html}{comma}<br>'
            else:
                # 如果值是基本类型，同行显示
                html_output += f'{next_indent}{key_html}{colon_html}{val_html}{comma}<br>'

        html_output += f'{current_indent}<span style="{STYLE_SYMBOL}">}}</span>'

    elif isinstance(data, list):
        html_output += f'<span style="{STYLE_SYMBOL}">[</span><br>'
        for i, val in enumerate(data):
            val_html = render_colored_json(val, indent + 1)
            comma = f'<span style="{STYLE_SYMBOL}">,</span>' if i < len(data) - 1 else ''
            html_output += f'{next_indent}{val_html}{comma}<br>'
        html_output += f'{current_indent}<span style="{STYLE_SYMBOL}">]</span>'

    elif isinstance(data, str):
        # 核心：处理换行符 + HTML转义
        safe_str = html.escape(data).replace('\n', '<br>').replace('\\n', '<br>')
        html_output += f'<span style="{STYLE_SYMBOL}">"</span><span style="{STYLE_STRING}">{safe_str}</span><span style="{STYLE_SYMBOL}">"</span>'

    elif isinstance(data, (int, float, bool)) or data is None:
        val_str = str(data).lower() if isinstance(data, bool) else str(data)
        html_output += f'<span style="{STYLE_NUMBER}">{val_str}</span>'

    return html_output


# --- 3. 数据处理逻辑 ---
def load_data():
    data = []
    if os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data.append(json.loads(line))
                    except:
                        pass
    return data


def save_result(record):
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_labeled_ids():
    labeled = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    if 'original_index' in obj:
                        labeled.add(obj['original_index'])
                except:
                    pass
    return labeled


# --- 4. 初始化 Session ---
if 'data' not in st.session_state:
    st.session_state.data = load_data()

if 'current_index' not in st.session_state:
    labeled_ids = get_labeled_ids()
    start = 0
    for i in range(len(st.session_state.data)):
        if i not in labeled_ids:
            start = i
            break
    st.session_state.current_index = start


# --- 5. 主界面逻辑 ---
def main():
    data = st.session_state.data
    if not data:
        st.error(f"没有数据，请检查 {INPUT_FILE}")
        return

    idx = st.session_state.current_index
    total = len(data)

    # 顶部进度条
    st.progress((idx + 1) / total)
    st.caption(f"当前进度: {idx + 1} / {total}")

    row = data[idx]
    raw_response = row.get("response", "")

    # --- 核心展示区：使用高级 HTML 渲染 ---
    st.markdown("---")
    st.subheader("📄 Model Response Content")

    parsed_json = None
    is_valid_json = False

    try:
        parsed_json = json.loads(raw_response)
        is_valid_json = True

        # 调用渲染函数生成 HTML
        json_html = render_colored_json(parsed_json)

        # 嵌入到一个带有深色背景和滚动条的 Div 中
        st.markdown(
            f"""
            <div style="
                background-color: #1E1E1E; 
                padding: 20px; 
                border-radius: 10px; 
                border: 1px solid #444;
                font-family: 'Consolas', 'Monaco', monospace; 
                font-size: 15px; 
                line-height: 1.6;
                white-space: normal; /* 允许自动换行 */
            ">
                {json_html}
            </div>
            """,
            unsafe_allow_html=True
        )

    except json.JSONDecodeError:
        st.error("⚠️ JSON 解析失败，显示原始文本")
        st.text_area("Raw Response", raw_response, height=300)

    st.markdown("---")

    # --- 6. 底部操作区 (合并选项) ---

    def submit(label):
        record = {
            "original_index": idx,
            "model": row.get("model", "unknown"),
            "content": parsed_json if is_valid_json else raw_response,
            "human_label": label,
            "is_valid_json": is_valid_json
        }
        save_result(record)

        if st.session_state.current_index < total - 1:
            st.session_state.current_index += 1
            st.rerun()
        else:
            st.success("🎉 所有任务完成！")

    # 三列布局按钮
    c1, c2, c3 = st.columns([1, 1, 1])

    with c1:
        if st.button("✅ 正确", type="primary", use_container_width=True):
            submit("正确")

    with c2:
        # 错误选项合并
        if st.button("❌ 错误 (逻辑/内容/格式)", use_container_width=True):
            submit("错误")

    with c3:
        if st.button("⬅️ 上一条", use_container_width=True):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1
                st.rerun()


if __name__ == "__main__":
    main()