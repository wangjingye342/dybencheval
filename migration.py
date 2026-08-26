# -*- coding: utf-8 -*-
"""整理迁移脚本：把真实使用的代码复制到 整理版代码/，重命名+归一路径+去明文key。原文件不动。"""
import os, re, shutil

SRC = r"D:\STUDY\2026-project1\project1"
DST = os.path.join(SRC, "整理版代码")

# ---------- 核心脚本映射 (src_rel -> dst_rel) ----------
CORE = [
 # 2_数据增强
 ("main_work/scripts/generate_prompt_final.py", "2_数据增强/构造增强prompt.py"),
 ("main_work/scripts/出题.py", "2_数据增强/调用生成.py"),
 ("main_work/scripts/提取gen.py", "2_数据增强/提取生成结果.py"),
 ("main_work/scripts/看gen.py", "2_数据增强/清洗生成结果.py"),
 ("main_work/scripts/看.py", "2_数据增强/转可读json.py"),
 ("rebuttal/增补embedding/get_embedding_qwen.py", "2_数据增强/embedding/增强数据取embedding.py"),
 ("rebuttal/heatmap/分别embedding.py", "2_数据增强/embedding/数据集取embedding_api.py"),
 ("rebuttal/heatmap/获取embedding.py", "2_数据增强/embedding/数据集取embedding_本地.py"),
 # 3_主实验生成
 ("main_work/通用模型实验/批量制造prompt.py", "3_主实验生成/构造改写prompt.py"),
 ("main_work/通用模型实验/批量制造prompt_剩余数据集.py", "3_主实验生成/其他/构造改写prompt_剩余.py"),
 ("main_work/通用模型实验/抽样5.py", "3_主实验生成/其他/抽样5.py"),
 ("main_work/通用模型实验/抽样json.py", "3_主实验生成/其他/抽样json.py"),
 ("main_work/通用模型实验/阅读.py", "3_主实验生成/其他/阅读.py"),
 ("main_work/通用模型实验/问api.py", "3_主实验生成/其他/问api_旧.py"),
 # 4_评测指标
 ("main_work/计算指标/1/相似度/提取题目.py", "4_评测指标/提取seed与response.py"),
 ("main_work/计算指标/00/溯源new.py", "4_评测指标/溯源加标签.py"),
 ("main_work/计算指标/00/溯源.py", "4_评测指标/其他/溯源_旧.py"),
 ("main_work/计算指标/00/seed&response/全部数据.py", "4_评测指标/其他/组合seed_response_全部.py"),
 ("main_work/计算指标/00/s&r+溯源/组合.py", "4_评测指标/其他/组合seed_response.py"),
 ("main_work/计算指标/1/n-gram/高级计算.py", "4_评测指标/多样性/Dist2与BLEU4.py"),
 ("main_work/计算指标/1/self_bleu/算.py", "4_评测指标/多样性/self_bleu.py"),
 ("main_work/计算指标/1/re_embedding/re_embedding.py", "4_评测指标/多样性/取embedding.py"),
 ("main_work/计算指标/1/re_embedding/统计外部相似度.py", "4_评测指标/多样性/外部相似度SemSim.py"),
 ("rebuttal/vendi score/算vendi2.py", "4_评测指标/多样性/vendi.py"),
 ("main_work/计算指标/1/n-gram/计算.py", "4_评测指标/多样性/其他/单文件dist.py"),
 ("main_work/计算指标/1/相似度/计算BLEU-4.py", "4_评测指标/多样性/其他/单文件BLEU4.py"),
 ("rebuttal/vendi score/算vendi.py", "4_评测指标/多样性/其他/vendi_旧.py"),
 ("rebuttal/vendi score/ana.py", "4_评测指标/多样性/其他/vendi诊断.py"),
 ("main_work/计算指标/2/生成prompt_only3.py", "4_评测指标/连贯性/生成prompt_主实验.py"),
 ("main_work/计算指标/2/生成prompt.py", "4_评测指标/连贯性/生成prompt_三级_一致性用.py"),
 ("main_work/计算指标/2/问api.py", "4_评测指标/连贯性/调用裁判_gemini.py"),
 ("main_work/计算指标/2/问api_re.py", "4_评测指标/连贯性/调用裁判_gpt52.py"),
 ("main_work/计算指标/2/提取结果.py", "4_评测指标/连贯性/提取分数.py"),
 ("main_work/计算指标/2/0re/计算平均分.py", "4_评测指标/连贯性/计算平均分.py"),
 ("main_work/计算指标/3/生成prompt_only3.py", "4_评测指标/正确性/生成prompt_主实验.py"),
 ("main_work/计算指标/3/生成prompt.py", "4_评测指标/正确性/生成prompt_三级_一致性用.py"),
 ("main_work/计算指标/3/问api.py", "4_评测指标/正确性/调用裁判.py"),
 ("main_work/计算指标/3/提取结果.py", "4_评测指标/正确性/提取分数.py"),
 ("main_work/计算指标/3/提取题目.py", "4_评测指标/正确性/提取seed与response.py"),
 # 5_人工评测
 ("main_work/评价题目质量/题目质量比较/评价题目质量.py", "5_人工评测/连贯性_pairwise标注.py"),
 ("main_work/评价题目质量/抽取.py", "5_人工评测/连贯性_抽样.py"),
 ("main_work/评价题目质量/final/编号.py", "5_人工评测/连贯性_重编号.py"),
 ("main_work/测评_人工检验/评审.py", "5_人工评测/正确性_pointwise标注.py"),
 ("main_work/测评_人工检验/抽取——正确率.py", "5_人工评测/正确性_抽样.py"),
 ("main_work/测评_人工检验/合并.py", "5_人工评测/正确性_合并样本.py"),
 ("main_work/测评_人工检验/打乱顺序.py", "5_人工评测/正确性_打乱顺序.py"),
 ("main_work/测评_人工检验/添加id.py", "5_人工评测/正确性_添加id.py"),
 ("main_work/计算指标/2/计算正确率.py", "5_人工评测/一致性_连贯性.py"),
 ("main_work/计算指标/3/计算正确率.py", "5_人工评测/一致性_正确性.py"),
 ("main_work/计算指标/2/rank.py", "5_人工评测/排名_BradleyTerry.py"),
 ("main_work/scripts/人工评判.py", "5_人工评测/生成样本质量打分.py"),
 ("main_work/模型再评价/再评价数据生成.py", "5_人工评测/模型再评价/汇总输入.py"),
 ("main_work/模型再评价/再评价prompt生成.py", "5_人工评测/模型再评价/构造prompt.py"),
 ("main_work/模型再评价/问api.py", "5_人工评测/模型再评价/调用裁判.py"),
 ("main_work/模型再评价/添加编号.py", "5_人工评测/模型再评价/添加编号.py"),
 ("main_work/模型再评价/人工评价.py", "5_人工评测/模型再评价/人工标注.py"),
 ("main_work/模型再评价/人工评价结果/去重.py", "5_人工评测/模型再评价/结果_去重.py"),
 ("main_work/模型再评价/人工评价结果/提取保留.py", "5_人工评测/模型再评价/结果_提取保留.py"),
 ("main_work/模型再评价/人工评价结果/提取修改.py", "5_人工评测/模型再评价/结果_提取修改.py"),
 ("main_work/模型再评价/人工评价结果/最终数据集/合并.py", "5_人工评测/模型再评价/结果_按域任务拆分.py"),
 # 6_消融与显著性
 ("main_work/scripts/后补实验/采样3个.py", "6_消融与显著性/prompt变体/采样3shot.py"),
 ("main_work/scripts/后补实验/generate_prompt_final.py", "6_消融与显著性/prompt变体/采样5shot.py"),
 ("main_work/scripts/后补实验/采样7个.py", "6_消融与显著性/prompt变体/采样7shot.py"),
 ("main_work/scripts/后补实验/采样同任务.py", "6_消融与显著性/prompt变体/仅同任务.py"),
 ("main_work/scripts/后补实验/采样同情境.py", "6_消融与显著性/prompt变体/仅同域.py"),
 ("main_work/scripts/后补实验/采样自己.py", "6_消融与显著性/prompt变体/仅同格子.py"),
 ("main_work/scripts/后补实验/组合prompts.py", "6_消融与显著性/prompt变体/合并prompt文件.py"),
 ("main_work/scripts/后补实验/问api.py", "6_消融与显著性/调用生成.py"),
 ("main_work/scripts/后补实验/评估指标/1/distinct-2.py", "6_消融与显著性/打分/Dist2.py"),
 ("main_work/scripts/后补实验/评估指标/2/2批量制造prompt.py", "6_消融与显著性/打分/连贯性_构造prompt.py"),
 ("main_work/scripts/后补实验/评估指标/2/2问api.py", "6_消融与显著性/打分/连贯性_调用裁判.py"),
 ("main_work/scripts/后补实验/评估指标/2/2提取结果.py", "6_消融与显著性/打分/连贯性_提取分数.py"),
 ("main_work/scripts/后补实验/评估指标/2/2统计结果.py", "6_消融与显著性/打分/连贯性_统计.py"),
 ("main_work/scripts/后补实验/评估指标/2/清理.py", "6_消融与显著性/打分/连贯性_按id清理.py"),
 ("main_work/scripts/后补实验/评估指标/3/3批量制造prompt.py", "6_消融与显著性/打分/正确性_构造prompt.py"),
 ("main_work/scripts/后补实验/评估指标/3/3问api.py", "6_消融与显著性/打分/正确性_调用裁判.py"),
 ("main_work/scripts/后补实验/评估指标/3/3提取结果.py", "6_消融与显著性/打分/正确性_提取分数.py"),
 ("main_work/scripts/后补实验/评估指标/3/3统计结果.py", "6_消融与显著性/打分/正确性_统计.py"),
 ("main_work/scripts/后补实验/评估指标/3/清理.py", "6_消融与显著性/打分/正确性_按id清理.py"),
 ("main_work/scripts/后补实验/评估指标/显著性.py", "6_消融与显著性/显著性检验.py"),
 # 1_数据准备/组装数据集
 ("main_work/scripts/后补实验/评估指标/计算size/final数据集/提取.py", "1_数据准备/组装数据集/汇总为数据集.py"),
 ("main_work/scripts/后补实验/评估指标/计算size/final数据集/组合全部.py", "1_数据准备/组装数据集/合并全部jsonl.py"),
 ("main_work/scripts/后补实验/评估指标/计算size/final数据集/抽取100.py", "1_数据准备/组装数据集/抽样100条.py"),
 ("main_work/scripts/后补实验/评估指标/计算size/final数据集/计算.py", "1_数据准备/组装数据集/数据集统计.py"),
 ("back_up/datasets/base/TruthfulQA/data_process.py", "1_数据准备/抽取脚本/其他/TruthfulQA_data_process.py"),
 # 7_结果与画表
 ("main_work/计算指标/0_final/final数据（指标2，3）/汇总所有数据.py", "7_结果与画表/汇总数据.py"),
 ("main_work/计算指标/0_final/final_分开测评.py", "7_结果与画表/分模型测评.py"),
 ("main_work/计算指标/0_final/final评测.py", "7_结果与画表/总体测评.py"),
 ("main_work/计算指标/0_final/table3.py", "7_结果与画表/表3_leaderboard.py"),
 ("main_work/计算指标/0_final/table5.py", "7_结果与画表/表5_排名卡.py"),
 ("main_work/计算指标/0_final/生成latex表/生成latex表.py", "7_结果与画表/生成latex表.py"),
 ("main_work/计算指标/1/n-gram/制表.py", "7_结果与画表/填多样性表.py"),
 ("main_work/计算指标/1/n-gram/取均值.py", "7_结果与画表/多样性取均值.py"),
 ("main_work/计算指标/1/制表/制表1.py", "7_结果与画表/填正确率表.py"),
 ("main_work/计算指标/1/制表/求均值.py", "7_结果与画表/指标取均值.py"),
 ("FINAL_FILES/datasets/合并.py", "7_结果与画表/合并为总表json.py"),
 ("rebuttal/heatmap/画表.py", "7_结果与画表/相似度热图/热图_均值.py"),
 ("rebuttal/heatmap/画表（pairwise）.py", "7_结果与画表/相似度热图/热图_pairwise.py"),
]

