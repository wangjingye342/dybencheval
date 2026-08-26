import json
import os


# -----------------------------------------------------------------------------
# 1. 定义 Prompt 模板 (已针对“分数分布不均”问题进行深度优化)
# -----------------------------------------------------------------------------

def generate_level_3_prompt(seed, rewrite):
    """
    Level 3: Multi-Dimensional Analysis + Text-Based Fixed Rubric (Enhanced Distribution)
    修改说明：
    1. 增加了 [CRITICAL INSTRUCTION] 强制模型避免中庸打分，要求必须使用 1-10 全范围。
    2. 重新定义了 3-4, 5-6, 7-8 的边界：
       - 简单的同义词替换现在属于 3-4 分。
       - 5-6 分被严格限制为“名词替换但句式结构不变”。
       - 7-8 分必须包含“句式结构的重组”。
    3. 引入了 "Tie-breaking" 机制，指导模型在犹豫时如何选择。
    """
    return f"""You are a Senior Benchmark Security Expert. Your goal is to rigorously evaluate a "Rewritten Question" against an "Original Seed Question".

### CRITICAL INSTRUCTION: AVOID CENTRAL TENDENCY
**WARNING:** Previous evaluations have shown a bias towards "safe" scores (5-6).
- Do **NOT** default to 5 or 6 unless the rewrite strictly fits that specific definition.
- You **MUST** use the full spectrum of the scoring range (1-10).
- Be harsh on lazy rewrites (push them down to 3-4) and generous to creative logic masking (push them up to 7-8).

### Input Data
**Original Seed Question:**
{seed}

**Rewritten Question:**
{rewrite}

### Evaluation Protocol
Follow this strict 3-step evaluation process.

#### Step 1: Dimension Definition & Analysis
Identify 3 distinct dimensions (e.g., "Narrative Divergence", "Logical Obfuscation", "Parameter Disguise").
For EACH dimension, assign a raw sub-score (1-10).

#### Step 2: Mapping to Fixed Standards
Map the overall quality to the following strict rubric. Pay close attention to the "Ceiling" and "Threshold" notes.

* **Score 1-2 (Failed/Invalid)**
    - The rewrite is gibberish, incomplete, or mathematically/logically broken.
    - It is not a functional question.

* **Score 3-4 (Lazy Paraphrasing / Synonym Swap)**
    - **Definition:** The rewrite merely uses synonyms or slightly changes word order but keeps the *exact same* entities and context (e.g., changing "Bob has 5 apples" to "Bob possesses 5 apples").
    - **Constraint:** If the *subject matter* has not changed, the score MUST NOT exceed 4.

* **Score 5-6 (Surface-Level Substitution - "The Mask")**
    - **Definition:** The rewrite performs a "Find & Replace" operation. Names, objects, or places are changed (e.g., "Apples" -> "Spaceships"), BUT the sentence structure and logic flow map 1:1 to the original.
    - **Hard Ceiling:** If you can easily map every sentence of the rewrite back to the original line-by-line (Structure Preservation), the score represents a **HARD CEILING at 6**.

* **Score 7-8 (Deep Contextual Re-engineering)**
    - **Definition:** The scenario is completely different. The logic is preserved, but it is embedded in a new, coherent story that distracts from the original pattern. The sentence structure is significantly altered.
    - **Threshold:** If the user has to read the question twice to realize it's the same math problem as the original, it starts at 7.

* **Score 9-10 (Cognitive Decoupling)**
    - **Definition:** Masterful rewriting. The problem is unrecognizable as the original seed but tests the exact same underlying reasoning capabilities. It exceeds the quality of human-written exam questions.

#### Step 3: Decision Logic (Tie-Breaker)
Use this logic to finalize your score:
- **Debating between 4 and 5?** Ask: "Did the context/topic actually change?" -> If No (same topic), Score 4. If Yes, Score 5.
- **Debating between 6 and 7?** Ask: "Is the sentence structure identical?" -> If Yes, Score 6. If No (structure changed), Score 7.

### Output Requirements
Output your response in the following XML format:

<dimensional_analysis>
[Analyze 3 dimensions. Be critical.]
1. Dimension Name: ...
   - Analysis: ...
   - Sub-score: [x/10]
...
</dimensional_analysis>

<synthesis_and_reasoning>
[Explicitly state why the score falls into the chosen bucket. Reference the "Tie-Breaker" logic used.]
</synthesis_and_reasoning>

<final_verdict>
[Output the final integer score (1-10) in the exact format below:]
###FINAL_RESULT: [[n]]
</final_verdict>
"""


# -----------------------------------------------------------------------------
# 2. 主处理逻辑
# -----------------------------------------------------------------------------

def process_prompts():
    # 定义输入和输出目录 (保持你原有的路径不变)
    input_dir = "./external/metrics/1/similarity"
    output_dir = "./external/metrics/2/0re/promptsonly3_re/"

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"已创建输出目录: {output_dir}")
        except OSError as e:
            print(f"创建目录失败: {e}")
            return

    # 获取输入目录下所有的 jsonl 文件
    try:
        files = [f for f in os.listdir(input_dir) if f.endswith(".jsonl")]
    except FileNotFoundError:
        print(f"错误: 找不到输入目录 {input_dir}")
        return

    if not files:
        print(f"在目录 {input_dir} 中未找到 .jsonl 文件。")
        return

    print(f"找到 {len(files)} 个文件，准备处理...")

    # 遍历所有文件
    for filename in files:
        input_path = os.path.join(input_dir, filename)

        # 构造输出文件名：去除 .jsonl 后缀，加上 _prompt_level3.jsonl
        output_filename = filename.replace(".jsonl", "") + "_prompt_level3.jsonl"
        output_path = os.path.join(output_dir, output_filename)

        print(f"正在处理: {filename} -> {output_filename}")

        count = 0

        try:
            with open(input_path, 'r', encoding='utf-8') as fin, \
                    open(output_path, 'w', encoding='utf-8') as fout:

                for line in fin:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)

                        seed_text = data.get("seed_text", "")
                        response_text = data.get("response_text", "")
                        record_id = data.get("id", count)
                        model_name = data.get("model", "")

                        if not seed_text or not response_text:
                            # 简单的日志，避免刷屏
                            continue

                        # 仅生成 Level 3 Prompt (使用新的打分逻辑)
                        prompt_l3 = generate_level_3_prompt(seed_text, response_text)

                        # 构造输出对象
                        out_l3 = {
                            "id": record_id,
                            "model": model_name,
                            "seed_text": seed_text,
                            "response_text": response_text,
                            "prompt": prompt_l3
                        }

                        # 写入文件
                        fout.write(json.dumps(out_l3, ensure_ascii=False) + "\n")
                        count += 1

                    except json.JSONDecodeError:
                        print(f"文件 {filename} 中存在无效 JSON 行，已跳过。")
                        continue

            print(f"  - 完成。共写入 {count} 条数据。")

        except Exception as e:
            print(f"处理文件 {filename} 时发生错误: {e}")

    print("-" * 30)
    print("所有文件处理完毕！")


if __name__ == "__main__":
    process_prompts()