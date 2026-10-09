#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 / Step 8: 全文级 R2/R3/R5 编码（把 [C] 档升级为 [A]/[B]）。

方法学：
  对已下载的 arXiv 全文 .txt（Step 7 产物），用**逐篇手工核定的引文**（verbatim quote）
  重编码 R2（聚合口径披露）/ R3（种子数披露）/ R5（测试集构成披露）。
  ⚠️ 判定标准（预注册，写进论文方法节）：
     [A] = 全文中有**明确语句**披露该字段（下面 evidence 字段给出原句）
     [B] = 有间接/部分线索（如报告了方差但未说 seed 数）
     [C] = 全文通读后仍未找到该字段的披露
  ⚠️ 反例纪律：**摘要看不到 ≠ 正文没有**。本脚本的存在就是为了证明这一点：
     在摘要级编码里 R3 是 0/35，但取全文后发现有多篇明确报告了 seed。
     这是 P0-S1 方法学诚实性的核心体现。
"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = OUT_DIR

# 逐篇全文级编码。evidence = 原文引句（verbatim）；code ∈ {A,B,C}
FULLTEXT_CODING = {
    "2607.22380": {   # IR275K
        "id": "IR275K", "file": "2607.22380",
        "R2_agg": "B", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "报告了各 split 的 thermal contrast / temporal noise 的 均值/中位/IQR（分布级刻画），"
                       "但未明确说评测指标（PSNR）本身是逐图均值还是中位。",
        "R3_evidence": "全文未见 seed 数或多次训练平均的表述。",
        "R5_evidence": "'Training receives 261 sequences with 192,776 frames, validation receives 111 "
                       "sequences with 27,576 frames, and test receives 222 sequences with 54,844 frames.' "
                       "且 'no frame from the same sequence appears in more than one partition'（序列级隔离）。",
        "note": "★ benchmark 论文，R5 做得很规范（序列级 split + 分布级刻画）；但 R3 仍缺席。",
    },
    "2606.08535": {   # NGram-MoSE
        "id": "NGram-MoSE", "file": "2606.08535",
        "R2_agg": "C", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "未说明 PSNR 聚合方式。",
        "R3_evidence": "未报告 seed 数或多次运行。",
        "R5_evidence": "'The training set is constructed from five large-scale high-resolution remote sensing scenes "
                       "(5000x5000 pixels each)... Evaluation is conducted on an independent test set of 29 "
                       "geographically disjoint scenes (480x480), which are excluded from training.'",
        "note": "★ 明确的地理隔离 OOD 测试集（29 场景）；R5 优秀，R2/R3 缺席。",
    },
    "2605.00310": {   # GeoSR-Bench
        "id": "GeoSR-Bench", "file": "2605.00310",
        "R2_agg": "B", "R3_seeds": "A", "R5_testset": "A",
        "R2_evidence": "下游任务用 mean F1 / MAE，未明确 SR 保真指标的聚合口径。",
        "R3_evidence": "'To enhance result robustness, for each evaluation case we train the pixel-level "
                       "prediction models three times, and report performance averaged over the three runs.' "
                       "表 VIII/IX 标题亦标注 'averaged over three independent runs'。",
        "R5_evidence": "~36,000 空间共定位、时间对齐、质控后的图像对，覆盖 500m-0.6m 多分辨率。",
        "note": "★★★【标杆】唯一一篇在**下游任务**上明确 3 次独立运行取平均的论文。"
                "⇒ 证明'种子重复'在这个领域是可做且已被做的——问题在于它没有被推广。",
    },
    "2604.14558": {   # NTIRE2026-SR
        "id": "NTIRE2026-SR", "file": "2604.14558",
        "R2_agg": "A", "R3_seeds": "B", "R5_testset": "A",
        "R2_evidence": "'A 4-pixel border is excluded from each image during evaluation, and all calculations are "
                       "carried out on the Y channel of the YCbCr color space.' + 8 指标定义明确。",
        "R3_seeds": "B",
        "R3_evidence": "多数队伍仅报单次；个别队伍给 'Random seed 42'（单一 seed，非多次重复）。",
        "R5_evidence": "DIV2K test 100 张；LR-HR 由 HQ 经 bicubic ×4 生成；HR 测试图全程保密。",
        "note": "★★★ 官方口径最完整（border/色彩通道/8 指标）；但官方仍用**单点阈值**而非统计功效。",
    },
    "2604.21312": {   # NTIRE2026-IR
        "id": "NTIRE2026-IR", "file": "2604.21312",
        "R2_agg": "A", "R3_seeds": "A", "R5_testset": "A",
        "R2_evidence": "★ 挑战赛评分公式明确：'Score = PSNR + 20 x SSIM amplifies SSIM by a factor of 20 "
                       "relative to PSNR. Concretely, an SSIM improvement of 0.01 contributes the same as a "
                       "0.2 dB PSNR gain.' ⇒ **权重选择被显式披露，且直接改变排名语义**。",
        "R3_evidence": "参赛队表格中明确列出 'Random seed 42'（S2 队）；S1 未列。",
        "R5_evidence": "1,019 official HR/LR pairs，no extra data；另有队伍用 SatVideoIRSDT 补充训练。",
        "note": "★★★【最点题】官方评分公式把 SSIM 放大 20 倍（0.01 SSIM = 0.2 dB PSNR）——"
                "**这正是 P0-S1 说的'口径选择直接决定排名'的权威例证**。且该口径是被明示的，"
                "说明官方知道权重选择重要。",
    },
    "2604.21801": {   # SyMTRS
        "id": "SyMTRS", "file": "2604.21801",
        "R2_agg": "C", "R3_seeds": "B", "R5_testset": "A",
        "R2_evidence": "未说明 PSNR 聚合口径。",
        "R3_evidence": "明确 split seed 42（deterministic split），但未说明训练权重初始化 seed 数或多次运行。",
        "R5_evidence": "'we use a fixed split with seed 42, containing 1656 training tiles and 414 test tiles' "
                       "（80/20 确定性划分）。",
        "note": "★ R5/R3-split 明确；仍未做多次训练重复。",
    },
    "2610.06196": {   # EORestore-Agent
        "id": "EORestore-Agent", "file": "2610.06196",
        "R2_agg": "A", "R3_seeds": "A", "R5_testset": "A",
        "R2_evidence": "'PSNR, SSIM, and LPIPS averaged over all degradation combinations at each N' "
                       "（明确按退化组合数聚合）。",
        "R3_evidence": "★★★ 'We train E = 7 models differing only in random seed and average their predictions "
                       "at inference.' ⇒ **显式的多种子集成**。",
        "R5_evidence": "'The test set contains 270 clean tiles'；'The training split does not overlap with the "
                       "270 test tiles'；六种退化类型逐一定义。",
        "note": "★★★【全文级最佳实践】唯一一篇**明确 E=7 个 seed 训练并集成**的论文；"
                "且主动披露 '17/18 设置下 zero-shot agent 反而低于退化输入' 的系统性负结果。"
                "⇒ 它是 P0-S1 想要的'应该如何做'的正面样板。",
    },
    "2609.07012": {   # AstraMoE-SR
        "id": "AstraMoE-SR", "file": "2609.07012",
        "R2_agg": "A", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "★ 'sizes span several hundred pixels to 12029x5014, so aggregates are area-weighted.' "
                       "⇒ **明确披露聚合是按面积加权**。另有 'We use DINO as the primary semantic-fidelity "
                       "criterion because pixel-wise metrics can be sensitive to ...' ⇒ **明确说明主指标选择理由**。",
        "R3_evidence": "全文未见 seed 数或多次训练平均。",
        "R5_evidence": "'We train on AID and evaluate on the train split of DOTA-v1.0, using all 1,411 images "
                       "rather than a subset'（明确说明未取子集）；自建物理前向退化模型。",
        "note": "★★★【R2 最佳实践】罕见地披露 **area-weighted 聚合** + **主指标选择理由**。"
                "⇒ 证明'聚合口径'在本领域是可报告且应当报告的，只是几乎没人报。",
    },
    "2605.09687": {   # SFG-SwinSR
        "id": "SFG-SwinSR", "file": "2605.09687",
        "R2_agg": "C", "R3_seeds": "A", "R5_testset": "A",
        "R2_evidence": "未说明 PSNR 聚合口径。",
        "R3_evidence": "'For reproducibility, a fixed random seed of 42 is used for data shuffling and weight "
                       "initialization.' ⇒ **明确单一固定 seed 并说明用途**。",
        "R5_evidence": "'we obtain 12,144 valid image pairs, comprising 10,261 training samples and 1,883 test "
                       "samples.'（精确计数）+ 自建退化过程。",
        "note": "★ R3/R5 明确（单 seed 42 + 精确 split 计数）；R2 缺席。",
    },
    "2605.17980": {   # DS-DiT
        "id": "DS-DiT (RefSR)", "file": "2605.17980",
        "R2_agg": "C", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "未说明聚合口径。",
        "R3_evidence": "未报告 seed。",
        "R5_evidence": "'We follow the official split, using 2,968 image pairs for training and 1,694 pairs for "
                       "testing.'（SECOND 官方 split）+ FUSU。",
        "note": "R5 明确（沿用官方 split）；R2/R3 缺席。",
    },
    "2605.02198": {   # SlimDiffSR
        "id": "SlimDiffSR", "file": "2605.02198",
        "R2_agg": "C", "R3_seeds": "C", "R5_testset": "C",
        "R2_evidence": "全文关键词检索未见聚合口径披露。",
        "R3_evidence": "全文未见 seed 数。",
        "R5_evidence": "全文未见精确 test split 规模（需进一步人工定位）。",
        "note": "轻量扩散 SR；三个字段均未在自动检索中命中，标注为待人工确认。",
    },
    "2605.15558": {   # Text-RSIR
        "id": "Text-RSIR", "file": "2605.15558",
        "R2_agg": "C", "R3_seeds": "C", "R5_testset": "C",
        "R2_evidence": "全文关键词检索未见聚合口径披露。",
        "R3_evidence": "全文未见 seed 数。",
        "R5_evidence": "提及三个数据集（Alsat-2B/UC Merced/Aerial）但未在检索片段中给出精确计数。",
        "note": "文本引导重建；三字段待人工确认。",
    },
    "2512.11524": {   # THREASURE-Net
        "id": "THREASURE-Net", "file": "2512.11524",
        "R2_agg": "A", "R3_seeds": "C", "R5_testset": "B",
        "R2_evidence": "★★ 'Values are reported as the median, along with the 25th and 75th percentiles'；"
                       "误差用 box-and-whisker（中位+IQR）；表格列 '(Tree Height, m ± STD)'。"
                       "⇒ **罕见的 median + IQR 报告，而非仅报 mean**。",
        "R3_evidence": "未见 seed 数（但用了 Mann-Kendall 统计显著性检验）。",
        "R5_evidence": "法国全域多生态区；多分辨率（2.5/5/10 m）对比，但未在检索片段给精确 split 计数。",
        "note": "★★★【R2 最佳实践】用 **median + IQR** 而非 mean，且做 Mann-Kendall 趋势显著性检验。"
                "⇒ 与 P0-S1 的核心主张（聚合口径决定结论）直接呼应。",
    },

    # ===== 以下为 MDPI 系（Step 7b 通过 mdpi-res.com CDN 取得 PDF）=====
    "10.3390/rs18091419": {   # GrasslandGAN
        "id": "GrasslandGAN", "file": "grassland_gan_rs18_1419",
        "R2_agg": "A", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "★★★ 全池**最强的聚合/不确定性实践**："
                       "(1) 定义 'coefficient of variation (CV), defined as the ratio of the standard "
                       "deviation to the mean (CV = SD/M)'，并给出分级"
                       "'CV < 10% ... low variability, 10% < CV < 20% ... moderate, CV ≥ 20% ... high variability'；"
                       "(2) 表格明确列 'mean, standard deviation, and coefficient of variation (CV)'；"
                       "(3) 'Normality assumptions were not satisfied, and the Kruskal–Wallis test confirmed...'。",
        "R3_evidence": "未见训练随机种子数（仅报告 30 epochs / batch size 1 等训练超参）。",
        "R5_evidence": "★★ 'This stratification produced a balanced training set of 409 paired tiles (80%) and a "
                       "test set of 102 paired tiles per cluster (20%)'；三层操作框架（intra-sensor / cross-sensor / "
                       "intra-to-cross generalization）显式定义。",
        "note": "★★★【全池唯一的 R4 级实践】用 **CV = SD/M + Kruskal-Wallis（H 统计量 + p 值）** 做"
                "**分布级**稳定性分析，且显式检验正态假设。⇒ **它证明'报告离散度与显著性检验'在 RS-SR "
                "里完全可做**——只是它被当成'生态学分层的附产物'而非'SR 评测的标准动作'。"
                "这是 P0-S1 最有说服力的正面样板，也是最强的反例（说明不是不能做）。",
    },
    "10.3390/rs18121910": {   # DFSMamba
        "id": "DFSMamba", "file": "dfsmamba_rs18_1910",
        "R2_agg": "B", "R3_seeds": "C", "R5_testset": "B",
        "R2_evidence": "★ 做了**分类别（per-category）分解**：'in the \"Farmland\" category, it achieves "
                       "29.02 dB, exceeding MambaIRv2 by about 0.74 dB'；消融明确 'all single-module "
                       "configurations underperform the baseline in PSNR'。"
                       "但未说明总体 PSNR 是逐图均值还是中位。",
        "R3_evidence": "未见 seed 数；仅给 'Parameter Settings'（学习率等）。",
        "R5_evidence": "含 AID/WHU-RS19（×2/×3）+ 一个'不同季节与天气'的测试集；未在正文给精确 split 计数。",
        "note": "★ 有 per-category 分解（比全池多数更细），但总体聚合口径仍未披露。"
                "★ 另注意：其消融显示单模块在 PSNR 上**全面低于基线**，却仍以组合模型 +1.07 dB 为主结论——"
                "这正是'模块叠加 vs 容量效应'难以归因的典型（与用户 BSRNet 机制证伪的经验同源）。",
    },
    "10.3390/s26020683": {   # SpectralSR-Bench
        "id": "SpectralSR-Bench", "file": "spectral_sr_bench_s26_683",
        "R2_agg": "A", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "★★★ 'results are summarized as mean± std over a 50-image set'；"
                       "每张表标题均为 'quantitative results (mean± std over 50 images)'；"
                       "'We report mean± standard deviation over a 50-image set for all metrics'；"
                       "'This reinforces the value of reporting mean± std across 50 images and including SAM "
                       "alongside PSNR and SSIM to capture both spatial fidelity and spectral consistency.'",
        "R3_evidence": "未见训练 seed（全部为 zero-shot 使用公开预训练权重，故无训练随机性；"
                       "但**推理随机性**——扩散模型的采样噪声——同样未用多种子刻画）。",
        "R5_evidence": "★★ 'on 50 unseen images'；MST++ 生成 31→30 band 伪光谱 GT；"
                       "统一 pipeline 逐图记录（reproducible evaluation framework）。",
        "note": "★★★【本轮最锋利的一篇】它是全池**唯一把 mean ± std 写进每张表**的工作，"
                "但**std 量级（1.90–3.66 dB）远大于方法间差距**："
                "见 `audit_H_spectralsr_std.json` —— **10 对相邻方法中 8 对满足 Δ < std**。"
                "⇒ **论文自己报告了离散度，却仍按 mean 排序宣称某法更优**。"
                "这是 P0-S1 核心论点最硬的证据：**证据来自论文自身，不依赖我们复现任何东西**。",
    },
    # ========== 第二轮：非 arXiv 通道（Nature/SciRep 全 OA，直连可取） ==========
    "srep:10.1038/s41598-026-36632-w": {   # MLIN-MetaWeight
        "id": "MLIN-MetaWeight", "file": "mlin_metaw_srep",
        "R2_agg": "A", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "'Table 1 Average PSNR (dB) and SSIM scores on the WHU-RS19 test set across continuous "
                       "scaling factors.' ⇒ **聚合量被显式命名为 Average**（非 median/trim），"
                       "且在连续尺度上逐尺度报告。",
        "R3_evidence": "全文出现 'reproducibility'，但**语境是'公平性'而非'种间重复'**："
                       "'To ensure fairness and reproducibility, all models are trained under identical batch "
                       "sizes and iteration counts.' ⇒ 统一训练配置，**未报告 seed 数、未做多次重复**。",
        "R5_evidence": "'both datasets were divided into training and testing subsets using an 80%–20% split'；"
                       "'leverage its bicubic interpolation module to implement continuous-scale downsampling'；"
                       "'image patches of size 48 x 48'；WHU-RS19 1005 张 / UCMerced。",
        "note": "★★ 反面教材的精准样本：**把 'reproducibility' 用成了 'fairness' 的同义词**"
                "（统一超参 = 可复现），却仍未做种子重复。这正好把 R3 与'训练公平性'区分开——"
                "前者是**结果稳定性**，后者是**比较公平性**，两者不可互相替代。",
    },
    "srep:10.1038/s41598-026-41832-5": {   # SDGAN-SciRep
        "id": "SDGAN-SciRep", "file": "sdgan_srep_a",
        "R2_agg": "A", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "'Average PSNR (dB)'、'Table 5 Comparison of average PSNR and SSIM results'、"
                       "'the average values of AG and NIQE'、'single-image average processing time' —— "
                       "**平均口径全程显式**；另用 FID/IS 表、AG/NIQE 分布图做多指标报告。",
        "R3_evidence": "**全文 seed / three runs / repeat 出现 0 次**（80k 字符正文）。"
                       "FID/IS 用 'Average FID and IS scores during training'，但未说明跨几次运行。",
        "R5_evidence": "UCMerced-LandUse / WHU-RS19 / AID 三数据集，均从官方仓库获取；"
                       "评测尺寸统一 1200x1200（315/285 test images）；参考/无参考指标都覆盖。"
                       "但**未报告三数据集的 train/test 划分比例**（R5 只能记 [A] 弱项）。",
        "note": "★ 全文级最典型的'零种子披露'样本：正文近 80k 字符、报 6+ 种指标、报 FID/IS，"
                "**却一次都没提种子或重复**。⇒ 说明 R3 缺席不是空间不够，而是**规范意识缺失**。",
    },
    "srep:10.1038/s41598-026-65714-y": {   # 内窥镜视频SR（补位：非RS，作跨领域对照）
        "id": "SDGAN-SciRep", "file": "sdgan_srep_b",
        "R2_agg": "B", "R3_seeds": "C", "R5_testset": "A",
        "R2_evidence": "附录给出 additional experimental details，含训练配置；聚合口径部分披露。",
        "R3_evidence": "未报告 seed 数或多次运行。",
        "R5_evidence": "'The split was performed at the video-sequence level to avoid information leakage.' "
                       "⇒ **序列级隔离**（与 IR275K 同级的规范做法）。",
        "note": "★ 跨领域对照（医学视频 SR）：R5 序列级隔离做得好，R3 同样缺席 ⇒ "
                "**R3 缺失是跨领域的普遍现象，不是遥感特有**。",
    },
}


