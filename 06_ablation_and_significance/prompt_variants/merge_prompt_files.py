import os
import json
import glob

# ================= 配置区域 =================

# 你的“后补实验”根目录路径
ROOT_DIR = "./external/ablation"

# 需要处理的子目录列表 (根据你图中的目录名)
TARGET_SUBDIRS = [
    "prompts_3",
    "prompts_5",
    "prompts_7",
    "prompts_onlydomain",
    "prompts_onlyself",
    "prompts_onlytask"
]

# 【关键】定义文件读取的严格顺序
# 只有按照固定顺序读取，才能保证合并后的 ID 在不同文件夹的结果中是一一对应的
FILE_ORDER_KEYWORDS = [
    "Humanity_Code_Generation",  # 1. 人文代码
    "Other_Professional_Knowledge",  # 2. 其他专业知识
    "SocialScience_Role_Play",  # 3. 社科角色扮演
    "STEM_Reasoning"  # 4. 理科推理
]


# ================= 核心逻辑 =================

def process_directories():
    print(f"开始处理目录，根路径: {ROOT_DIR}")

    for subdir_name in TARGET_SUBDIRS:
        subdir_path = os.path.join(ROOT_DIR, subdir_name)
        output_file = os.path.join(ROOT_DIR, f"{subdir_name}.jsonl")

        if not os.path.exists(subdir_path):
            print(f"[跳过] 找不到目录: {subdir_path}")
            continue

        print(f"正在处理: {subdir_name} ...")

        merged_data = []
        global_id = 0  # 每个数据集独立重置 ID

        # 按照强制顺序遍历文件
        for keyword in FILE_ORDER_KEYWORDS:
            # 查找匹配该关键字的文件
            pattern = os.path.join(subdir_path, f"*{keyword}*.jsonl")
            found_files = glob.glob(pattern)

            if not found_files:
                print(f"  [警告] 在 {subdir_name} 中未找到包含 '{keyword}' 的文件")
                continue

            # 理论上每个关键词只对应一个文件，取第一个
            target_file = found_files[0]

            with open(target_file, 'r', encoding='utf-8') as f_in:
                lines = f_in.readlines()
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        original_json = json.loads(line)

                        # 构造新的有序字典，确保 id 在第一位
                        new_record = {"id": global_id}
                        # 将原始数据合并进去
                        new_record.update(original_json)

                        merged_data.append(new_record)
                        global_id += 1

                    except json.JSONDecodeError:
                        print(f"  [错误] 无法解析 JSON: {target_file}")

        # 将合并后的数据写入对应的输出文件
        with open(output_file, 'w', encoding='utf-8') as f_out:
            for record in merged_data:
                f_out.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"  -> 已生成: {output_file} (共 {len(merged_data)} 条数据)")

    print("\n所有任务处理完成。")


if __name__ == "__main__":
    process_directories()