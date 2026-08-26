import json
import os


# -----------------------------------------------------------------------------
# 1. 定义 Prompt 模板 (只保留 Level 3)
# -----------------------------------------------------------------------------

def generate_level_3_prompt(seed, rewrite):
    """
    Level 3: Expert Data Quality Assurance Specialist (Independent Verification & Dynamic Dimensions)
    """
    return f"""You are an expert Data Quality Assurance Specialist. Your task is to verify the **Correctness** of the "Answer" within the modified data using a rigorous Chain-of-Thought process.

**Input Data:**
Original Data (Reference Only):
\"\"\"
{seed}
\"\"\"

Modified Data (Target for Evaluation):
\"\"\"
{rewrite}
\"\"\"

**Evaluation Protocol:**

**CRITICAL GUARDRAIL 1: INDEPENDENCE**
* **IGNORE the Original Data's content for verification.** The Modified Data may have changed numbers, logic, or facts.
* **Evaluate the Modified Data as a STANDALONE entity.** You must recalculate or re-verify the answer strictly based on the information provided in the "Modified Data".
* *Example:* If Original says "1+1=2" and Modified says "1+2=3", the Modified data is **CORRECT** (Pass). Do not compare it to the Original.

**CRITICAL GUARDRAIL 2: FOCUS**
* **IGNORE Question Quality:** Do not judge if the question is simple or weird.
* **IGNORE Style:** Do not judge the writing quality.
* **FOCUS ONLY:** Is the Answer objectively correct relative to the Question *in the Modified Data*?

**Step 1: Data Parsing & Extraction (From Modified Data Only)**
Analyze the **Modified Data** to lock in the target for evaluation:
* **Scenario A (Explicit Q&A):** If the text clearly separates a Question and an Answer, identify them directly.
* **Scenario B (Unstructured/Narrative):** If no explicit Q&A structure exists, you must **EXTRACT** a valid pair from the content:
    * *Extracted Question:* What is the core problem/topic presented in the **Modified Data**?
    * *Extracted Answer:* What is the specific solution provided in the **Modified Data**?

**Step 2: Autonomous Dimension Generation & Analysis**
Based on the content type of the **Modified Data**, **self-define** 3 specific dimensions to judge the correctness of the Answer.
* *Action:* Define the dimension name (e.g., "Math Logic", "Code Syntax", "Historical Fact", "Internal Consistency"), then evaluate the Answer against it using **only** the Modified Data's context.

**Step 3: Synthesis**
Synthesize the results from your 3 self-defined dimensions.
* **Result 1 (Pass):** The answer is objectively correct and logically sound based on the new data's premises.
* **Result 0 (Fail):** The answer is factually wrong, contains calculation errors, or is logically invalid within the modified text.

**Response Template:**
### Reasoning Process:
* **Phase 1: Extraction (Based on Modified Data)**
    * *Target Question:* [Extracted Question]
    * *Target Answer:* [Extracted Answer]
* **Phase 2: Multi-Dimensional Analysis**
    * *Dimension 1 [[Self-Defined Name]]:* [Detailed Check based on new context...]
    * *Dimension 2 [[Self-Defined Name]]:* [Detailed Check based on new context...]
    * *Dimension 3 [[Self-Defined Name]]:* [Detailed Check based on new context...]
* **Phase 3: Synthesis**
    * *Summary:* [Is the answer correct according to the modified question?]

###FINAL_RESULT: [[x]]
"""


# -----------------------------------------------------------------------------
# 2. 主处理逻辑
# -----------------------------------------------------------------------------

def process_all_datasets():
    # --- 配置区域 ---
    # 输入目录：设置为 '.' 表示当前目录，或者是具体的文件夹路径，例如 './raw_data'
    input_directory = "D:/STUDY/2026-project1/project1/main_work/计算指标/1/gemini"

    # 输出目录 (Prompts 存放位置)
    output_base_dir = "prompts-gemini"
    # ----------------

    # 1. 确保输出目录存在
    if not os.path.exists(output_base_dir):
        try:
            os.makedirs(output_base_dir)
            print(f"创建输出目录: {output_base_dir}")
        except OSError as e:
            print(f"创建目录失败: {e}")
            return

    # 2. 获取目录下所有 .jsonl 文件
    try:
        all_files = os.listdir(input_directory)
        jsonl_files = [f for f in all_files if
                       f.endswith('.jsonl') and not f.endswith('_prompt_level3.jsonl')]  # 排除掉已经是结果的文件，防止死循环
    except FileNotFoundError:
        print(f"错误: 找不到输入目录 {input_directory}")
        return

    if not jsonl_files:
        print(f"在目录 '{input_directory}' 中没有找到 .jsonl 文件。")
        return

    print(f"检测到 {len(jsonl_files)} 个 JSONL 数据集文件，开始处理...\n")

    # 3. 循环处理每个文件
    for idx, filename in enumerate(jsonl_files):
        input_path = os.path.join(input_directory, filename)

        # 构建输出文件名： filename.jsonl -> filename_prompt_level3.jsonl
        filename_no_ext = os.path.splitext(filename)[0]
        output_filename = f"{filename_no_ext}_prompt_level3.jsonl"
        output_path = os.path.join(output_base_dir, output_filename)

        print(f"[{idx + 1}/{len(jsonl_files)}] 正在处理: {filename} -> {output_filename}")

        count = 0
        success_count = 0

        try:
            with open(input_path, 'r', encoding='utf-8') as fin, \
                    open(output_path, 'w', encoding='utf-8') as fout:

                for line in fin:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        # 提取关键字段
                        seed_text = data.get("seed_text", "")
                        response_text = data.get("response_text", "")
                        # 优先使用原数据ID，如果没有则使用计数器
                        record_id = data.get("id", count)
                        model_name = data.get("model", "")

                        if not seed_text or not response_text:
                            # 默默跳过缺失数据，或者取消注释下方打印警告
                            # print(f"  - 警告: id={record_id} 数据缺失 seed/response，跳过。")
                            continue

                        # 只生成 Level 3 Prompt
                        prompt_l3 = generate_level_3_prompt(seed_text, response_text)

                        # 构造输出字典
                        out_l3 = {
                            "id": record_id,
                            "model": model_name,
                            "seed_text": seed_text,
                            "response_text": response_text,
                            "prompt": prompt_l3
                        }

                        # 写入 JSONL
                        fout.write(json.dumps(out_l3, ensure_ascii=False) + "\n")
                        success_count += 1
                        count += 1

                    except json.JSONDecodeError:
                        print(f"  - 错误: 文件 {filename} 中某行 JSON 格式无效，跳过。")
                        continue

            print(f"   完成。成功生成 {success_count} 条 Level 3 数据。")

        except Exception as e:
            print(f"   处理文件 {filename} 时发生未知错误: {e}")

    print("-" * 30)
    print(f"所有任务处理完成！结果保存在: {output_base_dir}")


if __name__ == "__main__":
    process_all_datasets()