# 13 个问api：1:1 保留原名到 各模型调用/
API_DIR = "main_work/通用模型实验"
for f in ["问api_claude.py","问api_deepseek.py","问api_glm.py","问api_gpt5_2.py","问api_qwen3max.py",
          "问api_qwen3-8b.py","问api_qwen3-30b.py","问api_qwen3-235b-a22b-instruct-2507.py",
          "问api_llama-3-8b.py","问api_new_gemini.py","问api_new_llama3-70b.py","问api_new_llama3-8b.py",
          "new_问api_llama-3-8b.py"]:
    CORE.append((f"{API_DIR}/{f}", f"3_主实验生成/各模型调用/{f}"))

# ---------- 关键小数据 ----------
DATA_DIRS = [
 ("FINAL_FILES/datasets/DyBenchEval", "数据/DyBenchEval数据集"),
 ("main_work/计算指标/00/seed&response", "数据/各模型生成结果/seed_and_response"),
 ("main_work/计算指标/00/溯源后", "数据/各模型生成结果/溯源后"),
 ("main_work/计算指标/0_final/final数据（指标2，3）/final", "数据/各模型生成结果/final_all"),
]
DATA_FILES = [
 ("main_work/计算指标/2/annotation_results_fixed_100.jsonl", "数据/人工标注"),
 ("main_work/计算指标/2/annotation_results_fixed.jsonl", "数据/人工标注"),
 ("main_work/测评_人工检验/正确性120_final.jsonl", "数据/人工标注"),
 ("main_work/模型再评价/labeled_120.jsonl", "数据/人工标注"),
 ("main_work/评价题目质量/题目质量比较/annotation_results.jsonl", "数据/人工标注"),
 ("main_work/scripts/后补实验/评估指标/2/coherence_score_summary.json", "数据/打分结果"),
 ("main_work/scripts/后补实验/评估指标/3/coherence_score_summary.json", "数据/打分结果"),
 ("main_work/scripts/后补实验/评估指标/1/distinct2_scores.json", "数据/打分结果"),
 ("main_work/scripts/后补实验/评估指标/1/distinct2_scores_100.json", "数据/打分结果"),
 ("rebuttal/vendi score/simcse_vendi_scores.json", "数据/打分结果"),
 ("rebuttal/vendi score/vendi_scores_2_results.json", "数据/打分结果"),
]
EXTRACTOR_SRC = "main_work/scripts/后补实验/评估指标/计算size/所有数据集"
EXTRACTOR_DST = "1_数据准备/抽取脚本"

