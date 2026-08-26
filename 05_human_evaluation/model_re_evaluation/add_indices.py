import json
from collections import OrderedDict

def add_index_to_jsonl(
    input_jsonl_path: str,
    output_jsonl_path: str,
    start_index: int = 0
):
    """
    为 jsonl 文件中的每一项添加一个 index 字段，并放在第一个位置
    """
    with open(input_jsonl_path, "r", encoding="utf-8") as fin, \
         open(output_jsonl_path, "w", encoding="utf-8") as fout:

        for idx, line in enumerate(fin, start=start_index):
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)

            # 构造新的有序字典，确保 index 在最前
            new_data = OrderedDict()
            new_data["index"] = idx

            for k, v in data.items():
                new_data[k] = v

            fout.write(json.dumps(new_data, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    input_path = "./external/model_re_evaluation/responses.jsonl"
    output_path = "output_with_index.jsonl"

    add_index_to_jsonl(input_path, output_path)
