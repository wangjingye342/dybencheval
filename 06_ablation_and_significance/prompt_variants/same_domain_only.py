import os
import json
import random
import glob

# ================= 配置区域 =================

DATA_ROOT = "./data/raw_datasets"
# [修改点1] 输出目录修改为体现"Only Scenario"的路径，避免覆盖
OUTPUT_DIR = "./external/ablation/prompts_onlydomain"

# 模型自主生成子情境的概率
MODEL_DERIVED_SUB_SCENARIO = 0.4
# 生成数量
num_prompts = 30

# 定义图中显示的四个特定任务配置 (Scenario, Task)
TARGET_CONFIGS = [
    ("STEM", "Reasoning"),
    ("Humanity", "Code_Generation"),
    ("Other", "Professional_Knowledge"),
    ("SocialScience", "Role_Play")
]

SCENARIO_MAP = {
    "STEM": "STEM",
    "Humanity": "Humanity",
    "Social Science": "SocialScience",
    "Other": "Other"
}

TASK_MAP = {
    "1": "Basic_NLP",
    "2": "Open_QA",
    "3": "Writing",
    "4": "Reasoning",
    "5": "Role_Play",
    "6": "Professional_Knowledge",
    "7": "Code_Generation"
}

SCENARIO_DISPLAY = {v: k for k, v in SCENARIO_MAP.items()}
TASK_DISPLAY = {v: v for k, v in TASK_MAP.items()}

# ================= 强约束定义 =================

SCENARIO_SPEC = {
    "STEM": """This scenario focuses on science, engineering, mathematics, or technology. Content should be technical, objective, and formal.""",

    "Humanity": """This scenario covers humanities such as philosophy, history, culture, and logic. The tone should be analytical or reflective rather than procedural or technical.""",

    "SocialScience": """This scenario includes law, finance, economics, business, and governance. Content should reflect institutional, regulatory, contractual, organizational, or societal contexts. Casual conversation and purely technical STEM content are not allowed.""",

    "Other": """This scenario includes news, education, and daily-life informational contexts. Content should remain realistic and socially grounded."""
}

# ================= 子情境定义 =================

SCENARIO_SUBDOMAINS = {
    "STEM": [
        "Physics", "Chemistry", "Biology", "Mathematics", "Computer Science", "Engineering"
    ],
    "Humanity": [
        "Philosophy", "History", "Cultural Studies", "Ethics", "Logic", "Literary Analysis"
    ],
    "SocialScience": [
        "Law", "Finance", "Economics", "Business", "Governance"
    ],
    "Other": [
        "News Reporting", "Education", "Public Information", "Daily-life Knowledge"
    ]
}

# ================= 子情境来源模式 =================

SUB_SCENARIO_MODE_PROBS = {
    "SYSTEM_ASSIGNED": 1 - MODEL_DERIVED_SUB_SCENARIO,
    "MODEL_DERIVED": MODEL_DERIVED_SUB_SCENARIO
}


def sample_sub_scenario_mode():
    return random.choices(
        list(SUB_SCENARIO_MODE_PROBS.keys()),
        weights=list(SUB_SCENARIO_MODE_PROBS.values()),
        k=1
    )[0]


# ================= 任务定义 =================

TASK_SPEC = {
    "Basic_NLP": """The task should test basic natural language processing abilities such as classification, paraphrasing, or simple extraction.""",

    "Open_QA": """The task should require answering a factual or descriptive question. The answer must be concise and unambiguous.""",

    "Writing": """The task should require coherent and context-aware text generation, such as explanations, summaries, or essays.""",

    "Reasoning": """The task must require multi-step logical reasoning.

The correct answer must NOT be obtainable via:
- keyword matching
- direct factual recall
- simple numerical calculation

The reasoning process should involve:
- rule or principle application
- conditional evaluation
- conflict resolution or inference

MANDATORY OUTPUT REQUIREMENT:
The output MUST explicitly include a clearly labeled section named:
**reasoning process**

Failure to include an explicit reasoning process INVALIDATES the output.""",

    "Role_Play": """The task should simulate a role-based interaction with clear objectives and consistent persona behavior.

MANDATORY OUTPUT REQUIREMENT:
The output MUST explicitly specify the acting **role** (e.g., identity, position, or persona) and maintain this role consistently throughout the interaction.

Failure to clearly define and adhere to a role INVALIDATES the output.""",

    "Professional_Knowledge": """The task should assess domain-specific professional knowledge and its correct application.""",

    "Code_Generation": """The task should require generating correct and functional code that satisfies the given specification.

MANDATORY OUTPUT REQUIREMENT:
The output MUST explicitly include a section named:
**test_cases**

The test cases should be concrete, executable, and consistent with the generated code.

Failure to include test cases INVALIDATES the output."""
}

# ================= Prompt 模板 =================

