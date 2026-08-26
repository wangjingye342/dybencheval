import json
import os

# ================= 配置区域 =================

# 输入目录 (上一轮生成的结果，包含 'response' 字段)
INPUT_DIR = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/all_results"

# 输出目录 (存放用于评测 Correctness 的 prompt)
OUTPUT_DIR = "./prompts_correctness"


# ================= 1. 定义 Prompt 模板 =================

def generate_correctness_prompt(generated_content):
    """
    针对单条生成内容进行 Correctness (正确性) 评分。
    核心逻辑：无需对比 Seed，而是检查生成内容内部的逻辑自洽性、事实正确性以及是否解决了其自身提出的问题。
    """
    return f"""You are an expert Data Quality Assurance Specialist. Your task is to verify the **Correctness** of the "Generated Content" using a rigorous Chain-of-Thought process.

**Input Data (Target for Evaluation):**
\"\"\"
{generated_content}
\"\"\"

**Evaluation Protocol:**

**CRITICAL GUARDRAIL 1: SELF-CONTAINED VERIFICATION**
* You do NOT have access to a "ground truth" reference.
* You must evaluate the content based on **Internal Consistency**, **Logical Validity**, and **General Domain Knowledge** (e.g., Math rules, Python syntax, Historical facts).
* If the content generates a question and then answers it, verify if the answer is actually correct for *that specific question*.

**CRITICAL GUARDRAIL 2: FOCUS**
* **IGNORE Style:** Do not judge the writing flair or tone.
* **FOCUS ONLY:** Is the solution/answer objectively correct relative to the problem/question presented in the text?

**Step 1: Data Parsing & Extraction (Crucial)**
Analyze the **Input Data** to structure the evaluation. You must handle two scenarios:
* **Scenario A (Explicit Structure):** If the text clearly separates a "Question/Instruction" and an "Answer/Reasoning" (e.g., standard Q&A format), identify them directly.
* **Scenario B (Unstructured/Narrative):** If no explicit structure exists, you must **EXTRACT** the implied Q&A pair:
    * *Extracted Question:* What is the core problem, math equation, or coding task presented or implied in the text?
    * *Extracted Answer:* What is the specific solution, result, or code provided in the text?

**Step 2: Autonomous Dimension Generation & Analysis**
Based on the content type (e.g., Math, Code, History, Logic), **self-define** 3 specific dimensions to judge the correctness.
* *Action:* Define the dimension name, then evaluate the Extracted Answer against the Extracted Question.

**Step 3: Synthesis**
Synthesize the results from your 3 self-defined dimensions.
* **Result 1 (Pass):** The answer is objectively correct and logically sound.
* **Result 0 (Fail):** The answer is factually wrong, contains calculation errors, hallucinations, or code that clearly won't run.

**Response Template:**
### Reasoning Process:
* **Phase 1: Extraction**
    * *Target Question:* [The question identified or extracted from the text]
    * *Target Answer:* [The solution identified or extracted from the text]
* **Phase 2: Multi-Dimensional Analysis**
    * *Dimension 1 [[Self-Defined Name]]:* [Verification details...]
    * *Dimension 2 [[Self-Defined Name]]:* [Verification details...]
    * *Dimension 3 [[Self-Defined Name]]:* [Verification details...]
* **Phase 3: Synthesis**
    * *Summary:* [Is the answer correct?]

###FINAL_RESULT: [[x]]
"""


# ================= 2. 主处理逻辑 =================

def process_all_datasets():
    # 1. 确保输出目录存在
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"创建输出目录: {OUTPUT_DIR}")
        except OSError as e:
            print(f"创建目录失败: {e}")
            return

    # 2. 获取目录下所有 .jsonl 文件
    try:
        files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.jsonl')]
    except FileNotFoundError:
        print(f"错误: 找不到输入目录 {INPUT_DIR}")
        return

    if not files:
        print(f"在目录 '{INPUT_DIR}' 中没有找到 .jsonl 文件。")
        return

    print(f"检测到 {len(files)} 个 JSONL 数据集文件，开始处理...\n")

    # 3. 循环处理每个文件
    for idx, filename in enumerate(files):
        input_path = os.path.join(INPUT_DIR, filename)

        # 构建输出文件名： filename.jsonl -> filename_prompt_correctness.jsonl
        filename_no_ext = os.path.splitext(filename)[0]
        output_filename = f"{filename_no_ext}_prompt_correctness.jsonl"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"[{idx + 1}/{len(files)}] 正在处理: {filename} -> {output_filename}")

        count = 0
        success_count = 0
        skipped_count = 0

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
                        # 这里我们只关心 'response'，这是大模型生成的需要被验证的内容
                        generated_content = data.get("response", "")
                        record_id = data.get("id")

                        # 校验数据有效性
                        if not generated_content:
                            skipped_count += 1
                            continue

                        # 生成 Correctness Prompt (Level 3)
                        prompt_correctness = generate_correctness_prompt(generated_content)

                        # 构造输出对象 (保留原始元数据以便追踪)
                        out_record = {
                            "id": record_id,
                            "target_task": data.get("target_task", ""),
                            "target_scenario": data.get("target_scenario", ""),
                            "original_response": generated_content,  # 被评测的内容
                            "prompt": prompt_correctness  # 评测用的 Prompt
                        }

                        # 写入 JSONL
                        fout.write(json.dumps(out_record, ensure_ascii=False) + "\n")
                        success_count += 1
                        count += 1

                    except json.JSONDecodeError:
                        print(f"  - 错误: 文件 {filename} 中某行 JSON 格式无效，跳过。")
                        continue

            print(f"   完成。生成: {success_count} 条 | 跳过(空内容): {skipped_count} 条")

        except Exception as e:
            print(f"   处理文件 {filename} 时发生未知错误: {e}")

    print("-" * 30)
    print(f"所有任务处理完成！结果保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_all_datasets()