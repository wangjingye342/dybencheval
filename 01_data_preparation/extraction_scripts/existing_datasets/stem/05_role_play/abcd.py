import json
import argparse
from pathlib import Path


def format_scenario(scenario):
    """
    将 scenario dict 转换为可读文本
    """
    if not scenario:
        return ""
    parts = []
    for k, v in scenario.items():
        parts.append(f"{k}: {v}")
    return "\n".join(parts)


def format_dialog(dialog):
    """
    将对话 list 格式化为文本
    dialog 通常是 list[dict] 或 list[str]
    """
    lines = []
    for turn in dialog:
        if isinstance(turn, dict):
            role = turn.get("role", turn.get("speaker", "unknown"))
            text = turn.get("text", turn.get("utterance", ""))
            lines.append(f"{role}: {text}")
        else:
            lines.append(str(turn))
    return "\n".join(lines)


def split_context_and_answer(dialog):
    """
    默认策略：
    - 前 N-1 轮作为 context
    - 最后一轮作为 answer
    """
    if not dialog or len(dialog) < 2:
        return dialog, ""

    context = dialog[:-1]
    answer_turn = dialog[-1]
    return context, answer_turn


def convert_dataset(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            convo_id = item.get("convo_id", idx)
            scenario = item.get("scenario", {})
            original_dialog = item.get("original", [])

            context_turns, answer_turn = split_context_and_answer(original_dialog)

            # question：scenario + 对话上下文
            question = (
                "You are given a conversation scenario and conversation history.\n\n"
                "=== Scenario ===\n"
                f"{format_scenario(scenario)}\n\n"
                "=== Conversation History ===\n"
                f"{format_dialog(context_turns)}\n\n"
                "Task: Generate the next response."
            )

            # answer：最后一轮
            if isinstance(answer_turn, dict):
                answer = answer_turn.get("text", answer_turn.get("utterance", ""))
            else:
                answer = str(answer_turn)

            results.append({
                "id": str(convo_id),
                "question": question,
                "answer": answer.strip()
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert conversation JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
