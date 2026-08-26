import json
import os

# -----------------------------------------------------------------------------
# 1. 定义 Prompt 模板
# -----------------------------------------------------------------------------

def generate_level_1_prompt(seed, rewrite):
    """
    Level 1: Direct Intuition + Rubric (1-10 Scale)
    """
    return f"""### Task
Rate the quality of a rewritten exam question based on the provided rubric.

### Input Data
**Original Seed Question:**
\"\"\"
{seed}
\"\"\"

**Rewritten Question:**
\"\"\"
{rewrite}
\"\"\"

### Instructions
1. Rely on your immediate intuition to judge the rewritten question against the standards above.
2. Assign a single **INTEGER** score from 1 to 10.
3. **STRICT OUTPUT FORMAT:** You must output the score using exactly the format below, with no other text, explanation, or whitespace.

###FINAL_RESULT: [[n]]

(Replace 'n' with your integer score, e.g., 1, 6, 10).
"""


def generate_level_2_prompt(seed, rewrite):
    """
    Level 2: Generic CoT + Rubric (1-10 Scale)
    """
    return f"""### Task
Rate the overall quality of the rewritten question on a scale of 1-10.

### Input Data
**Original Seed Question:**
\"\"\"
{seed}
\"\"\"

**Rewritten Question:**
\"\"\"
{rewrite}
\"\"\"

### Instructions
Please evaluate the rewritten question. You must provide a brief reasoning for your judgment before giving the final score.

### Output Format
**Step 1: Reasoning**
[Briefly explain why you think the rewritten question falls into the specific score range (1-3, 4-6, 7-8, or 9-10) defined above. Write 2-3 sentences.]

**Step 2: Score**
[Output the final integer score using exactly the following format:]
###FINAL_RESULT: [[n]]

(Replace 'n' with your integer score, e.g., 1, 6, 10).
"""


def generate_level_3_prompt(seed, rewrite):
    """
    Level 3: Multi-Dimensional Analysis + Text-Based Fixed Rubric (User Defined)
    修改点：
    1. 根据用户最新的中文要求更新了 1-10 分的具体评判标准。
    2. 重点强化了 7-8 分关于“防止记忆调用”的描述。
    """
    return f"""You are a Senior Benchmark Security Expert. Your goal is to rigorously evaluate a "Rewritten Question" to ensure it serves as a valid, uncontaminated test case for LLMs.

### Input Data
**Original Seed Question:**
{seed}

**Rewritten Question:**
{rewrite}

### Evaluation Protocol
You must follow a strict 3-step evaluation process using the **Fixed Scoring Standards** provided below.

#### Step 1: Dimension Definition & Analysis
First, identify 3-4 critical dimensions for evaluating this specific type of question (e.g., "Degree of Disguise", "Logic Preservation", "Solvability").
For **EACH** dimension:
1.  Analyze the rewrite's performance.
2.  Assign a sub-score (1-10) for that specific dimension.

#### Step 2: Synthesis against Fixed Standards
Synthesize your dimensional analysis and map the *overall quality* to the following strict standards. Do not deviate from these definitions:

* **Score 1-2 (Invalid Question)**
    The rewrite is not a functional problem (e.g., gibberish, not a question at all).

* **Score 3-4 (High Similarity)**
    The rewrite is too similar to the original seed; it is practically identical with no meaningful variation.

* **Score 5-6 (Surface-Level Substitution)**
    The rewrite performs only simple noun replacements (e.g., changing names or objects). Crucially, the overall scenario, theme, and structural framework remain unchanged.

* **Score 7-8 (Deep Transformation & Decontamination)**
    The rewrite undergoes a drastic transformation in context, variables, and setting. It is almost impossible to identify the connection to the original question. The magnitude of change is significantly larger than the 5-6 range, ensuring that a model exposed to the original question cannot solve this rewrite simply by recalling its memory.

* **Score 9-10 (Super-Human Excellence)**
    The quality is even better than the 7-8 range. The rewrite significantly exceeds the question-setting standards of human domain experts.

#### Step 3: Final Verdict
Determine the final integer score based on the standards above.

### Output Requirements
Output your response in the following XML format:

<dimensional_analysis>
[Define 3-4 dimensions. For each, provide analysis and a sub-score]
1. Dimension Name: ...
   - Analysis: ...
   - Sub-score: [x/10]

2. Dimension Name: ...
   - Analysis: ...
   - Sub-score: [x/10]
...
</dimensional_analysis>

<synthesis_and_reasoning>
[Explain why the rewrite fits into a specific score range of the Fixed Standards based on the dimensions above]
</synthesis_and_reasoning>

<final_verdict>
[Output the final integer score (1-10) in the exact format below:]
###FINAL_RESULT: [[n]]

(Replace 'n' with your integer score, e.g., 1, 6, 10).
</final_verdict>
"""


# -----------------------------------------------------------------------------
# 2. 主处理逻辑
# -----------------------------------------------------------------------------

def process_prompts():
    # 输入文件路径
    input_name = "deepseek_seed_response_extracted.jsonl"

    input_path = "./external/metrics/1/similarity/" + input_name

    same_output = "./external/metrics/2/prompts/"

    # 确保输出目录存在
    output_dir = os.path.dirname(input_path)

    # 确保目标输出子目录存在
    if not os.path.exists(same_output):
        try:
            os.makedirs(same_output)
        except OSError:
            pass

    # 定义输出文件路径
    output_path_l1 = os.path.join(output_dir, same_output + input_name + "_prompt_level1.jsonl")
    output_path_l2 = os.path.join(output_dir, same_output + input_name + "_prompt_level2.jsonl")
    output_path_l3 = os.path.join(output_dir, same_output + input_name + "_prompt_level3.jsonl")

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

                    seed_text = data.get("seed_text", "")
                    response_text = data.get("response_text", "")
                    record_id = data.get("id", count)
                    # 【修改点1】获取 model 字段的内容，如果没有则默认为空字符串
                    model_name = data.get("model", "")

                    if not seed_text or not response_text:
                        print(f"警告: 第 {count} 行数据缺失 seed_text 或 response_text，跳过。")
                        continue

                    # 生成 Prompt (全部使用新的 1-10 标准)
                    prompt_l1 = generate_level_1_prompt(seed_text, response_text)
                    prompt_l2 = generate_level_2_prompt(seed_text, response_text)
                    prompt_l3 = generate_level_3_prompt(seed_text, response_text)

                    # -------------------------------------------------------------
                    # 构造输出对象：包含 seed, response 和 prompt
                    # 【修改点2】将 model 字段放入字典，并确保在 id 之后（第二位）
                    # -------------------------------------------------------------
                    out_l1 = {
                        "id": record_id,
                        "model": model_name,  # 新增: model 在第二位
                        "seed_text": seed_text,
                        "response_text": response_text,
                        "prompt": prompt_l1
                    }
                    out_l2 = {
                        "id": record_id,
                        "model": model_name,  # 新增: model 在第二位
                        "seed_text": seed_text,
                        "response_text": response_text,
                        "prompt": prompt_l2
                    }
                    out_l3 = {
                        "id": record_id,
                        "model": model_name,  # 新增: model 在第二位
                        "seed_text": seed_text,
                        "response_text": response_text,
                        "prompt": prompt_l3
                    }

                    # 写入文件
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
    except Exception as e:
        print(f"发生未知错误: {e}")


if __name__ == "__main__":
    process_prompts()