# [修改点2] 更新模板，Example 2 和 Example 3 的 Task 占位符不再硬编码为 target_task_disp
PROMPT_TEMPLATE = """# Role Definition
You are a professional dataset generation engine.
Your responsibility is to generate NEW, ORIGINAL, and HIGH-QUALITY dataset samples
that strictly satisfy the explicitly defined Task and Scenario requirements.

You MUST prioritize the formal definitions below over any example content.

---

# 1. Explicit Generation Requirements (HIGHEST PRIORITY)

## Target Scenario: {target_scenario_disp}

{scenario_spec}

### Sub-Scenario Selection Protocol (MANDATORY)

Sub-scenario selection mode:
**{sub_scenario_mode}**

{selected_sub_scenario_block}

## Target Task: {target_task_disp}

{task_spec}

---

# 2. Output Contract (STRICT)

Generate exactly ONE complete dataset sample.

The sample must:
- Be self-contained
- Be answerable
- Have a clearly identifiable correct output
- Strictly match the target task and the sub-scenario

DO NOT generate multiple questions.
DO NOT include meta explanations.

---

# 3. Reference Examples (LOW PRIORITY)

The following examples are provided only to help calibrate language style, complexity, and realism.

You MUST NOT:
- Copy entities, facts, or structures
- Rephrase or adapt example content
- Infer requirements from examples

### Example 1
[Scenario: {target_scenario_disp}] | [Task: {target_task_disp}]
{shot1_content}

### Example 2
[Scenario: {shot2_scenario_disp}] | [Task: {shot2_task_disp}]
{shot2_content}

### Example 3
[Scenario: {shot3_scenario_disp}] | [Task: {shot3_task_disp}]
{shot3_content}

### Example 4
[Scenario: {target_scenario_disp}] | [Task: {shot4_task_disp}]
{shot4_content}

### Example 5
[Scenario: {target_scenario_disp}] | [Task: {shot5_task_disp}]
{shot5_content}

---

# Final Instruction

Generate ONE new dataset sample that strictly satisfies:
- the target task
- the target scenario
- the selected or derived sub-scenario

Focus on reasoning depth, institutional realism, and correctness.
"""

# ================= 采样概率 =================

SCENARIO_PROBS = {
    "STEM": {"Humanity": 0.33, "SocialScience": 0.34, "Other": 0.33},
    "Humanity": {"STEM": 0.31, "SocialScience": 0.35, "Other": 0.34},
    "SocialScience": {"STEM": 0.33, "Humanity": 0.35, "Other": 0.32},
    "Other": {"STEM": 0.33, "Humanity": 0.34, "SocialScience": 0.33}
}

TASK_PROBS = {
    "Basic_NLP": {"Open_QA": 0.18, "Writing": 0.18, "Reasoning": 0.17, "Role_Play": 0.17,
                  "Professional_Knowledge": 0.16, "Code_Generation": 0.14},
    "Open_QA": {"Basic_NLP": 0.18, "Writing": 0.17, "Reasoning": 0.18, "Role_Play": 0.16,
                "Professional_Knowledge": 0.17, "Code_Generation": 0.13},
    "Writing": {"Basic_NLP": 0.19, "Open_QA": 0.18, "Reasoning": 0.17, "Role_Play": 0.17,
                "Professional_Knowledge": 0.16, "Code_Generation": 0.13},
    "Reasoning": {"Basic_NLP": 0.17, "Open_QA": 0.19, "Writing": 0.16, "Role_Play": 0.16,
                  "Professional_Knowledge": 0.18, "Code_Generation": 0.14},
    "Role_Play": {"Basic_NLP": 0.18, "Open_QA": 0.17, "Writing": 0.17, "Reasoning": 0.17,
                  "Professional_Knowledge": 0.16, "Code_Generation": 0.15},
    "Professional_Knowledge": {"Basic_NLP": 0.17, "Open_QA": 0.18, "Writing": 0.16, "Reasoning": 0.19,
                               "Role_Play": 0.16, "Code_Generation": 0.14},
    "Code_Generation": {"Basic_NLP": 0.17, "Open_QA": 0.16, "Writing": 0.16, "Reasoning": 0.17, "Role_Play": 0.17,
                        "Professional_Knowledge": 0.17}
}


# ================= 核心逻辑 =================