# ---------- 转换：归一机器根路径 + 明文key改环境变量 ----------
NR = "D:/STUDY/2026-project1/project1"
ROOT_PATS = [r'/root/autodl-tmp/project1',
             r'[Tt]:[\\/]+2026-project1[\\/]+project1',
             r'[Dd]:[\\/]+STUDY[\\/]+2026-project1[\\/]+project1']
KEY_PATS = [r'"sk-[A-Za-z0-9_\-]{18,}"', r"'sk-[A-Za-z0-9_\-]{18,}'",
            r'"[0-9a-fA-F]{24,}\.[A-Za-z0-9]{12,}"', r"'[0-9a-fA-F]{24,}\.[A-Za-z0-9]{12,}'"]
KEY_REPL = 'os.environ.get("DYBENCH_API_KEY", "")'

def transform(text):
    nroot = nkey = 0
    for pat in ROOT_PATS:
        text, c = re.subn(pat, NR, text); nroot += c
    for pat in KEY_PATS:
        text, c = re.subn(pat, KEY_REPL, text); nkey += c
    if nkey and re.search(r'^\s*import os(\s|$|,)', text, re.M) is None:
        text = "import os  # 整理:环境变量读取key\n" + text
    return text, nroot, nkey

def copy_script(sabs, dabs):
    os.makedirs(os.path.dirname(dabs), exist_ok=True)
    raw = open(sabs, encoding="utf-8", errors="surrogateescape").read()
    out, nr, nk = transform(raw)
    open(dabs, "w", encoding="utf-8", errors="surrogateescape").write(out)
    return nr, nk

