import json
import os

# ================= 配置区域 =================
# 输入文件的名称
INPUT_FILE = 'taskmaster_20.jsonl'
# 注意：请确认这里指向的是你的真实数据文件路径

# 输出文件的名称
OUTPUT_FILE = 'taskmaster_test.jsonl'


# ===========================================

def format_dialogue_dataset(input_path, output_path):
    """
    读取原始数据集（支持 JSON 和 JSONL），将其转换为 {id, question, answer} 的 JSONL 格式。
    """

    raw_data = []

    # 1. 读取数据 (增强版：兼容 JSON 和 JSONL)
    print(f"正在读取文件: {input_path} ...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            # 方法 A: 尝试直接读取整个 JSON (针对标准 JSON list)
            try:
                content = json.load(f)
                if isinstance(content, list):
                    raw_data = content
                elif isinstance(content, dict):
                    raw_data = [content]
            except json.JSONDecodeError:
                # 方法 B: 如果失败，尝试按行读取 (针对 JSONL)
                f.seek(0)  # 文件指针回到开头
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            raw_data.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print(f"跳过无法解析的行: {e}")
                            continue

    except FileNotFoundError:
        print(f"错误：未找到文件 {input_path}")
        return

    print(f"读取成功，共 {len(raw_data)} 条数据。正在处理...")

    # 2. 处理并写入数据
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for idx, item in enumerate(raw_data):

            # --- 构建 Question (输入信息) ---
            instruction_id = item.get('instruction_id', 'Unknown')
            conversation_id = item.get('conversation_id', 'Unknown')

            # 构建清晰的对话文本
            dialogue_lines = []
            utterances = item.get('utterances', [])

            for turn in utterances:
                speaker = turn.get('speaker', 'UNKNOWN')
                text = turn.get('text', '')
                dialogue_lines.append(f"{speaker}: {text}")

            dialogue_text = "\n".join(dialogue_lines)

            # 组合成完整的 Question 字段
            question_content = (
                f"Instruction ID: {instruction_id}\n"
                f"Conversation ID: {conversation_id}\n"
                f"Please analyze the following conversation:\n\n"
                f"{dialogue_text}"
            )

            # --- 构建 Answer (参考答案) ---
            # 提取所有的 annotations 作为答案
            extracted_info = []

            for turn in utterances:
                # speaker = turn.get('speaker', '') # Unused in this scope
                segments = turn.get('segments', [])

                for seg in segments:
                    text_segment = seg.get('text', '')
                    annotations = seg.get('annotations', [])

                    for note in annotations:
                        label_name = note.get('name')
                        if label_name:
                            extracted_info.append(
                                f"Turn {turn.get('index')}: '{text_segment}' is identified as [{label_name}]"
                            )

            if extracted_info:
                answer_content = "\n".join(extracted_info)
            else:
                answer_content = "No specific entities identified in this conversation."

            # --- 组装最终对象 ---
            output_entry = {
                "id": idx,
                "question": question_content,
                "answer": answer_content
            }

            # 写入 JSONL
            f_out.write(json.dumps(output_entry, ensure_ascii=False) + '\n')

    print(f"处理完成！已生成文件：{output_path}")


# ================= 运行 =================
if __name__ == "__main__":
    # 确保使用绝对路径或正确的文件名
    # 如果你的文件名不是 taskmaster.json，请在代码顶部修改 INPUT_FILE
    format_dialogue_dataset(INPUT_FILE, OUTPUT_FILE)