import os
import json
import tqdm

# =================配置区域=================
# 输入根目录
SOURCE_DIR = "./data/raw_datasets/temporary_augmentation"

# 输出文件路径 (你可以修改为你想要保存的位置)
OUTPUT_FILE = "./external/model_runs/constructed_prompts_temporary_augmentation.jsonl"

# Prompt 模板
PROMPT_TEMPLATE = """# Role
You are an Advanced Data Augmentation Architect. Your goal is to generate a high-quality "Parallel Test Case" based on a provided SEED DATA entry.

# Objective
The SEED DATA is likely contaminated (memorized by models). You must create a **new** problem-answer pair that tests the *exact same* underlying skill or logic as the seed, but looks different enough to bypass memorization.

# 1. Degrees of Freedom (Where you MUST be creative)
You are granted freedom to modify the following elements to ensure the new data is fresh and diverse:
* **Context Re-skinning:** Completely change the story or setting. (e.g., If the seed is about "calculating trajectory of a missile", you can change it to "calculating the path of a magic spell" or "robot arm movement", provided the math remains applicable).
* **Variable Perturbation:** You may alter specific numbers, entity names, or attributes, as long as the change does not break the logic. (e.g., Change "3 red balls" to "5 blue crystals", adjusting the answer accordingly).
* **Input Format:** You may slightly vary how the information is presented (e.g., changing a list to a paragraph description), provided it remains clear.

# 2. Strict Anchors (Where you MUST NOT deviate)
Despite the freedom above, you must strictly adhere to the seed's core essence:
* **Core Logic Invariance:** The specific reasoning step, algorithm, or knowledge point required to solve the problem must remain identical. Do not simplify or complicate the underlying logic.
* **Difficulty Anchoring:** The cognitive load required to solve the new problem must match the seed. Do not turn a 2-step reasoning problem into a 5-step one, or vice versa.
* **Category Consistency:** If the seed is a "coding task", the output must be code. If it is "information extraction", the output must be extraction.

# 3. Quality Assurance
* The new Question must be unambiguous.
* The new Answer must be rigorously derived from the new Question.
* **Avoid Hallucination:** Ensure the new scenario is logically sound.

# Output Format
Output ONLY a single valid JSON object (compact JSONL format).
The structure must match the seed keys.

# Input Seed Data
{{SEED_DATA}}

# Action
Based on the guidelines above, generate the new JSONL line now. **Double-check that your generated Output is the mathematically/logically correct solution to your generated Input.**"""


# =================主逻辑=================

def process_datasets():
    # 确保输出目录存在
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    total_files = 0
    jsonl_files = []

    # 1. 扫描所有 jsonl 文件
    print(f"正在扫描目录: {SOURCE_DIR} ...")
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith(".jsonl"):
                jsonl_files.append(os.path.join(root, file))

    print(f"找到 {len(jsonl_files)} 个 JSONL 文件。开始处理...")

    count = 0
    # 打开输出文件准备写入
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        # 遍历每个文件
        for file_path in jsonl_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f_in:
                    # 读取每一行种子数据
                    for line_num, line in enumerate(f_in):
                        line = line.strip()
                        if not line:
                            continue

                        try:
                            # 解析原始种子数据
                            seed_data = json.loads(line)

                            # 将种子数据转为字符串 (ensure_ascii=False 保证中文正常显示)
                            seed_data_str = json.dumps(seed_data, ensure_ascii=False)

                            # 构造最终 Prompt
                            full_prompt = PROMPT_TEMPLATE.replace("{{SEED_DATA}}", seed_data_str)

                            # 构造输出对象
                            # 我们保存源文件路径、原始数据以及构造好的prompt
                            output_obj = {
                                "source_file": file_path,
                                "source_line_index": line_num,
                                "constructed_prompt": full_prompt
                            }

                            # 写入结果文件
                            f_out.write(json.dumps(output_obj, ensure_ascii=False) + "\n")
                            count += 1

                        except json.JSONDecodeError:
                            print(f"[Warning] 无法解析 JSON (文件: {file_path}, 行: {line_num})")
                            continue

            except Exception as e:
                print(f"[Error] 读取文件出错: {file_path}, 错误: {e}")

    print(f"\n处理完成！")
    print(f"共生成 {count} 条 Prompt。")
    print(f"结果已保存至: {OUTPUT_FILE}")


if __name__ == "__main__":
    process_datasets()