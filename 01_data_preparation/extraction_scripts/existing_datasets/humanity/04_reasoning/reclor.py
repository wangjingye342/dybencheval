import json
import os

# === 配置部分 ===
input_file = 'ReClor_20.jsonl'  # 输入文件名
output_file = 'ReClor_20_test.jsonl'  # 输出文件名


def process_jsonl(input_path, output_path):
    print(f"正在读取文件: {input_path} ...")

    # 计数器，用于生成新的 ID
    new_id_counter = 0
    success_count = 0
    error_count = 0

    try:
        with open(input_path, 'r', encoding='utf-8') as f_in, \
                open(output_path, 'w', encoding='utf-8') as f_out:

            for line in f_in:
                line = line.strip()
                if not line:
                    continue  # 跳过空行

                try:
                    # 1. 解析原始数据
                    item = json.loads(line)

                    # 2. 提取并处理字段
                    # 合并 context 和 question
                    context = item.get('context', '')
                    question_text = item.get('question', '')
                    full_question = f"{context}\n{question_text}".strip()

                    # 根据 label 获取正确答案
                    answers = item.get('answers', [])
                    label_idx = item.get('label')

                    # 简单的错误检查，防止索引越界
                    if isinstance(label_idx, int) and 0 <= label_idx < len(answers):
                        final_answer = answers[label_idx]
                    else:
                        final_answer = ""  # 或者标记为错误数据
                        print(f"警告: ID {item.get('id_string')} 的 label 索引无效，已置空。")

                    # 3. 构建新对象
                    new_entry = {
                        "id": new_id_counter,
                        "question": full_question,
                        "answer": final_answer
                    }

                    # 4. 写入新文件 (JSONL格式：一行一个JSON，不包含缩进)
                    f_out.write(json.dumps(new_entry, ensure_ascii=False) + '\n')

                    # 更新计数器
                    new_id_counter += 1
                    success_count += 1

                except json.JSONDecodeError:
                    print(f"错误: 无法解析行: {line[:50]}...")
                    error_count += 1
                except Exception as e:
                    print(f"处理数据时发生未知错误: {e}")
                    error_count += 1

        print("-" * 30)
        print(f"处理完成！")
        print(f"成功转换条数: {success_count}")
        if error_count > 0:
            print(f"失败/跳过条数: {error_count}")
        print(f"新数据集已保存为: {output_path}")

    except FileNotFoundError:
        print(f"错误: 找不到输入文件 '{input_path}'。请确保文件在当前目录下。")


# === 执行主函数 ===
if __name__ == "__main__":
    # 如果你没有真实文件，可以先生成一个示例文件来测试
    if not os.path.exists(input_file):
        print("未找到输入文件，正在生成示例文件 'data.jsonl' 用于演示...")
        sample_data = {
            "context": "Sample context text.",
            "question": "Sample question?",
            "answers": ["Wrong answer", "Correct answer"],
            "label": 1,
            "id_string": "test_001"
        }
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(sample_data) + '\n')

    process_jsonl(input_file, output_file)