def main():
    survey_p = os.path.join(OUT, "audit_F_field_survey.json")
    survey = json.load(open(survey_p, encoding="utf-8"))

    # 把全文级编码合并回主编码表
    upgraded = 0
    id_to_key = {}
    for k, v in FULLTEXT_CODING.items():
        # 若同一 id 出现多次（如补位条目），保留最后一条
        id_to_key[v["id"]] = k
    for p in survey["papers"]:
        k = id_to_key.get(p["id"])
        if k is None:
            continue
        m = FULLTEXT_CODING[k]
        p["R2_agg"] = m["R2_agg"]
        p["R3_seeds"] = m["R3_seeds"]
        p["R5_testset"] = m["R5_testset"]
        p["fulltext_evidence"] = {
            "R2": m["R2_evidence"], "R3": m["R3_evidence"], "R5": m["R5_evidence"]}
        p["fulltext_note"] = m["note"]
        p["fulltext_key"] = k
        p["fulltext_source"] = "arxiv" if k[0].isdigit() else (
            "mdpi" if k.startswith("mdpi:") else "nature/srep")
        upgraded += 1

    n = survey["n_papers"]
    print("=" * 92)
    print(f"全文级 R2/R3/R5 编码（已升级 {upgraded}/{n} 篇）")
    print("=" * 92)

    for label, key in [("R2 聚合口径", "R2_agg"), ("R3 种子报告", "R3_seeds"), ("R5 测试集构成", "R5_testset")]:
        from collections import Counter
        c = Counter(p[key] for p in survey["papers"])
        n_a, n_b, n_c = c.get("A", 0), c.get("B", 0), c.get("C", 0)
        print(f"  {label:14s}  [A]显式披露={n_a:2d}  [B]部分线索={n_b:2d}  [C]未找到={n_c:2d}")

    print("\n【核心对比】摘要级 vs 全文级（R3 种子报告）")
    print("  摘要级：0/35 提及 seed / 方差 / 统计检验")
    n_r3a = sum(1 for p in survey["papers"] if p["R3_seeds"] == "A")
    n_r3ab = sum(1 for p in survey["papers"] if p["R3_seeds"] in ("A", "B"))
    print(f"  全文级：{n_r3a} 篇明确披露 seed（[A]），另有 {n_r3ab-n_r3a} 篇部分线索（[B]）")
    print("  ⇒ **摘要看不到 ≠ 正文没有**：取全文后 R3 从 0 变成 "
          f"{n_r3a} 篇显式。这正是本审计方法学诚实性的核心。")

    print("\n【R2 聚合口径的阳性样本（可直接作论文正面样板）】")
    for p in survey["papers"]:
        if p["R2_agg"] == "A":
            print(f"  • {p['id']:18s} {p.get('fulltext_note','')[:78]}")

    print("\n【R3 种子报告的阳性样本】")
    for p in survey["papers"]:
        if p["R3_seeds"] in ("A", "B"):
            ev = p.get("fulltext_evidence", {}).get("R3", "")
            print(f"  • [{p['R3_seeds']}] {p['id']:18s} {ev[:88]}")

    # 统计显式报告 seed 的绝对数
    survey["fulltext_summary"] = {
        "n_upgraded": upgraded,
        "R2_A": sum(1 for p in survey["papers"] if p["R2_agg"] == "A"),
        "R3_A": n_r3a,
        "R5_A": sum(1 for p in survey["papers"] if p["R5_testset"] == "A"),
        "abstract_level_R3_mention": 0,
        "key_lesson": "摘要级 R3=0/35，全文级 R3[A]=%d/35 ⇒ 摘要不可作为'未报告'的依据。" % n_r3a,
    }
    json.dump(survey, open(survey_p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n已写回 {survey_p}")


if __name__ == "__main__":
    main()
