import random
import os


def sample_from_jsonl(input_file, output_file, sample_size=20):
    """
    从 jsonl 文件中随机抽取指定数量的行并保存。
    """
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"错误: 找不到文件 {input_file}")
        return

    try:
        # 1. 读取所有数据
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        print(f"源文件共有 {total_lines} 条数据。")

        # 2. 随机抽取
        # 如果源文件行数少于抽取数量，则抽取所有行
        if total_lines <= sample_size:
            print(f"注意: 数据量少于 {sample_size} 条，将复制所有数据。")
            selected_lines = lines
        else:
            selected_lines = random.sample(lines, sample_size)
            print(f"已随机抽取 {sample_size} 条数据。")

        # 3. 写入新文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(selected_lines)

        print(f"成功保存至: {output_file}")

    except Exception as e:
        print(f"发生错误: {e}")


# --- 使用配置 ---
source_path = './external/model_runs/constructed_prompts.jsonl'  # 这里修改你的源文件名
target_path = 'apiask_sample_5.jsonl'  # 输出文件名

# 执行函数
if __name__ == '__main__':
    sample_from_jsonl(source_path, target_path, 5)