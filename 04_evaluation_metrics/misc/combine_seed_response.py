import json
import os


def load_metadata(file_path):
    """
    读取元数据文件，构建 id -> {scenario, task} 的映射字典
    """
    mapping = {}
    print(f"正在读取元数据: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # 提取需要的字段
                    if 'id' in data:
                        mapping[data['id']] = {
                            'scenario': data.get('scenario', ''),
                            'task': data.get('task', '')
                        }
                except json.JSONDecodeError:
                    print(f"警告: 无法解析行: {line[:50]}...")
    except FileNotFoundError:
        print(f"错误: 找不到文件 {file_path}")
        return None

    print(f"元数据加载完成，共包含 {len(mapping)} 条记录。")
    return mapping


def insert_fields_at_position(original_dict, new_fields):
    """
    创建一个新的字典，将 new_fields 插入到 original_dict 的第2和第3位。
    Python 3.7+ 字典保持插入顺序。
    """
    new_dict = {}
    keys = list(original_dict.keys())

    # 1. 插入原字典的第1个字段 (通常是 id)
    if keys:
        first_key = keys[0]
        new_dict[first_key] = original_dict[first_key]

    # 2. 插入新的字段 (scenario 和 task)
    for k, v in new_fields.items():
        new_dict[k] = v

    # 3. 插入原字典剩余的字段
    for k in keys[1:]:
        new_dict[k] = original_dict[k]

    return new_dict


def process_datasets(meta_mapping, input_dir, output_dir):
    """
    处理输入目录下的所有 jsonl 文件并保存
    """
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"创建输出目录: {output_dir}")

    # 获取目录下所有文件
    files = [f for f in os.listdir(input_dir) if f.endswith('.jsonl')]

    if not files:
        print(f"在 {input_dir} 中没有找到 .jsonl 文件。")
        return

    print(f"开始处理 {len(files)} 个文件...")

    for filename in files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        processed_count = 0
        match_count = 0

        with open(input_path, 'r', encoding='utf-8') as f_in, \
                open(output_path, 'w', encoding='utf-8') as f_out:

            for line in f_in:
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    processed_count += 1

                    # 获取当前记录的 ID
                    curr_id = record.get('id')

                    # 检查是否有对应的元数据
                    if curr_id in meta_mapping:
                        match_count += 1
                        fields_to_add = meta_mapping[curr_id]

                        # 执行插入操作 (插入到第2、3位)
                        new_record = insert_fields_at_position(record, fields_to_add)

                        # 写入新记录
                        f_out.write(json.dumps(new_record, ensure_ascii=False) + '\n')
                    else:
                        # 如果没有匹配到ID，保持原样写入（或者你可以选择跳过）
                        f_out.write(line + '\n')

                except json.JSONDecodeError:
                    print(f"文件 {filename} 中存在无法解析的行，已跳过。")

        print(f"完成: {filename} (匹配数/总数: {match_count}/{processed_count}) -> 保存至输出目录")


def main():
    # 路径配置
    meta_file_path = "D:/STUDY/2026-project1/project1/main_work/计算指标/00/溯源后/Final_standard.jsonl"
    input_directory = "D:/STUDY/2026-project1/project1/main_work/计算指标/00/seed&response"
    output_directory = "D:/STUDY/2026-project1/project1/main_work/计算指标/00/s&r+溯源"

    # 1. 加载元数据
    meta_data = load_metadata(meta_file_path)

    if meta_data:
        # 2. 处理数据集
        process_datasets(meta_data, input_directory, output_directory)
        print("\n所有任务已完成。")


if __name__ == "__main__":
    main()