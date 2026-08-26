import json

input_file = 'D:/STUDY/2026-project1/project1/main_work/测评_人工检验/正确性120.jsonl'
output_file = 'D:/STUDY/2026-project1/project1/main_work/测评_人工检验/正确性120_final.jsonl'

with open(input_file, 'r', encoding='utf-8') as f_in, \
        open(output_file, 'w', encoding='utf-8') as f_out:
    for index, line in enumerate(f_in):
        if line.strip():
            original_data = json.loads(line)

            # 【关键步骤】构建新字典：先放 id，再解包原有数据
            # 这里的 **original_data 会将原数据的所有字段跟在 id 后面
            new_data = {
                "id": index + 1,
                **original_data
            }

            f_out.write(json.dumps(new_data, ensure_ascii=False) + '\n')

print("处理完成！ID 已置于首位。")