import json
import argparse
from pathlib import Path


def format_participant_info(info: dict):
    """participant_info dict -> 可读文本"""
    if not info:
        return ""
    return "\n".join([f"{k}: {v}" for k, v in info.items()])


def format_annotations(annotations):
    """annotations list -> 可读文本（可选）"""
    if not annotations:
        return ""
    if isinstance(annotations, list):
        # 每条 annotation 可能是 dict
        return "\n".join([json.dumps(a, ensure_ascii=False) for a in annotations])
    return str(annotations)


def format_chat_logs(chat_logs):
    """chat_logs list -> 可读多轮对话文本"""
    lines = []
    for turn in chat_logs:
        if isinstance(turn, dict):
            role = turn.get("role", turn.get("speaker", "unknown"))
            text = turn.get("text", turn.get("content", turn.get("message", "")))
            lines.append(f"{role}: {text}")
        else:
            lines.append(str(turn))
    return "\n".join(lines)


def split_context_and_answer(chat_logs):
    """
    默认策略：
    - 前 N-1 轮作为 context
    - 最后一轮作为 answer
    """
    if not chat_logs or len(chat_logs) < 2:
        return chat_logs, ""

    context = chat_logs[:-1]
    answer_turn = chat_logs[-1]
    return context, answer_turn


def extract_turn_text(turn):
    """从 turn 中提取文本"""
    if isinstance(turn, dict):
        return str(turn.get("text", turn.get("content", turn.get("message", "")))).strip()
    return str(turn).strip()


def convert_dataset(input_file, output_file, include_annotations=True):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            participant_info = item.get("participant_info", {})
            annotations = item.get("annotations", [])
            chat_logs = item.get("chat_logs", [])

            context_turns, answer_turn = split_context_and_answer(chat_logs)

            question = (
                "You are given participant information and a conversation history. "
                "Generate the next appropriate response.\n\n"
                "=== Participant Info ===\n"
                f"{format_participant_info(participant_info)}\n\n"
                "=== Conversation History ===\n"
                f"{format_chat_logs(context_turns)}\n\n"
            )

            if include_annotations and annotations:
                question += (
                    "=== Annotations (Optional) ===\n"
                    f"{format_annotations(annotations)}\n\n"
                )

            question += "Task: Generate the next response."

            answer = extract_turn_text(answer_turn)

            results.append({
                "id": f"chat_{idx}",
                "question": question,
                "answer": answer
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert chat logs + participant info + annotations JSONL into training format"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument(
        "--include_annotations",
        action="store_true",
        help="Whether to include annotations into question (default False)"
    )

    args = parser.parse_args()
    convert_dataset(args.input, args.output, include_annotations=args.include_annotations)


if __name__ == "__main__":
    main()
