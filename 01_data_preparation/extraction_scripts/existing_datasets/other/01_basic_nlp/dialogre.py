import json
import os

# ================= 配置区域 =================
# 在这里修改你的输入和输出文件路径
INPUT_FILE = 'dialogre_20.jsonl'  # 输入文件的路径 (假设每行是一个json)
OUTPUT_FILE = 'dialogre_test.jsonl'  # 输出文件的路径


# ===========================================

def format_dialogue(dialogue_list):
    """
    将对话列表拼接成清晰的文本格式
    """
    return "\n".join(dialogue_list)


def format_relations(relations_list):
    """
    将关系列表转化为模型需要生成的文本答案。
    格式示例:
    Subject: Chandler, Relation: per:girl/boyfriend, Object: Speaker 1
    """
    lines = []
    for rel in relations_list:
        # 提取主体(x), 客体(y) 和 关系类型(r)
        # 注意：源数据中 'r' 是一个列表，通常取第一个元素
        subject_ent = rel.get('x', '')
        object_ent = rel.get('y', '')
        relation_type = rel.get('r', ['unknown'])[0]

        # 格式化为一行文本
        line = f"Subject: {subject_ent}, Relation: {relation_type}, Object: {object_ent}"
        lines.append(line)

    return "\n".join(lines)


def process_dataset(input_path, output_path):
    print(f"正在处理数据: {input_path} ...")

    processed_count = 0

    try:
        with open(input_path, 'r', encoding='utf-8') as fin, \
                open(output_path, 'w', encoding='utf-8') as fout:

            for index, line in enumerate(fin):
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    print(f"警告: 第 {index + 1} 行不是有效的 JSON，已跳过。")
                    continue

                # 1. 构建 ID (如果源数据没有id，使用行号确保唯一性)
                # 这里的 'dialogue_id' 是为了方便追踪，也可以用 uuid
                unique_id = f"train_{index}"

                # 2. 构建 Question (输入)
                # 包含任务指令和对话上下文
                dialogue_text = format_dialogue(data.get('dialogue', []))
                question = (
                    "Below is a dialogue text. Please extract the relationships between the entities "
                    "mentioned in the dialogue. List each relationship in the format: "
                    "'Subject: [Entity1], Relation: [RelationType], Object: [Entity2]'.\n\n"
                    "Dialogue:\n"
                    f"{dialogue_text}"
                )

                # 3. 构建 Answer (输出)
                # 从 relations 字段提取参考答案
                answer = format_relations(data.get('relations', []))

                # 4. 组装最终对象
                output_obj = {
                    "id": unique_id,
                    "question": question,
                    "answer": answer
                }

                # 写入输出文件
                fout.write(json.dumps(output_obj, ensure_ascii=False) + '\n')
                processed_count += 1

        print(f"处理完成！")
        print(f"共转换 {processed_count} 条数据。")
        print(f"结果已保存至: {output_path}")

    except FileNotFoundError:
        print(f"错误: 找不到输入文件 '{input_path}'，请检查路径配置。")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    # 建议先创建一个包含你提供的那条样例的 dummy 文件来测试
    # 比如创建一个名为 input_dataset.jsonl 的文件，把你的样例粘贴进去
    process_dataset(INPUT_FILE, OUTPUT_FILE)