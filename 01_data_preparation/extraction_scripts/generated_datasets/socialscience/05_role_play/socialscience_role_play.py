import json
import argparse
from pathlib import Path


def format_dict(d):
    """dict -> pretty JSON string"""
    if not d:
        return ""
    return json.dumps(d, ensure_ascii=False, indent=2)


def format_conversation(conversation):
    """
    conversation list -> 多轮对话文本
    每轮可能是 dict / list / str，尽量兼容
    """
    lines = []
    for turn in conversation:
        if isinstance(turn, dict):
            role = turn.get("role", turn.get("speaker", "unknown"))
            text = turn.get("text", turn.get("content", turn.get("utterance", "")))
            lines.append(f"{role}: {text}")
        elif isinstance(turn, list) and len(turn) == 2:
            lines.append(f"{turn[0]}: {turn[1]}")
        else:
            lines.append(str(turn))
    return "\n".join(lines)


def split_context_and_answer(conversation):
    """
    默认策略：
    - 前 N-1 轮作为 context
    - 最后一轮作为 answer
    """
    if not conversation or len(conversation) < 2:
        return conversation, ""
    return conversation[:-1], conversation[-1]


def extract_turn_text(turn):
    """从最后一轮提取文本"""
    if isinstance(turn, dict):
        return str(turn.get("text", turn.get("content", turn.get("utterance", "")))).strip()
    if isinstance(turn, list) and len(turn) == 2:
        return str(turn[1]).strip()
    return str(turn).strip()


def build_question(item):
    """
    question：包含所有对模型有用的信息
    """
    gid = item.get("my_generated_id", "")
    target_scenario = str(item.get("target_scenario", "")).strip()
    target_task = str(item.get("target_task", "")).strip()
    meta_info = item.get("meta_info", {})
    role_def = item.get("role_definition", {})
    situation = str(item.get("situation_context", "")).strip()
    conversation = item.get("conversation", [])

    context_turns, _ = split_context_and_answer(conversation)

    question = (
        "You are role-playing based on the given role definition and situation context. "
        "Continue the conversation appropriately.\n\n"
        f"Generated ID: {gid}\n"
        f"Target Scenario: {target_scenario}\n"
        f"Target Task: {target_task}\n\n"
        "=== Meta Info ===\n"
        f"{format_dict(meta_info)}\n\n"
        "=== Role Definition ===\n"
        f"{format_dict(role_def)}\n\n"
        "=== Situation Context ===\n"
        f"{situation}\n\n"
        "=== Conversation History ===\n"
        f"{format_conversation(context_turns)}\n\n"
        "Task: Generate the next response."
    )
    return question


def build_answer(item):
    """
    answer：取 conversation 最后一轮作为参考答案
    """
    conversation = item.get("conversation", [])
    if not conversation:
        return ""
    _, last_turn = split_context_and_answer(conversation)
    return extract_turn_text(last_turn)


def build_id(item, idx):
    """
    id：优先 my_generated_id，否则 fallback 行号
    """
    gid = item.get("my_generated_id", None)
    if gid is not None:
        return str(gid)
    return f"sample_{idx}"


def convert_dataset(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            results.append({
                "id": build_id(item, idx),
                "question": build_question(item),
                "answer": build_answer(item)
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert roleplay conversation JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
