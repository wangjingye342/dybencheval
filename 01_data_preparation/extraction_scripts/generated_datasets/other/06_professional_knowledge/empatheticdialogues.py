import json
import argparse
from pathlib import Path


def build_question(item, include_scores=False):
    """
    question：包含所有提供给模型的有用信息
    """
    conv_id = str(item.get("conv_id", "")).strip()
    utt_idx = item.get("utterance_idx", "")
    speaker = item.get("speaker_idx", "")
    context = str(item.get("context", "")).strip()
    prompt = str(item.get("prompt", "")).strip()

    selfeval = str(item.get("selfeval", "")).strip()
    c9 = item.get("C9", "")

    question = (
        "You are given a conversation context and a prompt. Generate the next utterance.\n\n"
        f"Conversation ID: {conv_id}\n"
        f"Utterance Index: {utt_idx}\n"
        f"Speaker Index: {speaker}\n\n"
        "=== Prompt ===\n"
        f"{prompt}\n\n"
        "=== Context ===\n"
        f"{context}\n\n"
    )

    if include_scores:
        question += (
            "=== Self-evaluation / Scores (Optional) ===\n"
            f"selfeval: {selfeval}\n"
            f"C9: {c9}\n\n"
        )

    question += "Task: Generate the next utterance."
    return question


def build_answer(item):
    """
    answer：参考答案 utterance
    """
    return str(item.get("utterance", "")).strip()


def build_id(item, idx):
    """
    id：conv_id + utterance_idx
    """
    conv_id = str(item.get("conv_id", "")).strip()
    utt_idx = item.get("utterance_idx", idx)
    return f"{conv_id}_{utt_idx}"


def convert_dataset(input_file, output_file, include_scores=False):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            item = json.loads(line)

            sample_id = build_id(item, idx)
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
        description="Convert utterance-level dialog JSONL dataset into training format (id/question/answer)"
    )
    parser.add_argument("--input", required=True, help="Input JSONL file path")
    parser.add_argument("--output", required=True, help="Output JSONL file path")
    parser.add_argument(
        "--include_scores",
        action="store_true",
        help="Include selfeval and C9 score in question (default False)"
    )

    args = parser.parse_args()
    convert_dataset(args.input, args.output, include_scores=args.include_scores)


if __name__ == "__main__":
    main()
