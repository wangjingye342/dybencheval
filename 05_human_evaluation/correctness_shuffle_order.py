import random
import os


def shuffle_jsonl_overwrite(file_path):
    # 1. 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：找不到文件 -> {file_path}")
        return

    print(f"正在读取文件: {file_path}")

    try:
        # 2. 读取所有行到内存
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        line_count = len(lines)
        if line_count == 0:
            print("文件为空，无需打乱。")
            return

        print(f"共读取 {line_count} 行，正在打乱顺序...")

        # 3. 随机打乱列表顺序 (原地打乱)
        random.shuffle(lines)

        # 4. 覆盖写入回原文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

        print("成功！文件顺序已打乱并保存回原路径。")

    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    # 指定你的文件绝对路径
    TARGET_FILE = "D:/STUDY/2026-project1/project1/main_work/测评_人工检验/正确性120.jsonl"

    shuffle_jsonl_overwrite(TARGET_FILE)