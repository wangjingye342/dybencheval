import json
import os

# ================= 配置区域 =================

# 输入目录 (上一轮生成的结果)
INPUT_DIR = "D:/STUDY/2026-project1/project1/main_work/scripts/后补实验/all_results"
# 输出目录 (存放用于评测 Coherence 的 prompt)
OUTPUT_DIR = "./prompts_coherence"

# ================= 1. 定义 Prompt 模板 (High Difficulty Version) =================

def generate_coherence_prompt(generated_question):
    """
    针对单条生成的题目进行 Coherence (连贯性/完整性/逻辑性) 评分。
    本次修改大幅提升了评分难度，引入了严苛的扣分机制。
    """
    return f"""You are a **Ruthless Exam Board Auditor**. Your job is to reject or heavily penalize any generated question that does not meet the highest professional standards of high-stakes examinations.

**CRITICAL INSTRUCTION: DEFEAT THE "NICE EVALUATOR" BIAS.**
* **Default Score:** Assume the question is a **5/10** (Average) until proven otherwise.
* **The "10" Trap:** A score of 10 implies **PERFECTION**. It must be novel, precise, elegant, and challenging. If you can improve the wording *at all*, it is NOT a 10.
* **Punish Ambiguity:** If a user has to "guess" the context or assumes standard values that aren't stated, deduct points immediately.

### Input Data
**Generated Question:**
{generated_question}

### Evaluation Protocol
Follow this strict 3-step process.

#### Step 1: "Red Flag" Dimension Analysis
Analyze the question for these specific flaws. Be pedantic.
1.  **Grammar & Tone**: Is it "translationese" (awkward phrasing)? Is it too casual? (e.g., "Let's calculate..." is bad style for formal exams).
2.  **Structural Integrity**: Are the inputs/variables clearly defined *before* the question is asked? Is the goal explicit?
3.  **Logical & Internal Consistency**: Is the scenario physically/logically possible? Are there redundant conditions?
4.  **Self-Containment**: Can the question be solved *strictly* using the information provided, without external assumptions?

#### Step 2: Synthesis against STRICT Scoring Standards

* **Score 1-2 (Fatal Failure)**
    * Gibberish, incomplete sentences, code artifacts.
    * The question cuts off mid-sentence.
    * Logically impossible (e.g., "A triangle with sides 1, 2, 10").

* **Score 3-4 (Broken / Unsolvable)**
    * **Major Ambiguity:** Key variables are missing (e.g., "Calculate the speed" without time).
    * **Logic Conflict:** Contradictory constraints make the solution undefined.
    * **Severe Grammar:** So broken that the meaning is guessed.

* **Score 5-6 (The "Mediocre" Baseline)**
    * *This is the most common category.*
    * The question is solvable and correct, **BUT**:
    * Phrasing is clunky, repetitive, or robotic.
    * Structure is loose (e.g., mixes setup and question together confusingly).
    * It relies on "common sense" rather than explicit definition (e.g., assuming gravity is 9.8 without stating it in a physics problem).

* **Score 7-8 (Professional Standard)**
    * The question is **flawless** in grammar and logic.
    * It reads like a standard textbook problem.
    * All constraints are explicitly stated.
    * **Why not 10?** It is generic, simple, or follows a very predictable template. It lacks depth or nuance.

* **Score 9-10 (Elite / Distinguised)**
    * **Rare (Top 1% only).**
    * Not only flawless, but **elegant**. Concise, precise, and structurally beautiful.
    * Zero ambiguity. Corner cases are handled.
    * Demonstrates high-level complexity or institutional-grade quality (e.g., GRE/Gaokao/Professional Certification level).

#### Step 3: Final Verdict
Determine the final integer score. **Be harsh.**

### Output Requirements
Output your response in the following XML format:

<dimensional_analysis>
[Provide a critical critique. Point out specific flaws.]
1. Grammar & Tone: ... (Sub-score: x/10)
2. Structural Integrity: ... (Sub-score: x/10)
3. Logical Consistency: ... (Sub-score: x/10)
4. Self-Containment: ... (Sub-score: x/10)
</dimensional_analysis>

<synthesis_and_reasoning>
[Explain exactly why this question did NOT get a higher score. Compare it to the boundaries defined above.]
</synthesis_and_reasoning>

<final_verdict>
[Output the final integer score (1-10) in the exact format below:]
###FINAL_RESULT: [[n]]
</final_verdict>
"""

# ================= 2. 主处理逻辑 =================

def process_prompts():
    # 确保输出目录存在
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
            print(f"已创建输出目录: {OUTPUT_DIR}")
        except OSError as e:
            print(f"创建目录失败: {e}")
            return

    # 获取输入目录下所有的 jsonl 文件
    try:
        files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".jsonl")]
    except FileNotFoundError:
        print(f"错误: 找不到输入目录 {INPUT_DIR}")
        return

    if not files:
        print(f"在目录 {INPUT_DIR} 中未找到 .jsonl 文件。")
        return

    print(f"找到 {len(files)} 个文件，准备处理...")

    # 遍历所有文件
    for filename in files:
        input_path = os.path.join(INPUT_DIR, filename)

        # 构造输出文件名
        file_name_only = os.path.splitext(filename)[0]
        output_filename = f"{file_name_only}_prompt_coherence.jsonl"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"正在处理: {filename} -> {output_filename}")

        count = 0
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

                        # 获取关键字段
                        generated_question = data.get("response", "")
                        record_id = data.get("id")

                        # 校验数据有效性
                        if not generated_question:
                            skipped_count += 1
                            continue

                        # 生成 Coherence 评测 Prompt (使用新的高难度版本)
                        prompt_coherence = generate_coherence_prompt(generated_question)

                        # 构造输出对象
                        out_record = {
                            "id": record_id,
                            "target_task": data.get("target_task", ""),
                            "target_scenario": data.get("target_scenario", ""),
                            "original_response": generated_question,
                            "prompt": prompt_coherence
                        }

                        # 写入文件
                        fout.write(json.dumps(out_record, ensure_ascii=False) + "\n")
                        count += 1

                    except json.JSONDecodeError:
                        print(f"文件 {filename} 中存在无效 JSON 行，已跳过。")
                        continue

            print(f"  - 完成。写入: {count} 条 | 跳过(空内容): {skipped_count} 条")

        except Exception as e:
            print(f"处理文件 {filename} 时发生错误: {e}")

    print("-" * 30)
    print(f"所有文件处理完毕！结果保存在: {OUTPUT_DIR}")


if __name__ == "__main__":
    process_prompts()