import shutil
from pathlib import Path


def extract_specific_files(src_dir: str, dst_dir: str, file_suffix: str):
    """
    从源目录递归查找特定后缀的文件，并将其复制到目标目录，
    同时保持原有的目录结构。

    :param src_dir: 源目录路径
    :param dst_dir: 目标目录路径
    :param file_suffix: 文件后缀 (例如 "_test.jsonl")
    """
    source_path = Path(src_dir)
    dest_path = Path(dst_dir)

    # 1. 检查源目录是否存在
    if not source_path.exists():
        print(f"错误: 源目录 '{src_dir}' 不存在。")
        return

    print(f"开始扫描: {src_dir}")
    print(f"目标目录: {dst_dir}")
    print("-" * 30)

    count = 0

    # 2. rglob('*' + suffix) 递归查找匹配的文件
    # 注意: 如果需要严格匹配结尾，可以使用字符串判断
    for file_path in source_path.rglob("*"):

        # 3. 筛选文件：是文件 且 以指定后缀结尾
        if file_path.is_file() and file_path.name.endswith(file_suffix):
            # 4. 计算相对路径以保持结构
            # 例如: src/data/a/1.jsonl -> relative: data/a/1.jsonl
            relative_path = file_path.relative_to(source_path)

            # 5. 拼接目标完整路径
            target_file_path = dest_path / relative_path

            # 6. 创建目标文件的父目录（如果不存在）
            target_file_path.parent.mkdir(parents=True, exist_ok=True)

            # 7. 复制文件 (copy2 保留文件元数据如时间戳)
            shutil.copy2(file_path, target_file_path)

            print(f"已复制: {relative_path}")
            count += 1

    print("-" * 30)
    print(f"处理完成! 共复制了 {count} 个文件。")


# --- 使用示例 ---
if __name__ == "__main__":
    # 请在这里修改你的实际路径
    # 建议使用绝对路径，或者确保相对路径是正确的
    SOURCE_DIRECTORY = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/评估指标/计算size/所有数据集"  # 输入目录
    TARGET_DIRECTORY = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/评估指标/计算size/final数据集/DyBenchEval"  # 输出目录

    # 执行提取
    extract_specific_files(SOURCE_DIRECTORY, TARGET_DIRECTORY, "_test.jsonl")