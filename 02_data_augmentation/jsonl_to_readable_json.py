import json


def jsonl_to_pretty_json(input_file, output_file):
    data_list = []

    # 1. 读取 JSONL 文件
    print(f"正在读取 {input_file}...")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line in f:
                # 跳过空行
                if line.strip():
                    data_list.append(json.loads(line))
    except FileNotFoundError:
        print("错误：找不到输入文件。")
        return

    # 2. 写入格式化的 JSON 文件
    print(f"正在转换并写入 {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        # indent=4 负责缩进，ensure_ascii=False 保证中文正常显示
        json.dump(data_list, f, indent=4, ensure_ascii=False)

    print("完成！")


# 使用示例
if __name__ == "__main__":
    # 假设你的文件名为 data.jsonl
    jsonl_to_pretty_json('D:/STUDY/2026-project1/project1/main_work/测评_人工检验/正确性120.jsonl', 'D:/STUDY/2026-project1/project1/main_work/测评_人工检验/正确性120_readable.json')