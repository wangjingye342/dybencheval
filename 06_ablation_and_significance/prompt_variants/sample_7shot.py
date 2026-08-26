import os
import json
import random
import glob

# ================= 配置区域 =================

DATA_ROOT = "D:/STUDY/2026-project1/project1/all_datasets"
# 模型自主生成子情境的概率
MODEL_DERIVED_SUB_SCENARIO = 0.4
# 生成数量
num_prompts = 30
target_scenarios = ["STEM"]
target_tasks = ["Reasoning"]

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


# ================= 任务定义（增强版） =================

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

# ================= Prompt 模板 (已修改：支持7个示例) =================

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

### Example 1 (Target Match)
[Scenario: {target_scenario_disp}] | [Task: {target_task_disp}]
{shot1_content}

### Example 2 (Same Task, Different Scenario)
[Scenario: {shot2_scenario_disp}] | [Task: {target_task_disp}]
{shot2_content}

### Example 3 (Same Task, Different Scenario)
[Scenario: {shot3_scenario_disp}] | [Task: {target_task_disp}]
{shot3_content}

### Example 4 (Same Task, Different Scenario)
[Scenario: {shot4_scenario_disp}] | [Task: {target_task_disp}]
{shot4_content}

### Example 5 (Same Scenario, Different Task)
[Scenario: {target_scenario_disp}] | [Task: {shot5_task_disp}]
{shot5_content}

### Example 6 (Same Scenario, Different Task)
[Scenario: {target_scenario_disp}] | [Task: {shot6_task_disp}]
{shot6_content}

### Example 7 (Same Scenario, Different Task)
[Scenario: {target_scenario_disp}] | [Task: {shot7_task_disp}]
{shot7_content}

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
            return "{Error: No data found}"
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

    # 1. Target Sample (Sample 1)
    s1 = loader.get_random_sample_raw(target_scenario, target_task)

    # 2. Same Task, Different Scenarios (Sample 3 times)
    logic_s1 = weighted_sample(SCENARIO_PROBS[target_scenario])
    logic_s2 = weighted_sample(SCENARIO_PROBS[target_scenario])
    logic_s3 = weighted_sample(SCENARIO_PROBS[target_scenario])

    s2 = loader.get_random_sample_raw(logic_s1, target_task)
    s3 = loader.get_random_sample_raw(logic_s2, target_task)
    s4 = loader.get_random_sample_raw(logic_s3, target_task)

    # 3. Same Scenario, Different Tasks (Sample 3 times)
    style_t1 = weighted_sample(TASK_PROBS[target_task])
    style_t2 = weighted_sample(TASK_PROBS[target_task])
    style_t3 = weighted_sample(TASK_PROBS[target_task])

    s5 = loader.get_random_sample_raw(target_scenario, style_t1)
    s6 = loader.get_random_sample_raw(target_scenario, style_t2)
    s7 = loader.get_random_sample_raw(target_scenario, style_t3)

    return PROMPT_TEMPLATE.format(
        target_scenario_disp=SCENARIO_DISPLAY[target_scenario],
        target_task_disp=TASK_DISPLAY[target_task],
        scenario_spec=SCENARIO_SPEC[target_scenario],
        task_spec=TASK_SPEC[target_task],
        sub_scenario_mode=sub_mode,
        selected_sub_scenario_block=sub_block,

        # Shot 1 (Target)
        shot1_content=s1,

        # Shots 2, 3, 4 (Same Task, Diff Scenario)
        shot2_scenario_disp=SCENARIO_DISPLAY[logic_s1],
        shot2_content=s2,
        shot3_scenario_disp=SCENARIO_DISPLAY[logic_s2],
        shot3_content=s3,
        shot4_scenario_disp=SCENARIO_DISPLAY[logic_s3],
        shot4_content=s4,

        # Shots 5, 6, 7 (Same Scenario, Diff Task)
        shot5_task_disp=TASK_DISPLAY[style_t1],
        shot5_content=s5,
        shot6_task_disp=TASK_DISPLAY[style_t2],
        shot6_content=s6,
        shot7_task_disp=TASK_DISPLAY[style_t3],
        shot7_content=s7
    )


def main():
    loader = DatasetLoader(DATA_ROOT)
    # target_scenarios = target_scenarios
    # target_tasks = target_tasks
    output_file = f"prompts_7/generated_prompts_{target_scenarios[0]}_{target_tasks[0]}.jsonl"

    # 确保目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    count = 0
    with open(output_file, "w", encoding="utf-8") as f:
        for s in target_scenarios:
            for t in target_tasks:
                for _ in range(num_prompts):
                    prompt = generate_prompt_content(loader, s, t)
                    f.write(json.dumps({"target_scenario": s, "target_task": t, "prompt": prompt},
                                       ensure_ascii=False) + "\n")
                    count += 1
    print(f"Generated {count} prompts → {output_file}")


if __name__ == "__main__":
    main()