def main():
    done=missing=0; tot_root=tot_key=0; missing_list=[]; mapping=[]
    for s, d in CORE:
        sabs=os.path.join(SRC, s.replace("/", os.sep)); dabs=os.path.join(DST, d.replace("/", os.sep))
        if not os.path.isfile(sabs):
            missing+=1; missing_list.append(s); continue
        nr,nk=copy_script(sabs,dabs); tot_root+=nr; tot_key+=nk; done+=1
        mapping.append((d, s))
    # 抽取脚本整棵树的 .py
    ex=0
    esrc=os.path.join(SRC, EXTRACTOR_SRC.replace("/", os.sep))
    for dp,dn,fn in os.walk(esrc):
        for f in fn:
            if f.endswith(".py"):
                sabs=os.path.join(dp,f); rel=os.path.relpath(sabs, esrc)
                dabs=os.path.join(DST, EXTRACTOR_DST.replace("/", os.sep), rel)
                copy_script(sabs,dabs); ex+=1
    # 数据
    dcopied=0
    for s,d in DATA_DIRS:
        sabs=os.path.join(SRC, s.replace("/",os.sep)); dabs=os.path.join(DST, d.replace("/",os.sep))
        if os.path.isdir(sabs):
            if os.path.exists(dabs): shutil.rmtree(dabs)
            shutil.copytree(sabs,dabs); dcopied+=1
        else: missing_list.append("[数据]"+s)
    for s,d in DATA_FILES:
        sabs=os.path.join(SRC, s.replace("/",os.sep)); ddir=os.path.join(DST, d.replace("/",os.sep))
        if os.path.isfile(sabs):
            os.makedirs(ddir, exist_ok=True); shutil.copy2(sabs, os.path.join(ddir, os.path.basename(sabs))); dcopied+=1
        else: missing_list.append("[数据]"+s)
    # 映射表
    with open(os.path.join(DST,"_映射表.md"),"w",encoding="utf-8") as f:
        f.write("# 新↔旧文件对照\n\n| 新路径 | 旧路径 |\n|---|---|\n")
        for d,s in sorted(mapping): f.write(f"| `{d}` | `{s}` |\n")
    print(f"核心脚本复制: {done}  缺失: {missing}")
    print(f"抽取脚本复制: {ex}")
    print(f"数据项复制: {dcopied}")
    print(f"路径归一次数: {tot_root}  明文key替换次数: {tot_key}")
    if missing_list:
        print("\n缺失(未找到源，需核对名称):")
        for m in missing_list: print("  -", m)

if __name__=="__main__":
    main()