class DatasetLoader:
    def __init__(self, root_path):
        self.root_path = root_path
        self.data_index = {}
        self._build_index()

    def _build_index(self):
        for scenario_folder, scenario_key in SCENARIO_MAP.items():
            s_path = os.path.join(self.root_path, scenario_folder)
            if not os.path.exists(s_path):
                continue
            self.data_index[scenario_key] = {}
            for task_folder in os.listdir(s_path):
                task_path = os.path.join(s_path, task_folder)
                if not os.path.isdir(task_path):
                    continue
                prefix = task_folder.split('_')[0]
                if prefix in TASK_MAP:
                    task_key = TASK_MAP[prefix]
                    files = glob.glob(os.path.join(task_path, "*.jsonl"))
                    if files:
                        self.data_index[scenario_key][task_key] = files

    def get_random_sample_raw(self, scenario_key, task_key):
        files = self.data_index.get(scenario_key, {}).get(task_key, [])
        if not files:
            return f"{{Error: No data found for {scenario_key}/{task_key}}}"
        file = random.choice(files)
        with open(file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        return random.choice(lines) if lines else "{Error: Empty file}"


def weighted_sample(prob_dict):
    return random.choices(list(prob_dict.keys()), weights=list(prob_dict.values()), k=1)[0]


def sample_sub_scenario(target_scenario):
    return random.choice(SCENARIO_SUBDOMAINS[target_scenario])


def build_sub_scenario_block(mode, target_scenario):
    if mode == "SYSTEM_ASSIGNED":
        sub = sample_sub_scenario(target_scenario)
        return f"SYSTEM-ASSIGNED SUB-SCENARIO: **{sub}**. You must treat this sub-scenario as the only valid thematic basis, align institutions, actors, terminology, and reasoning structure accordingly, and not drift into other sub-scenarios."
    else:
        return "MODEL-DERIVED SUB-SCENARIO: You must propose one concrete and specific sub-scenario that clearly belongs to the target scenario, explicitly state the chosen sub-scenario name at the beginning of the output, ensure the sub-scenario is not a generic category, and use this sub-scenario consistently throughout the sample. Failure to do so invalidates the output."


def generate_prompt_content(loader, target_scenario, target_task):
    sub_mode = sample_sub_scenario_mode()
    sub_block = build_sub_scenario_block(sub_mode, target_scenario)

    # === [修改点3] 核心修改：5个样本全部来自 target_scenario，但任务不同 ===

    # Shot 1: Anchor (Target Scenario + Target Task)
    s1 = loader.get_random_sample_raw(target_scenario, target_task)

    # 确定 Shot 2, 3, 4, 5 的任务类型
    # 使用 TASK_PROBS 采样与当前任务相关的其他任务，保证在同一情境下有任务多样性
    t2 = weighted_sample(TASK_PROBS[target_task])
    t3 = weighted_sample(TASK_PROBS[target_task])
    t4 = weighted_sample(TASK_PROBS[target_task])
    t5 = weighted_sample(TASK_PROBS[target_task])

    # Shot 2 - 5: Target Scenario + Random Task
    s2 = loader.get_random_sample_raw(target_scenario, t2)
    s3 = loader.get_random_sample_raw(target_scenario, t3)
    s4 = loader.get_random_sample_raw(target_scenario, t4)
    s5 = loader.get_random_sample_raw(target_scenario, t5)

    return PROMPT_TEMPLATE.format(
        target_scenario_disp=SCENARIO_DISPLAY[target_scenario],
        target_task_disp=TASK_DISPLAY[target_task],
        scenario_spec=SCENARIO_SPEC[target_scenario],
        task_spec=TASK_SPEC[target_task],
        sub_scenario_mode=sub_mode,
        selected_sub_scenario_block=sub_block,

        # Shot 1
        shot1_content=s1,

        # Shot 2 (Scenario固定，Task变化)
        shot2_scenario_disp=SCENARIO_DISPLAY[target_scenario],
        shot2_task_disp=TASK_DISPLAY[t2],
        shot2_content=s2,

        # Shot 3 (Scenario固定，Task变化)
        shot3_scenario_disp=SCENARIO_DISPLAY[target_scenario],
        shot3_task_disp=TASK_DISPLAY[t3],
        shot3_content=s3,

        # Shot 4 (Scenario固定，Task变化)
        shot4_task_disp=TASK_DISPLAY[t4],
        shot4_content=s4,

        # Shot 5 (Scenario固定，Task变化)
        shot5_task_disp=TASK_DISPLAY[t5],
        shot5_content=s5
    )


def main():
    loader = DatasetLoader(DATA_ROOT)

    # 确保输出目录存在
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    total_count = 0

    # 遍历特定配置
    for (s_key, t_key) in TARGET_CONFIGS:
        output_file = os.path.join(OUTPUT_DIR, f"generated_prompts_{s_key}_{t_key}.jsonl")

        with open(output_file, "w", encoding="utf-8") as f:
            for _ in range(num_prompts):
                prompt = generate_prompt_content(loader, s_key, t_key)
                record = {
                    "target_scenario": s_key,
                    "target_task": t_key,
                    "prompt": prompt
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                total_count += 1

        print(f"Generated {num_prompts} prompts for [{s_key} - {t_key}] -> {output_file}")

    print(f"Total generated: {total_count}")


if __name__ == "__main__":
    main()