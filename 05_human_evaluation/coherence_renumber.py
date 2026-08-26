import json
import os


def reindex_jsonl(input_file, output_file):
    """
    读取 jsonl 文件，并将每行的 'line_number' 字段更新为实际行号。
    """
    print(f"正在处理文件: {input_file} ...")

    try:
        # 同时打开输入和输出文件
        with open(input_file, 'r', encoding='utf-8') as f_in, \
                open(output_file, 'w', encoding='utf-8') as f_out:

            # 使用 enumerate 获取行号，start=1 表示从第 1 行开始计数
            for index, line in enumerate(f_in, start=1):
                line = line.strip()
                if not line:
                    continue  # 跳过空行

                try:
                    # 1. 解析 JSON
                    data = json.loads(line)

                    # 2. 修改或添加 line_number 字段
                    data['line_number'] = index

                    # 3. 写入新文件 (ensure_ascii=False 保证中文不乱码)
                    f_out.write(json.dumps(data, ensure_ascii=False) + '\n')

                except json.JSONDecodeError:
                    print(f"警告: 第 {index} 行不是有效的 JSON 数据，已跳过。")

        print(f"处理完成！新文件已保存为: {output_file}")
        print(f"共处理了 {index} 行数据。")

    except FileNotFoundError:
        print(f"错误: 找不到文件 '{input_file}'")
    except Exception as e:
        print(f"发生未知错误: {e}")


# --- 使用示例 ---
if __name__ == "__main__":
    # 在这里修改你的文件名
    input_path = 'sample2_all.jsonl'  # 源文件名
    output_path = 'sample2_all_final.jsonl'  # 输出文件名

    # 为了演示，如果输入文件不存在，我们先创建一个伪造的
    if not os.path.exists(input_path):
        print("未找到源文件，正在生成测试数据...")
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write('{"text": "第一条数据", "line_number": 999}\n')
            f.write('{"text": "第二条数据"}\n')  # 这一行原本没有 line_number
            f.write('{"text": "第三条数据", "line_number": 0}\n')

    # 运行处理函数
    reindex_jsonl(input_path, output_path)