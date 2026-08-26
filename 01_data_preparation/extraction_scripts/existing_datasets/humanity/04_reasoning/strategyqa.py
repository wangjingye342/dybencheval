import json
import argparse


def convert_dataset(input_path, output_path):
    """
    Convert a JSONL dataset into training format:
    {"id": "...", "question": "...", "answer": "..."}
    """
    new_id = 1

    with open(input_path, "r", encoding="utf-8") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:

        for line in fin:
            line = line.strip()
            if not line:
                continue

            record = json.loads(line)

            # ---------- build question ----------
            question_parts = []

            if "instruction" in record:
                question_parts.append(str(record["instruction"]))
            if "input" in record and record["input"]:
                question_parts.append(str(record["input"]))
            if "question" in record:
                question_parts.append(str(record["question"]))

            if question_parts:
                question = "\n".join(question_parts).strip()
            else:
                # fallback: use full record as question
                question = json.dumps(record, ensure_ascii=False)

            # ---------- build answer ----------
            if "answer" in record:
                answer = str(record["answer"])
            elif "output" in record:
                answer = str(record["output"])
            elif "response" in record:
                answer = str(record["response"])
            else:
                answer = ""

            new_record = {
                "id": str(new_id),
                "question": question,
                "answer": answer
            }

            fout.write(json.dumps(new_record, ensure_ascii=False) + "\n")
            new_id += 1

    print(f"✅ Done. Output saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert JSONL dataset to training format"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input JSONL file"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output JSONL file"
    )

    args = parser.parse_args()
    convert_dataset(args.input, args.output)


if __name__ == "__main__":
    main()
