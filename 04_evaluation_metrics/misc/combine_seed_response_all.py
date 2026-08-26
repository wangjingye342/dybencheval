import os
import json


def process_jsonl_files(source_dir, target_dir):
    # 1. 确保目标目录存在
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
        print(f"已创建目标目录: {target_dir}")

    # 2. 获取源目录下所有文件
    files = os.listdir(source_dir)
    jsonl_files = [f for f in files if f.endswith('.jsonl')]

    if not jsonl_files:
        print("源目录中未找到 .jsonl 文件。")
        return

    print(f"找到 {len(jsonl_files)} 个 jsonl 文件，开始处理...")

    # 3. 遍历处理每个文件
    for filename in jsonl_files:
        source_path = os.path.join(source_dir, filename)
        target_path = os.path.join(target_dir, filename)

        try:
            with open(source_path, 'r', encoding='utf-8') as f_in, \
                    open(target_path, 'w', encoding='utf-8') as f_out:

                # 使用 enumerate 获取行号 (index)，从 0 开始
                for index, line in enumerate(f_in):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 4. 构建包含 id 的新字典，确保 id 在第一位
                        # 方法：先创建一个只有 id 的字典，然后把原数据更新进去
                        new_data = {"id": index}
                        new_data.update(data)

                        # 写入目标文件，ensure_ascii=False 保证中文不乱码
                        f_out.write(json.dumps(new_data, ensure_ascii=False) + "\n")

                    except json.JSONDecodeError as e:
                        print(f"文件 {filename} 第 {index} 行解析错误: {e}")

            print(f"处理完成: {filename} -> 保存在目标目录")

        except Exception as e:
            print(f"处理文件 {filename} 时发生错误: {e}")

    print("-" * 30)
    print("所有文件处理完毕。")


if __name__ == "__main__":
    # 配置路径
    source_directory = "./external/metrics/1/qwen8b-40"
    target_directory = "./external/metrics/00/tmp_gemini"

    process_jsonl_files(source_directory, target_directory)