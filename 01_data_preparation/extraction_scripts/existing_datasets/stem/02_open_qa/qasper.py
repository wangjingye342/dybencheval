import json
import argparse
from pathlib import Path


def tokens_to_text(sentences):
    return "\n".join([" ".join(sent) for sent in sentences])


def format_clusters(clusters):
    cluster_strs = []
    for idx, cluster in enumerate(clusters):
        spans = [f"{span}" for span in cluster]
        cluster_strs.append(f"Cluster {idx}: " + "; ".join(spans))
    return "\n".join(cluster_strs)


def format_relations(relations):
    rel_strs = []
    for sent_idx, rel_list in enumerate(relations):
        for rel in rel_list:
            if len(rel) == 5:
                s1, e1, s2, e2, label = rel
                rel_strs.append(
                    f"Sent {sent_idx}: ({s1}-{e1}) --{label}--> ({s2}-{e2})"
                )
            else:
                rel_strs.append(f"Sent {sent_idx}: {rel}")
    return "\n".join(rel_strs)


def build_question(item):
    doc_text = tokens_to_text(item.get("sentences", []))
    clusters_info = format_clusters(item.get("clusters", []))
    relations_info = format_relations(item.get("relations", []))

    question = (
        "You are given a document with tokenized sentences, entity clusters, and relations.\n\n"
        "=== Document Text ===\n"
        f"{doc_text}\n\n"
        "=== Entity Clusters (spans) ===\n"
        f"{clusters_info}\n\n"
        "=== Relations (spans and labels) ===\n"
        f"{relations_info}\n\n"
        "Task: Predict or reason about relations based on the given context."
    )
    return question


def build_answer(item):
    return json.dumps(item.get("relations", []), ensure_ascii=False)


def convert_dataset(input_file, output_file):
    input_path = Path(input_file)
    output_path = Path(output_file)

    results = []
    with input_path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            item = json.loads(line)
            sample_id = item.get("doc_key", f"sample_{i}")
            results.append({
                "id": sample_id,
                "question": build_question(item),
                "answer": build_answer(item)
            })

    with output_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"✅ Converted {len(results)} samples -> {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Batch convert multiple JSONL datasets")
    parser.add_argument("--inputs", nargs="+", required=True, help="Input JSONL file paths")
    parser.add_argument("--output_dir", required=True, help="Directory to save outputs")

    args = parser.parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for input_file in args.inputs:
        input_path = Path(input_file)
        out_file = out_dir / f"{input_path.stem}_train.jsonl"
        convert_dataset(input_file, out_file)


if __name__ == "__main__":
    main()
