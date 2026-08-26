import json
import os

# ================= 配置区域 =================
# 输入文件的名称
# 建议将你的输入文件命名为 input_multiwoz.json 或修改此处路径
INPUT_FILE = 'mutiwoz_20.jsonl'

# 输出文件的名称
OUTPUT_FILE = 'mutiwoz_test.jsonl'


# ===========================================

def format_multiwoz_dataset(input_path, output_path):
    """
    读取 MultiWOZ 格式数据集，将其转换为 {id, question, answer} 的 JSONL 格式。
    策略：
    - question: 包含对话 ID、涉及的服务列表以及完整的对话文本。
    - answer: 提取每一轮 USER 发言后的状态追踪结果（Intent 和 Slots）。
    """

    raw_data = []

    # 1. 读取数据 (兼容 JSON list 和 JSONL)
    print(f"正在读取文件: {input_path} ...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            try:
                # 尝试一次性读取（针对标准 JSON 列表）
                content = json.load(f)
                if isinstance(content, list):
                    raw_data = content
                elif isinstance(content, dict):
                    raw_data = [content]
            except json.JSONDecodeError:
                # 失败则尝试逐行读取（针对 JSONL）
                f.seek(0)
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            raw_data.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
    except FileNotFoundError:
        print(f"错误：未找到文件 {input_path}")
        return

    print(f"读取成功，共 {len(raw_data)} 条数据。正在处理...")

    # 2. 处理并写入数据
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for idx, item in enumerate(raw_data):

            # --- 构建 Question (输入信息) ---
            dialogue_id = item.get('dialogue_id', 'Unknown')
            # 获取涉及的服务列表
            services = item.get('services', [])
            services_str = ", ".join(services) if services else "None"

            # 构建对话文本
            dialogue_lines = []
            turns = item.get('turns', [])

            for turn in turns:
                speaker = turn.get('speaker', 'UNKNOWN')
                text = turn.get('utterance', '')
                dialogue_lines.append(f"{speaker}: {text}")

            full_dialogue_text = "\n".join(dialogue_lines)

            # 组合 Question
            question_content = (
                f"Dialogue ID: {dialogue_id}\n"
                f"Active Services: {services_str}\n"
                f"Task: Track the dialogue state (intents and slots) for the following conversation.\n\n"
                f"{full_dialogue_text}"
            )

            # --- 构建 Answer (参考答案) ---
            # 从 'frames' 中提取状态信息
            extracted_states = []

            for turn in turns:
                # 只分析 USER 的轮次，因为状态追踪通常是追踪用户的需求
                if turn.get('speaker') == 'USER':
                    turn_id = turn.get('turn_id')
                    frames = turn.get('frames', [])

                    # 遍历该轮次下所有服务的帧
                    for frame in frames:
                        service_name = frame.get('service', 'unknown')
                        state = frame.get('state', {})

                        active_intent = state.get('active_intent', 'NONE')
                        slot_values = state.get('slot_values', {})

                        # 过滤逻辑：
                        # 只有当意图不是 NONE，或者有槽位值时，才记录该服务的状态。
                        # MultiWOZ 中每一轮都会列出所有服务，很多是空的，必须过滤。
                        if active_intent != 'NONE' or len(slot_values) > 0:

                            # 格式化槽位: {"day": ["friday"]} -> day='friday'
                            slots_list = []
                            for k, v in slot_values.items():
                                val_str = v[0] if isinstance(v, list) and len(v) > 0 else str(v)
                                slots_list.append(f"{k}='{val_str}'")

                            slots_display = ", ".join(slots_list)

                            # 生成一行状态描述
                            state_desc = (
                                f"Turn {turn_id} [{service_name}]: "
                                f"Intent='{active_intent}', "
                                f"Slots={{ {slots_display} }}"
                            )
                            extracted_states.append(state_desc)

            if extracted_states:
                answer_content = "\n".join(extracted_states)
            else:
                answer_content = "No active dialogue state detected."

            # --- 组装最终对象 ---
            output_entry = {
                "id": idx,
                "question": question_content,
                "answer": answer_content
            }

            # 写入 JSONL
            f_out.write(json.dumps(output_entry, ensure_ascii=False) + '\n')

    print(f"处理完成！已生成文件：{output_path}")


# ================= 运行示例 =================
# 为了演示，这里创建一个临时的输入文件（包含你提供的样例）
# 实际使用时，请删除下面这段生成文件的代码，直接使用你的真实文件
sample_data = {
    "dialogue_id": "PMUL3141.json",
    "services": ["train", "hotel"],
    "turns": [
        {
            "frames": [{"actions": [], "service": "train", "slots": [],
                        "state": {"active_intent": "find_train", "requested_slots": [],
                                  "slot_values": {"train-day": ["friday"], "train-destination": ["cambridge"]}}}],
            "speaker": "USER", "turn_id": "0",
            "utterance": "I'm looking for a train leaving on friday going to cambridge."
        },
        {"frames": [], "speaker": "SYSTEM", "turn_id": "1",
         "utterance": "I can help with that. Where will you be departing from?"},
        {
            "frames": [{"actions": [], "service": "train", "slots": [],
                        "state": {"active_intent": "find_train", "requested_slots": [],
                                  "slot_values": {"train-arriveby": ["15:15"], "train-day": ["friday"],
                                                  "train-destination": ["cambridge"]}}}],
            "speaker": "USER", "turn_id": "2", "utterance": "I just want to arrive by 15:15."
        }
    ]
}

# 如果文件不存在，创建一个 demo 文件
if not os.path.exists(INPUT_FILE):
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        # 模拟一个 JSON 列表
        json.dump([sample_data], f, indent=2)

if __name__ == "__main__":
    format_multiwoz_dataset(INPUT_FILE, OUTPUT_FILE)