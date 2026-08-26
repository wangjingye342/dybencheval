import json
import os

# === 配置部分 ===
input_file = 'legalbench_20.jsonl'  # 输入文件名，请确保您的源文件名为此或修改此处
output_file = 'legalbench_test.jsonl'  # 输出文件名


def process_dataset_new(input_path, output_path):
    print(f"正在读取文件: {input_path} ...")

    current_id = 0
    success_count = 0
    error_count = 0

    try:
        with open(input_path, 'r', encoding='utf-8') as f_in, \
                open(output_path, 'w', encoding='utf-8') as f_out:

            for line in f_in:
                line = line.strip()
                if not line:
                    continue

                try:
                    # 1. 解析原始数据
                    item = json.loads(line)

                    # 2. 字段映射
                    # 新数据集的 'inputs' 包含了完整的上下文和问题，直接作为 question
                    # 'answer' 字段直接就是答案文本，不需要通过索引查找
                    question_text = item.get('inputs', '').strip()
                    answer_text = item.get('answer', '').strip()

                    # 简单校验：如果关键字段为空，可以选择跳过或保留（这里选择保留但打印警告）
                    if not question_text or not answer_text:
                        print(f"警告: ID {current_id} 的 question 或 answer 为空。")

                    # 3. 构建新对象
                    new_entry = {
                        "id": current_id,
                        "question": question_text,
                        "answer": answer_text
                    }

                    # 4. 写入新文件
                    f_out.write(json.dumps(new_entry, ensure_ascii=False) + '\n')

                    current_id += 1
                    success_count += 1

                except json.JSONDecodeError:
                    print(f"错误: 无法解析 JSON 行")
                    error_count += 1
                except Exception as e:
                    print(f"未知错误: {e}")
                    error_count += 1

        print("-" * 30)
        print(f"处理完成！")
        print(f"成功转换: {success_count} 条")
        if error_count > 0:
            print(f"失败: {error_count} 条")
        print(f"结果已保存至: {output_path}")

    except FileNotFoundError:
        print(f"错误: 找不到文件 '{input_path}'。")


# === 创建示例文件并运行（为了演示） ===
if __name__ == "__main__":
    # 如果本地没有输入文件，生成一个包含您提供样例的临时文件
    if not os.path.exists(input_file):
        print(f"未检测到 {input_file}，正在生成示例文件...")
        sample_data = {
            "answer": "suggestive",
            "index": "54",
            "task_type": "conclusion",
            "task_name": "abercrombie",
            "inputs": "A mark is generic if it is the common name for the product. A mark is descriptive if it describes a purpose, nature, or attribute of the product. A mark is suggestive if it suggests or implies a quality or characteristic of the product. A mark is arbitrary if it is a real English word that has no relation to the product. A mark is fanciful if it is an invented word.\n\nQ: The mark \"Seventeen\" for magazines targeted at teenagers. What is the type of mark?\n\nAnswer by only outputting the mark label which is either fanciful, arbitrary, suggestive, descriptive or generic.",
            "multiple_choice_targets": ["generic", "descriptive", "suggestive", "arbitrary", "fanciful"],
            "__index_level_0__": 88221
        }
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(sample_data) + '\n')

    # 执行处理函数
    process_dataset_new(input_file, output_file)