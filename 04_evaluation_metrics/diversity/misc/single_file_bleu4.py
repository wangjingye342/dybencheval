import json
from pathlib import Path
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

def compute_average_bleu4(jsonl_path):
    jsonl_path = Path(jsonl_path)
    assert jsonl_path.exists(), f"{jsonl_path} does not exist"

    smoothie = SmoothingFunction().method4
    bleu_scores = []
    total_lines = 0
    skipped_lines = 0

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            data = json.loads(line)

            seed_text = data.get("seed_text")
            response_text = data.get("response_text")

            if not seed_text or not response_text:
                skipped_lines += 1
                continue

            # 简单空格分词（推荐，稳定）
            reference = [seed_text.split()]
            candidate = response_text.split()

            bleu4 = sentence_bleu(
                reference,
                candidate,
                weights=(0.25, 0.25, 0.25, 0.25),
                smoothing_function=smoothie
            )

            bleu_scores.append(bleu4)

    if not bleu_scores:
        raise ValueError("No valid samples found for BLEU computation.")

    avg_bleu = sum(bleu_scores) / len(bleu_scores)

    print(f"Total lines     : {total_lines}")
    print(f"Valid samples   : {len(bleu_scores)}")
    print(f"Skipped samples : {skipped_lines}")
    print(f"Average BLEU-4  : {avg_bleu:.6f}")

    return avg_bleu


if __name__ == "__main__":
    jsonl_file = "qwen3-8b_seed_response_extracted.jsonl"
    compute_average_bleu4(jsonl_file)
