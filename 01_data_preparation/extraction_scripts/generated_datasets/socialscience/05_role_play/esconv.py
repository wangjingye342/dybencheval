import json
import argparse
from pathlib import Path


def format_scores(scores: dict):
    """survey_score dict -> 文本"""
    if not scores:
        return ""
    return "\n".join([f"{k}: {v}" for k, v in scores.items()])


def format_dialog(dialog):
    """
    dialog list -> 多轮对话文本
    每轮可能是 dict / list / str，尽量兼容
    """
    lines = []
    for turn in dialog:
        if isinstance(turn, dict):
            role = turn.get("role", turn.get("speaker", "unknown"))
            text = turn.get("text", turn.get("content", turn.get("utterance", "")))
            lines.append(f"{role}: {text}")
        elif isinstance(turn, list) and len(turn) == 2:
            lines.append(f"{turn[0]}: {turn[1]}")
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
    return dialog[:-1], dialog[-1]


def extract_text(turn):
    """从最后一轮 turn 中提取文本"""
    if isinstance(turn, dict):
        return str(turn.get("text", turn.get("content", turn.get("utterance", "")))).strip()
    if isinstance(turn, list) and len(turn) == 2:
        return str(turn[1]).strip()
    return str(turn).strip()


def build_question(item, include_scores=True):
    """
    question：包含所有对模型有用的信息
    """
    exp_type = str(item.get("experience_type", "")).strip()
    emo_type = str(item.get("emotion_type", "")).strip()
    prob_type = str(item.get("problem_type", "")).strip()
    situation = str(item.get("situation", "")).strip()

    scores = item.get("survey_score", {})
    dialog = item.get("dialog", [])

    seeker_q1 = str(item.get("seeker_question1", "")).strip()
    seeker_q2 = str(item.get("seeker_question2", "")).strip()
    supporter_q1 = str(item.get("supporter_question1", "")).strip()
    supporter_q2 = str(item.get("supporter_question2", "")).strip()

    context_turns, _ = split_context_and_answer(dialog)

    question = (
        "You are a supportive counselor. Based on the situation and the conversation history, "
        "generate a helpful supporter response.\n\n"
        f"Experience Type: {exp_type}\n"
        f"Emotion Type: {emo_type}\n"
        f"Problem Type: {prob_type}\n\n"
        "=== Situation ===\n"
        f"{situation}\n\n"
        "=== Seeker Questions ===\n"
        f"Q1: {seeker_q1}\n"
        f"Q2: {seeker_q2}\n\n"
        "=== Supporter Questions ===\n"
        f"Q1: {supporter_q1}\n"
        f"Q2: {supporter_q2}\n\n"
        "=== Conversation History ===\n"
        f"{format_dialog(context_turns)}\n\n"
    )

    if include_scores and scores:
        question += (
            "=== Survey Scores (Optional) ===\n"
            f"{format_scores(scores)}\n\n"
        )

    question += "Task: Generate the next supporter response."
    return question


def build_answer(item):
    """
    answer：取 dialog 最后一轮作为参考答案
    """
    dialog = item.get("dialog", [])
    if not dialog:
        return ""
    _, last_turn = split_context_and_answer(dialog)
    return extract_text(last_turn)


def build_id(idx):
    """
    id：行号生成
    """
    return f"sample_{idx}"


def convert_dataset(input_file, output_file, include_scores=True):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            sample_id = build_id(idx)
            question = build_question(item, include_scores=include_scores)
            answer = build_answer(item)

            results.append({
                "id": sample_id,
                "question": question,
                "answer": answer
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert emotional support dialog JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument(
        "--exclude_scores",
        action="store_true",
        help="If set, do NOT include survey_score in question (default includes)"
    )

    args = parser.parse_args()
    include_scores = not args.exclude_scores
    convert_dataset(args.input, args.output, include_scores=include_scores)


if __name__ == "__main__":
    main()
