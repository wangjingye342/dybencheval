import json
import os

# 定义输入和输出路径
input_path = './external/model_re_evaluation/human_review_results/human_reviewed_0-129.jsonl'
output_path = './external/model_re_evaluation/human_review_results/最终数据集/rewrite_part1.jsonl'


def process_file(in_file, out_file):
    # 确保输出文件的目录存在
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    count_processed = 0
    count_saved = 0

    print(f"开始处理文件: {in_file}")

    try:
        with open(in_file, 'r', encoding='utf-8') as f_in, \
                open(out_file, 'w', encoding='utf-8') as f_out:

            for line_number, line in enumerate(f_in, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    count_processed += 1

                    # 1. 检查 human_decision 是否为 "Needs Rewrite (需重写)"
                    # 使用 .get 链式安全获取，防止某些行缺失字段报错
                    review_data = record.get("human_review", {})
                    decision = review_data.get("human_decision", "")

                    if decision == "Needs Rewrite (需重写)":
                        # 2. 提取数据
                        oid = record.get("original_id")
                        mod_data = record.get("modified_data", {})

                        # 3. 构建新对象：将 original_id 赋给 my_generated_id，并合并 modified_data
                        new_record = {"my_generated_id": oid}
                        new_record.update(mod_data)

                        # 4. 写入输出文件
                        f_out.write(json.dumps(new_record, ensure_ascii=False) + '\n')
                        count_saved += 1

                except json.JSONDecodeError:
                    print(f"警告: 第 {line_number} 行不是有效的 JSON 数据，已跳过。")
                except Exception as e:
                    print(f"警告: 处理第 {line_number} 行时发生错误: {e}")

        print("-" * 30)
        print(f"处理完成！")
        print(f"共读取行数: {count_processed}")
        print(f"符合条件并保存的行数: {count_saved}")
        print(f"输出文件位置: {out_file}")

    except FileNotFoundError:
        print(f"错误: 找不到输入文件: {in_file}")
    except Exception as e:
        print(f"发生未预期的错误: {e}")


if __name__ == "__main__":
    process_file(input_path, output_path)