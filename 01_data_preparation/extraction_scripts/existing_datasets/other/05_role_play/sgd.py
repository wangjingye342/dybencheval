import json
import os

# ================= 配置区域 =================
# 输入文件的名称
INPUT_FILE = 'SGD.jsonl'

# 输出文件的名称
OUTPUT_FILE = 'SGD_test.jsonl'


# ===========================================

def format_sgd_dataset(input_path, output_path):
    """
    读取 SGD (Schema-Guided Dialogue) 格式数据集，将其转换为 {id, question, answer} 的 JSONL 格式。

    策略：
    - question: 包含 Dialogue ID、涉及的服务 (Services) 以及完整的对话文本。
    - answer: 提取每一轮的语义帧 (Frames)，包括用户的意图/槽位状态 (State) 和系统的动作 (Actions)。
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
            services = item.get('services', [])
            services_str = ", ".join(services) if services else "None"

            # 构建对话文本剧本
            dialogue_lines = []
            turns = item.get('turns', [])

            for turn_idx, turn in enumerate(turns):
                speaker = turn.get('speaker', 'UNKNOWN')
                utterance = turn.get('utterance', '')
                dialogue_lines.append(f"Turn {turn_idx} [{speaker}]: {utterance}")

            full_dialogue_text = "\n".join(dialogue_lines)

            # 组合 Question
            question_content = (
                f"Dialogue ID: {dialogue_id}\n"
                f"Services: {services_str}\n"
                f"Task: Extract the dialogue state and system actions for the following conversation.\n\n"
                f"{full_dialogue_text}"
            )

            # --- 构建 Answer (参考答案) ---
            # 提取 Frames 中的核心语义信息
            extracted_info = []

            for turn_idx, turn in enumerate(turns):
                speaker = turn.get('speaker')
                frames = turn.get('frames', [])

                for frame in frames:
                    service_name = frame.get('service', 'unknown')

                    # 1. 处理 USER 侧信息 (意图 + 槽位状态)
                    if speaker == "USER":
                        state = frame.get('state', {})
                        active_intent = state.get('active_intent', 'NONE')
                        slot_values = state.get('slot_values', {})
                        requested_slots = state.get('requested_slots', [])

                        # 格式化槽位
                        slots_str = ", ".join([f"{k}='{v[0]}'" for k, v in slot_values.items()])
                        req_str = ", ".join(requested_slots)

                        info_str = (
                            f"Turn {turn_idx} [USER] Service({service_name}): "
                            f"Intent='{active_intent}'"
                        )
                        if slots_str:
                            info_str += f", Slots={{ {slots_str} }}"
                        if req_str:
                            info_str += f", Requested=[{req_str}]"

                        extracted_info.append(info_str)

                    # 2. 处理 SYSTEM 侧信息 (动作 Acts)
                    elif speaker == "SYSTEM":
                        actions = frame.get('actions', [])
                        action_strs = []
                        for act in actions:
                            act_type = act.get('act')
                            slot = act.get('slot', '')
                            values = act.get('values', [])
                            val_str = str(values[0]) if values else ""

                            # 格式化动作显示: OFFER(hotel=Azure)
                            if slot and val_str:
                                action_strs.append(f"{act_type}({slot}='{val_str}')")
                            elif slot:
                                action_strs.append(f"{act_type}({slot})")
                            else:
                                action_strs.append(f"{act_type}")

                        if action_strs:
                            extracted_info.append(
                                f"Turn {turn_idx} [SYSTEM] Service({service_name}): Actions=[{', '.join(action_strs)}]"
                            )

            if extracted_info:
                answer_content = "\n".join(extracted_info)
            else:
                answer_content = "No semantic frames found."

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
# 为了演示，这里创建一个包含你提供样例的临时文件
sample_data = {
    "dialogue_id": "1_00064",
    "services": ["Hotels_4"],
    "turns": [
        {
            "frames": [{"actions": [{"act": "INFORM_INTENT", "canonical_values": ["SearchHotel"], "slot": "intent",
                                     "values": ["SearchHotel"]}], "service": "Hotels_4", "slots": [],
                        "state": {"active_intent": "SearchHotel", "requested_slots": [], "slot_values": {}}}],
            "speaker": "USER", "utterance": "Hi, please help with a hotel."
        },
        {
            "frames": [{"actions": [{"act": "REQUEST", "canonical_values": [], "slot": "location", "values": []}],
                        "service": "Hotels_4", "slots": []}],
            "speaker": "SYSTEM", "utterance": "which city do you want?"
        },
        {
            "frames": [{"actions": [
                {"act": "INFORM", "canonical_values": ["Nairobi"], "slot": "location", "values": ["Nairobi"]}],
                        "service": "Hotels_4", "slots": [{"exclusive_end": 30, "slot": "location", "start": 23}],
                        "state": {"active_intent": "SearchHotel", "requested_slots": [],
                                  "slot_values": {"location": ["Nairobi"]}}}],
            "speaker": "USER", "utterance": "How about somewhere in Nairobi?"
        }
    ]
}

# 创建演示文件 (实际使用时请删除此块并使用真实文件)
if not os.path.exists(INPUT_FILE):
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump([sample_data], f, indent=2)

if __name__ == "__main__":
    format_sgd_dataset(INPUT_FILE, OUTPUT_FILE)