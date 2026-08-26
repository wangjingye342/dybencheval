import json
import os


# -----------------------------------------------------------------------------
# 1. 定义新的 Prompt 模板
# -----------------------------------------------------------------------------

def generate_level_1_prompt(seed, rewrite):
    """
    Level 1: Strict Data Validator (Direct Boolean Output)
    """
    return f"""You are a strict data validator. Your task is to evaluate a "Modified Data" entry based on an "Original Data" entry.

**Task Rules:**
1. Analyze the input.
2. If the data contains a clear Question and Answer structure: Check if the Answer in the "Modified Data" is correct.
3. If there is no clear Question/Answer structure: Check if the "Modified Data" is logically coherent and sensible.
4. **Constraint:** You must NOT output any reasoning, explanation, or thinking process. You must ONLY output the final result tag.

**Evaluation Criteria:**
- If the modified data is correct/logical: Result is 1.
- If the modified data is incorrect/illogical: Result is 0.

**Input Data:**
Original Data:
\"\"\"
{seed}
\"\"\"

Modified Data:
\"\"\"
{rewrite}
\"\"\"

**Output Format:**
###FINAL_RESULT: [[x]]
"""


def generate_level_2_prompt(seed, rewrite):
    """
    Level 2: Intelligent Data Auditor (Step-by-Step + Boolean)
    """
    return f"""You are an intelligent data auditor. Your goal is to evaluate the quality of a "Modified Data" entry derived from an "Original Data" entry.

**Instructions:**
1.  **Analyze the Structure:** First, determine if the data consists of a distinct Question and Answer or if it is unstructured text.
2.  **Verify Logic:**
    * If Q&A: Verify if the provided answer is factually correct and answers the specific question asked.
    * If Unstructured: Verify if the text is logically consistent and free of contradictions.
3.  **Think Step-by-Step:** You must write out your reasoning process entirely before deciding. Compare the "Modified Data" against the "Original Data" to ensure no meaning was corrupted during modification.
4.  **Final Verdict:** Conclude with the required boolean tag.

**Input Data:**
Original Data:
\"\"\"
{seed}
\"\"\"

Modified Data:
\"\"\"
{rewrite}
\"\"\"

**Output Format:**
<Analysis>
[Write your step-by-step reasoning here...]
</Analysis>
###FINAL_RESULT: [[x]]
"""


def generate_level_3_prompt(seed, rewrite):
    """
    Level 3: Expert Data Quality Assurance Specialist (Independent Verification & Dynamic Dimensions)
    修改说明：
    1. 独立性约束 (Independence): 明确要求模型仅基于 Modified Data 进行判断，忽略 Original Data 的具体数值/事实（Original 仅作参考，不作标准）。
    2. 自主维度 (Self-Defined Dimensions): 保持模型自行定义3个维度的逻辑。
    3. 强制提取 (Extraction): 保持对非结构化数据的拆解逻辑。
    4. 评估核心: 验证新生成的答案在新的上下文中是否成立。
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

def process_prompts():
    # --- 配置区域 ---
    # 输入文件名
    input_name = "correctness_120_seed_response_extracted.jsonl"

    # 输入路径 (根据你的环境设置)
    input_path = "./" + input_name

    # 输出目录 (Prompts 存放位置)
    output_base_dir = "backup/prompts"
    # ----------------

    # 确保输出目录存在
    if not os.path.exists(output_base_dir):
        try:
            os.makedirs(output_base_dir)
            print(f"创建输出目录: {output_base_dir}")
        except OSError as e:
            print(f"创建目录失败: {e}")

    # 定义三个级别的输出文件路径
    output_path_l1 = os.path.join(output_base_dir, input_name + "_prompt_level1.jsonl")
    output_path_l2 = os.path.join(output_base_dir, input_name + "_prompt_level2.jsonl")
    output_path_l3 = os.path.join(output_base_dir, input_name + "_prompt_level3.jsonl")

    print(f"正在读取输入文件: {input_path}")

    count = 0

    try:
        with open(input_path, 'r', encoding='utf-8') as fin, \
                open(output_path_l1, 'w', encoding='utf-8') as f_l1, \
                open(output_path_l2, 'w', encoding='utf-8') as f_l2, \
                open(output_path_l3, 'w', encoding='utf-8') as f_l3:

            for line in fin:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)

                    # 提取关键字段
                    seed_text = data.get("seed_text", "")
                    response_text = data.get("response_text", "")
                    record_id = data.get("id", count)
                    model_name = data.get("model", "")  # 提取 model 字段

                    if not seed_text or not response_text:
                        print(f"警告: 第 {count} 行数据缺失 seed_text 或 response_text，跳过。")
                        continue

                    # 生成三个等级的 Prompt
                    prompt_l1 = generate_level_1_prompt(seed_text, response_text)
                    prompt_l2 = generate_level_2_prompt(seed_text, response_text)
                    prompt_l3 = generate_level_3_prompt(seed_text, response_text)

                    # 构造输出字典，确保 model 在第二位 (Python 3.7+ 字典保持插入顺序)
                    out_l1 = {
                        "id": record_id,
                        "model": model_name,
                        "seed_text": seed_text,
                        "response_text": response_text,
                        "prompt": prompt_l1
                    }

                    out_l2 = {
                        "id": record_id,
                        "model": model_name,
                        "seed_text": seed_text,
                        "response_text": response_text,
                        "prompt": prompt_l2
                    }

                    out_l3 = {
                        "id": record_id,
                        "model": model_name,
                        "seed_text": seed_text,
                        "response_text": response_text,
                        "prompt": prompt_l3
                    }

                    # 写入 JSONL 文件
                    f_l1.write(json.dumps(out_l1, ensure_ascii=False) + "\n")
                    f_l2.write(json.dumps(out_l2, ensure_ascii=False) + "\n")
                    f_l3.write(json.dumps(out_l3, ensure_ascii=False) + "\n")

                    count += 1

                except json.JSONDecodeError:
                    print(f"错误: 第 {count} 行不是有效的 JSON 格式。")
                    continue

        print("-" * 30)
        print(f"处理完成！共处理了 {count} 条数据。")
        print(f"结果已保存至:\n1. {output_path_l1}\n2. {output_path_l2}\n3. {output_path_l3}")

    except FileNotFoundError:
        print(f"错误: 找不到输入文件 {input_path}")
        print("请检查路径是否正确。")
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    process_prompts()