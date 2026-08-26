import os
import json
from collections import OrderedDict


def merge_jsonl_to_json(root_dir, output_path):
    """
    遍历 DyBenchEval 目录下所有 jsonl 文件，
    合并为一个 json 文件（数组形式），
    并添加 id、task_domain、scenario_domain、source_file 字段。
    """

    merged_data = []
    global_id = 0

    for task_domain in os.listdir(root_dir):
        task_path = os.path.join(root_dir, task_domain)

        if not os.path.isdir(task_path):
            continue

        for scenario_domain in os.listdir(task_path):
            scenario_path = os.path.join(task_path, scenario_domain)

            if not os.path.isdir(scenario_path):
                continue

            for file_name in os.listdir(scenario_path):
                if not file_name.endswith(".jsonl"):
                    continue

                file_path = os.path.join(scenario_path, file_name)
                print(f"Processing: {file_path}")

                with open(file_path, "r", encoding="utf-8") as infile:
                    for line in infile:
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            sample = json.loads(line)
                        except json.JSONDecodeError:
                            print(f"Skipping invalid JSON line in {file_path}")
                            continue

                        # 兼容不同字段名
                        question = (
                            sample.get("question")
                            or sample.get("instruction")
                            or sample.get("input")
                            or ""
                        )

                        # 构造有序字典，保证字段顺序
                        ordered_sample = OrderedDict()
                        ordered_sample["id"] = global_id
                        ordered_sample["task_domain"] = task_domain
                        ordered_sample["scenario_domain"] = scenario_domain
                        ordered_sample["source_file"] = file_name
                        ordered_sample["question"] = question

                        merged_data.append(ordered_sample)
                        global_id += 1

    # 保存为 JSON 文件（数组格式）
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(merged_data, outfile, ensure_ascii=False, indent=2)

    print(f"\nFinished! Total samples: {global_id}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    root_directory = "DyBenchEval"  # 修改为你的路径
    output_file = "DyBenchEval_merged.json"

    merge_jsonl_to_json(root_directory, output_file)
