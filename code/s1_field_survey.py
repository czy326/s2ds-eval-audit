#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --- portable roots injected by the packaging script ---
import os as _os
PROJ_ROOT = _os.environ.get("S2DS_AUDIT_ROOT", _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
OUT_DIR   = _os.environ.get("S2DS_AUDIT_OUT", _os.path.join(PROJ_ROOT, "results"))
DATA_ROOT = _os.environ.get("S2DS_DATA_ROOT", _os.path.join(PROJ_ROOT, "data"))
# --- end injected ---

"""
P0-S1 Audit / Step 5 (扩样版 v2): 领域抽样编码表 —— 2023-2026 RS-SR 论文"省略了 R1-R7 哪几项"。

⚠️ 方法学边界（必须写进论文）:
  本表基于**公开摘要 + 检索片段 + 可核查的正文片段**编码，未逐篇下载 PDF 通读。
  ⇒ R2/R3/R4/R6/R7 这类"未报告"判定，摘要里看不到 ≠ 正文里没有。
  ⇒ 因此本表分三档证据级别:
     [A] 摘要/检索片段直接可见（如声称的 dB 增益、数据集名、是否开源）
     [B] 正文片段可见（如 Table 1 的完整指标列、明确的退化设定）——比 [A] 更进一步，
         但仍不等于全文审计（正文可能有实验设置章节报告了 seed）
     [C] 需全文核对（如 seed 数、聚合口径、统计检验）——本表标记为"待核"
  只有 [A]/[B] 档结论可写进论文的"省略率"分子；[C] 档必须先取全文再定稿。

  关键设计：对每一篇给出 **可核查的增益引用原句**（gain_quote）与 **来源 URL**，
  使编码可复核。凡是拿不到具体 dB 数的，claimed_gain_dB=None，不臆造。
"""
import json, os, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = OUT_DIR

# 种子噪声门槛（来自本审计 C/D 线，逐数据集）
SEED_SD_MEDIAN = 0.088     # dB（全库中位）
SEED_SD_RANGE = (0.049, 0.248)
# 各数据集种子噪声 sd（用于"增益是否落在该数据集噪声内"的判定）
DATASET_NOISE = {"AID": 0.248, "RSSCN7": None, "UCMerced": None, "WHU-RS19": None}


def P(id, venue, year, task, datasets, gain, gain_vs, gain_quote, code,
      metric, ev_agg="C", ev_seeds="C", ev_test="C", url="", note=""):
    """构造一条编码。ev_* ∈ {A,B,C}"""
    return {
        "id": id, "venue": venue, "year": year, "task": task,
        "datasets": datasets, "claimed_gain_dB": gain, "claimed_vs": gain_vs,
        "gain_quote": gain_quote, "code": code, "metric_mention": metric,
        "R2_agg": ev_agg, "R3_seeds": ev_seeds, "R5_testset": ev_test,
        "ev_test": ev_test, "url": url, "note": note,
    }


PAPERS = [
    # ============ 组 1：单图 RS-SR (SISR) —— RS 专用数据集 ============
    P("DBTSR", "Expert Systems with Applications", 2026, "SISR-RS",
      ["AID", "DOTA", "DIOR", "RSSCN7"], 0.12, "SwinIR (avg); 对 TTST +0.05",
      "outperforms ... SwinIR and the advanced TTST in terms of PSNR by an average of approximately 0.12 dB and 0.05 dB",
      "github.com/TeresaTing/DBTSR", "PSNR (abstract)",
      note="摘要只提 PSNR；未提 seed / 方差 / 检验。"),
    P("ORDiffSR", "Expert Systems with Applications", 2026, "SISR-RS (diffusion)",
      ["AID", "DOTA", "DIOR", "WHU-RS19"], None, "CNN/Transformer/GAN/diffusion（未给具体 dB）",
      "significantly outperforms existing CNN, Transformer, GAN, and diffusion model approaches",
      "github.com/TeresaTing/ORDiffSR", "subjective + objective",
      note="只给效率对比（150× faster），性能增益定性描述，未给 dB。"),
    P("PLAN", "DOAJ (Parallel Lattice Attention Network)", 2026, "SISR-RS",
      ["AID", "UCMerced", "WHU-RS19"], 0.07, "ESTNet/BMFENet",
      "outperforming state-of-the-art methods such as ESTNet and BMFENet by at least 0.07 dB in PSNR and 0.0210 in SSIM",
      None, "PSNR + SSIM", note="报告运行时间；未提 seed/方差/检验。"),
    P("DFSMamba", "Remote Sensing (MDPI) 18(12), 1910", 2026, "SISR-RS (Mamba+DFT)",
      ["AID", "其他 5 个（摘要未列全）"], 1.07, "MambaIRv2 on AID×3",
      "On the AID×3 task, it achieves a PSNR of 31.48 dB, exceeding MambaIRv2 by 1.07 dB",
      None, "PSNR（摘要）", note="消融给 0.85 dB 模块增益；未提 seed/方差/检验。"),
    P("SFG-SwinSR", "arXiv 2605.09687", 2026, "SISR-RS (Swin, SFG-FFN)",
      ["SpaceNet", "SEN2VENμS"], None, "Swin2SR",
      "On SpaceNet, it achieves 45.19 dB PSNR and 0.9852 SSIM",
      None, "PSNR + SSIM",
      url="http://arxiv.gg/abs/2605.09687",
      note="★ 摘要给出绝对 PSNR（45.19 dB）但未给相对增益 dB；未提 seed/方差。"),
    P("NGram-MoSE", "arXiv 2606.08535", 2026, "SISR-RS (efficient Transformer)",
      ["地理隔离 OOD 测试集", "滑坡分割基准"], None, "重量级 Transformer 参照",
      "achieves 31.68 dB PSNR while reducing FLOPs by 14× ... yielding a 4.47% absolute gain in mAP@50 over bicubic",
      None, "PSNR + 下游 mAP@50",
      url="https://arxiv.org/abs/2606.08535",
      note="★ 报告 OOD 测试集 + 下游任务，但摘要未给相对 dB 增益、未提 seed。原话强调 robustness。"),
    P("MT-Hybrid", "IEEE TGRS Vol 64", 2026, "SISR-RS (Mamba-Transformer)",
      ["（摘要未列）"], None, "CNNs / Transformers / Mamba 类",
      "we propose a hybrid Mamba–Transformer (MT) framework",
      None, "（摘要未给具体指标）", note="摘要未给数字。"),
    P("LocalStateSpace", "中国图象图形学报", 2026, "SISR-RS (VSSM)",
      ["UCMerced", "RSSCN7", "AID", "WHU-RS19"], None,
      "FeNet/HauNet/MambaIR/RCAN/HAT/SwinIR/MambaformerSR/Rep-Mamba",
      "在 UCMerced 数据集×4 放大下，本文方法在 PSNR 上取得最高值，同时计算量显著低于其他方法",
      None, "PSNR + SSIM", ev_test="B",
      note="★ 正文明确退化方式（bicubic）——R5 部分信息可见。"),
    P("JNUN-CA", "西北大学学报(自然科学版) 56(1):108-117", 2026, "SISR-RS (通道注意力)",
      ["WHU-RS19"], 0.19, "次优方法（WHU-RS19）",
      "WHU-RS19 测试集上 PSNR/SSIM 分别为 28.70 dB / 0.7539，分别比次优方法提高了 0.19 dB 和 0.0066",
      None, "PSNR + SSIM", note="只报单数据集（WHU-RS19，101 张测试图）。"),
    P("MLIN-MetaWeight", "Scientific Reports", 2026, "连续尺度 RS-SR (跨域)",
      ["WHU-RS19", "UCMerced"], None, "连续尺度 SOTA",
      "demonstrating state-of-the-art performance and outperforming existing methods in both visual quality and quantitative metrics",
      None, "PSNR/SSIM（图中标注）", note="定性描述 SOTA，未给 dB。"),
    P("PLGMamba", "（HSI-SR，期刊）", 2026, "HSI-SR (状态空间)",
      ["Chikusei", "Houston", "Pavia", "GF-5"], None, "CNN/Transformer/其他 SOTA",
      "PSNR of 44.058, SAM 1.3404, and ERGAS 10.069 at ×2 scale (Chikusei); PSNR 39.804 ... at ×4 (Houston)",
      None, "PSNR + SAM + ERGAS",
      url="https://radaislice.com/news/ai-state-space-model-enhances-hyperspectral-image-resolution",
      note="★ 报三指标；摘要给绝对 PSNR 未给相对增益；训练 200 epochs / RTX 3060。"),

    # ============ 组 2：多图/多时相 SR (MISR) ============
    P("Sen4x", "IEEE JSTARS Vol 19, 11042-11051", 2026, "MISR+SISR 混合 (Sentinel-2)",
      ["Sentinel-2 + Pléiades Neo (Hanoi)"], None, "SOTA SR baselines（下游分类）",
      "We find that they lead to a significant performance improvement over state-of-the-art super-resolution baselines",
      None, "下游土地覆盖分类 + 视觉质量", ev_test="B",
      url="https://xplorestaging.ieee.org/document/11435384/",
      note="★ 罕见地把 SR 评测锚定到下游分类任务；但摘要未给 dB、未提 seed/检验。"),
    P("THREASURE-Net", "arXiv 2512.11524", 2026, "MISR (Sentinel-2 时序 → 冠层高度)",
      ["Sentinel-2 time series + LiDAR HD (France)"], None, "其他 SOTA 方法",
      "the 2.5 m model achieved a Mean Absolute Error (MAE) of 2.63 m ... THREASURE-Net compares to other state-of-the-art methods",
      None, "MAE (高度) + 分类",
      url="https://www.alphaxiv.org/overview/2512.11524v3",
      note="★ 任务型 SR（回归到 LiDAR 参考），非 PSNR 叙事。"),
    P("IR275K", "arXiv 2607.22380 (Benchmark)", 2026, "MISR (红外多帧)",
      ["IR275K (594 seq / 275,196 frames)"], 0.35, "红外单图 SR 参照（0.35--0.52 dB）",
      "It achieves 33.19dB PSNR, outperforming infrared single-image super-resolution references by 0.35--0.52 dB at substantially lower computational cost",
      "github.com/InfraRecon7/IR275K", "PSNR + FLOPs + params", ev_test="B",
      url="https://arxiv.org/abs/2607.22380",
      note="★ 明确提供 'reproducible X4 evaluation protocol' + sequence-level splits —— 本领域少见的协议自觉。"
           "但摘要仍未提 seed/方差/统计检验。"),
    P("S3-ESRGAN", "（Sentinel-2 + UAV, Univ. Twente）", 2026, "跨传感器 SR (5×)",
      ["Sen2UAV (428,000 patch pairs, 33 scenes)"], None, "SOTA SR 方法",
      "S3-ESRGAN consistently outperforms state-of-the-art methods, producing sharper textures, enhanced edges, and improved spectral fidelity",
      None, "视觉 + 光谱保真（消融）",
      url="https://research.utwente.nl/en/publications/ce847b6d-4fbc-4e27-9a90-11cd7658afa8",
      note="★ 大数据集（42.8 万对）却仍用定性 SOTA 表述；消融只证模块贡献。"),
    P("GrasslandGAN", "Remote Sensing (MDPI) 18(9), 1419", 2026, "GAN SR (草地, 分层评测)",
      ["PlanetScope 3m + UAV 0.03m (Texas)"], None, "SRGAN/ESRGAN/bicubic",
      "Landscape heterogeneity strongly influenced downscaling outcomes. SRGAN performance declined ... ESRGAN demonstrated consistently robust performance",
      None, "PSNR + SSIM + variability analysis", ev_test="B",
      url="https://www.mdpi.com/2072-4292/18/9/1419/html",
      note="★★ 少数做了'variability analysis'（报告性能稳定性）的论文——R4 种子噪声相关意识可见。"
           "但按景观异质性分层，不等于按 seed 分层。"),
    P("Text-RSIR", "arXiv 2605.15558", 2026, "文本引导重建/传输",
      ["Alsat-2B", "UC Merced", "Aerial Image"], None, "（语义保真对比）",
      "achieves reconstruction PSNRs of 16.36 dB, 26.87 dB, and 27.41 dB, respectively",
      "github.com/haoyangofficial/textrssr", "PSNR",
      url="https://arxiv.gg/abs/2605.15558",
      note="摘要给绝对 PSNR（16-27 dB 跨度极大，说明任务难）；未给相对增益。"),
    P("DS-DiT (RefSR)", "arXiv 2605.17980", 2026, "参考图引导 SR (diffusion)",
      ["SECOND", "FUSU"], None, "现有 RefSR 方法",
      "Experimental results across multiple datasets and scaling factors show that DS-DiT outperforms existing methods in both quantitative metrics and visual fidelity",
      None, "定量指标 + 视觉",
      url="https://www.pith.science/paper/2605.17980",
      note="★ 论文自己指出 'perceptual quality ... may still receive higher scores'（对感知指标的怀疑）——与评测批判同调。"),

    # ============ 组 3：盲 SR / 退化未知 ============
    P("HAC-MoE", "Neurocomputing Vol 685", 2026, "盲 SR (行星遥感, 无监督)",
      ["Ceres-50 (自建 benchmark)"], None, "无监督盲 SR 基线",
      "achieves competitive quantitative performance under physically motivated synthetic degradations",
      "github.com/2333repeat/HAC-MoE", "定量（未在摘要给 dB）", ev_test="B",
      url="https://acm-stag.literatumonline.com/doi/10.1016/j.neucom.2026.133615",
      note="★★ 摘要用词极克制（'competitive'、'in the evaluated setting'、"
           "'simplified surrogate analysis ... rather than a direct global guarantee'）——罕见的自我设限式表述。"
           "自建 benchmark + 开放代码与数据。"),
    P("DiffBSR", "（DOAJ 收录）", 2026, "盲 SR (扩散, 未知核)",
      ["Gaofen"], None, "SOTA CNN 方法",
      "our DiffBSR improves the learned perceptual image patch similarity metric by 32%–76% and achieves higher segmentation accuracy",
      None, "LPIPS + 分割精度",
      url="https://doaj.org/article/b98e0f0f1167469299cbc9cac67c9755",
      note="★ 报告相对 LPIPS 改善（32-76%）而非 PSNR dB —— 指标口径不可比。"),
    P("AstraMoE-SR", "arXiv 2609.07012", 2026, "盲去抖+SR (卫星 pushbroom)",
      ["DOTA-v1.0 (1,411 images, 自建退化前向模型)"], 0.64, "StableSR",
      "improving on StableSR, the strongest learned baseline, by 0.64 dB PSNR, 15.2% LPIPS, and 0.091 in DINO feature similarity",
      None, "PSNR + LPIPS + DINO", ev_test="B",
      url="https://arxiv.org/html/2609.07012v1",
      note="★ 报告了 3 个指标，且明确 self-degradation 前向模型（可复现性相关）；"
           "但'唯一在所有保真指标上超过 no-restoration baseline 的方法'这一表述暴露了基线普遍不可靠。"),
    P("BKX-HMM", "IEEE TPAMI 2026", 2026, "无监督盲超分 (HSI)",
      ["（摘要未列）"], None, "无监督 HSI-SR 方法",
      "建立了基于隐马尔可夫模型的统一统计框架 ... 首个无需任何标签、全自动盲估计的无监督超分方案",
      None, "（“砸钱换效果”批判式叙事）",
      url="https://gitcode.csdn.net/69e9de2a0a2f6a37c5a276c3.html",
      note="★ 论文自陈行业误区：'预设死板的模糊核和波段选择' —— 与本审计 R5（基线/退化口径）问题同源。"),
    P("UDAMSR", "Engineering (Elsevier/CAE)", 2026, "无监督退化感知 SR (光谱/作物)",
      ["3 设备 × 2 空间尺度 × 2 地理区域"], None, "有监督/无监督基线",
      "mean PSNR of 32.78, mean RMSE of 6.93, mean SSIM of 0.89, and mean SAM of 0.131 ... strong generalization across different spatial scales, geographic regions, devices, and data types",
      None, "PSNR + RMSE + SSIM + SAM", ev_test="B",
      url="https://www.sciencedirect.com/science/article/pii/S2095809926001682",
      note="★★ 明确的跨设备/跨尺度/跨区域泛化评测设计 + 4 指标。这是本池里最接近'协议有序'的一类，"
           "但摘要用 mean 而不是 median/trim，且未见 seed 或配对检验。"),

    # ============ 组 4：全色锐化 / 高光谱（指标族齐全） ============
    P("VolumeNet+TT", "ACM (ICMIP/相关会议)", 2026, "全色锐化 (HS)",
      ["WorldView3 ×4"], None, "PNN / PanNet / PSMD-Net",
      "Table 1: PSNR 30.43/30.03/31.15/31.17/31.75 ... SAM 0.072/0.075/0.072/0.068/0.067 ... ERGAS 4.627/5.089/4.280/4.260/4.040",
      None, "PSNR+SSIM+CC+SAM+ERGAS+params+time", ev_test="B",
      url="https://dl.acm.org/doi/abs/10.1145/3785443.3785445",
      note="★★ 罕见地把 5 个指标全列成表。但仅单一场景（WorldView3 ×4），且选择标准是"
           "'best accuracy during training'（best-checkpoint 选择，未提 seed）。"),
    P("HSISR-KAN", "（HSI-SR, 综述/方法）", 2026, "HSI-SR (KAN)",
      ["ARAD_1K"], None, "CNN/Transformer 基线",
      "EigenSR-β | ARAD_1K 4× | PSNR=40.46dB, SSIM=0.9605, SAM=1.18°",
      None, "PSNR + SSIM + SAM",
      url="https://www.emergentmind.com/topics/hyperspectral-single-image-super-resolution-hs-sisr",
      note="★ 综述汇总表显示该子领域'指标族'已相对统一（PSNR/SSIM/SAM/ERGAS），但仍无 seed/检验列。"),
    P("UDAMSR-mean", "ScienceDirect (crop sensing)", 2026, "光谱 SR（作物）",
      ["多设备/多区域"], None, "无监督 SR 基线",
      "best overall performance in the comprehensive evaluation, with a mean PSNR of 32.78",
      None, "PSNR+RMSE+SSIM+SAM",
      note="与 UDAMSR 同源，此处单列以记录'mean 聚合'表述。"),

    # ============ 组 5：评测 / 基准 / 协议（同调文献） ============
    P("GeoSR-Bench", "arXiv 2605.00310", 2026, "SR 基准（下游任务整合）",
      ["~36,000 地点, 500m-0.6m, 跨平台"], None, "GAN/Transformer/neural operator/diffusion",
      "improvements in traditional SR metrics often do not correlate with gains in task performance, and the correlations can be negative",
      None, "感知质量 + 下游任务（270 设置）", ev_test="A",
      url="https://scholar.google.com.sg/citations?user=X2Wfl1UAAAAJ",
      note="★★★ 【同调】直接证伪'PSNR 提升 = 有用'。270 设置 / 9 SR 模型 / 5 下游任务。"
           "这是 P0 叙事最直接的支撑文献，但不是关于**排名在多协议间不稳定**（我们的增量）。"),
    P("NTIRE2026-SR", "arXiv 2604.14558 (CVPRW)", 2026, "挑战赛报告 (×4 SR)",
      ["DIV2K (100 test) + LSDIR"], None, "（Track 1 PSNR / Track 2 感知）",
      "PSNR and seven perceptual metric scores are evaluated on the DIV2K test set (100 images). ... A 4-pixel border is excluded ... on the Y channel",
      None, "PSNR + SSIM + LPIPS + DISTS + NIQE + ManIQA + MUSIQ + CLIP-IQA", ev_test="A",
      url="https://arxiv.org/html/2604.14558v1",
      note="★★★【同调·最重要的协议标尺】官方明确：8 指标、4-pixel border、Y 通道、DIV2K 100 张测试。"
           "⇒ 说明'口径'确实被官方固定，但**学术论文普遍不照抄这套口径**（per-paper 各取所需）。"
           "这正是 R1/R2 的核心落差来源。"),
    P("NTIRE2026-ESR", "Codabench (CVPRW)", 2026, "高效 SR 挑战赛",
      ["DIV2K_LSDIR_valid/test"], None, "SPAN (基线)",
      "The threshold PSNR is set to 26.90 dB on DIV2K_LSDIR_valid and 26.99 dB on DIV2K_LSDIR_test ... greater weight will be given to teams ... in more than one aspect",
      None, "PSNR 阈值 + Runtime + FLOPs + Params", ev_test="A",
      url="https://www.codabench.org/competitions/13553/",
      note="★★ 官方用'单点阈值 + 加权'来对抗排名脆弱性，而非报告置信区间。"
           "⇒ 官方也在用一个 'hard threshold' 回避统计功效问题。"),
    P("SpectralSR-Bench", "Sensors 26(2), 683 (MDPI)", 2026, "光谱 SR 比较评测",
      ["MST++ 伪光谱 GT (31→30 band)"], None, "CNN/GAN/diffusion/classical",
      "The workflow was designed to be modular and reproducible ... Centralized logging records model metadata, timestamps, and per-image metrics, supporting traceability and repeatability",
      None, "PSNR（按 ×2/×4/×8 分档）", ev_test="A",
      url="https://doi.org/10.3390/s26020683",
      note="★★★【同调】明确以'reproducible evaluation protocol'为卖点，逐图记录指标、"
           "zero-shot 公平比较。⇒ 与本审计 A 线（逐图 path 一致性）同一诉求。"
           "但它做的是**跨方法公平性**，我们做的是**同方法跨口径排名稳定性**。"),

    # ============ 组 6：2026 其他新增（占位核实中，保留可核查项） ============
    P("SyMTRS", "arXiv 2604.21801", 2026, "SISR-RS (对称/多任务)",
      ["（待核）"], None, "（待核）",
      "（未取得可核查增益原句——列入待核队列）",
      None, "（待核）", ev_test="C", url="https://arxiv.org/abs/2604.21801",
      note="候选池成员；未取得摘要级增益，暂不计入分子。"),
    P("NTIRE2026-IR", "arXiv 2604.21312 (CVPRW)", 2026, "红外 SR 挑战赛报告",
      ["（挑战赛数据）"], None, "（挑战赛 baseline）",
      "（未取得可核查增益原句——列入待核队列）",
      None, "（待核）", ev_test="C", url="https://arxiv.org/abs/2604.21312",
      note="候选池成员；NTIRE 系，预期协议自觉度高，待取全文。"),
    P("SlimDiffSR", "arXiv 2605.02198", 2026, "轻量扩散 SR",
      ["（待核）"], None, "（待核）",
      "（未取得可核查增益原句——列入待核队列）",
      None, "（待核）", ev_test="C", url="https://arxiv.org/abs/2605.02198",
      note="候选池成员；待核。"),
    P("SDGAN-SciRep", "Scientific Reports 16, 11971", 2026, "GAN SR",
      ["（待核）"], None, "（待核）",
      "（未取得可核查增益原句——列入待核队列）",
      None, "（待核）", ev_test="C", url="https://www.nature.com/srep/",
      note="候选池成员；待核。"),
    P("EORestore-Agent", "arXiv 2610.06196", 2026, "复合退化恢复 (agent)",
      ["Landsat-8 合成基准 (6 退化)"], 2.3, "最强重训 all-in-one baseline（2.3--3.2 dB）",
      "EORestore-Agent improves PSNR by 2.3 to 3.2 dB over the strongest retrained all-in-one baseline on composites of two to six degradations, whereas zero-shot natural-image agents fall below the degraded input in PSNR in 17 of 18 settings",
      None, "PSNR + SSIM + LPIPS (+ 逐步骤接受判据)", ev_test="B",
      url="https://arxiv-vanity.com/papers/2610.06196",
      note="★★★【同调·方法论价值最高】用'reference-free verifiable per-step decision'替代'不可测目标'，"
           "明确报告 '17/18 设置下 zero-shot agent 反而低于退化输入' —— 罕见的系统性负结果披露。"),
]

# ------------------------------------------------------------------ 统计
def pct(a, b):
    return f"{a}/{b} ({100.0*a/b:.1f}%)" if b else "n/a"

def main():
    n = len(PAPERS)
    print("=" * 92)
    print(f"RS-SR 领域抽样编码表 v2（{n} 篇；2026 年为主，含少量 2025）")
    print("=" * 92)
    print(f"种子噪声实测（本审计 C/D 线）：全库 sd 中位 {SEED_SD_MEDIAN} dB，范围 {SEED_SD_RANGE[0]}–{SEED_SD_RANGE[1]} dB\n")

    graded = [p for p in PAPERS if p["ev_test"] != "C" or p["url"]]
    quantified = [p for p in PAPERS if p["claimed_gain_dB"] is not None]

    # ---- [1] 可核查增益 vs 噪声 ----
    print(f"[1] 给出**可核查**具体 dB 增益的论文: {pct(len(quantified), n)}")
    for p in sorted(quantified, key=lambda x: (x["claimed_gain_dB"] is None, x["claimed_gain_dB"])):
        g = p["claimed_gain_dB"]
        tag = "⚠️<噪声中位" if g < SEED_SD_MEDIAN else ("~噪声上沿" if g < 0.25 else "超噪声")
        print(f"      {p['id']:16s} +{g:.2f} dB  {tag:12s}  vs {p['claimed_vs'][:44]}")

    # ---- [2] 定性/未给 dB ----
    qual = [p for p in PAPERS if p["claimed_gain_dB"] is None]
    print(f"\n[2] 未给具体 dB（定性 SOTA / 只给绝对 PSNR / 只比效率）: {pct(len(qual), n)}")
    for p in qual:
        print(f"      {p['id']:16s} — {p['claimed_vs'][:56]}")

    # ---- [3] 数据集使用 ----
    print(f"\n[3] 数据集使用（可核查）")
    from collections import Counter
    c = Counter()
    for p in PAPERS:
        for d in p["datasets"]:
            c[d] += 1
    for d, k in c.most_common(14):
        print(f"      {d[:38]:38s} {k} 篇")

    # ---- [4] 代码可用性 ----
    with_code = [p for p in PAPERS if p["code"]]
    print(f"\n[4] 给出代码/数据链接: {pct(len(with_code), n)}")
    for p in PAPERS:
        print(f"      {p['id']:16s} {'✅ ' + p['code'] if p['code'] else '❌ / 未在摘要给出'}")

    # ---- [5] R2/R3/R5 证据级别分布 ----
    print(f"\n[5] R2(聚合口径) / R3(seed) / R5(测试集构成) 的证据级别分布")
    for key, label in [("R2_agg", "R2 聚合口径"), ("R3_seeds", "R3 种子报告"), ("R5_testset", "R5 测试集构成")]:
        cnt = Counter(p[key] for p in PAPERS)
        a, b, cc = cnt.get("A", 0), cnt.get("B", 0), cnt.get("C", 0)
        print(f"      {label:12s} [A]摘要可见={a:2d}  [B]正文片段可见={b:2d}  [C]需全文={cc:2d}")

    # ---- [6] 全池层面：0 篇在摘要中出现 seed / 统计检验 ----
    seed_words = re.compile(r"\b(seed|seeds|random seed|variance|std\b|standard deviation|"
                            r"confidence interval|significance|statistical test|Wilcoxon|"
                            r"p-value|p value|bootstrap)\b", re.I)
    agg_words = re.compile(r"\b(median|mean|average|trimmed|aggregat)\b", re.I)
    seeds_in_abs = [p["id"] for p in PAPERS
                    if seed_words.search(p["gain_quote"] or "")]
    agg_in_abs = [p["id"] for p in PAPERS
                  if agg_words.search(p["gain_quote"] or "")]
    print(f"\n[6] 【核心结论】在可核查的增益原句中出现 …")
    print(f"      seed / variance / 统计检验 关键词的论文: {pct(len(seeds_in_abs), n)}   {seeds_in_abs}")
    print(f"      聚合口径关键词 (mean/median/trim) 的论文: {pct(len(agg_in_abs), n)}   {agg_in_abs}")
    print(f"      ⇒ 这两个字段在摘要层几乎完全缺席。")

    # ---- [7] 下游/任务型评测的论文（与评测科学同调） ----
    task_like = ["GeoSR-Bench", "Sen4x", "THREASURE-Net", "NGram-MoSE", "UDAMSR",
                 "EORestore-Agent", "GrasslandGAN", "IR275K", "SpectralSR-Bench",
                 "NTIRE2026-SR", "NTIRE2026-ESR"]
    print(f"\n[7] 明确把 SR 评测锚定到**下游任务/协议复现**的论文: {pct(len(task_like), n)}")
    print(f"      {', '.join(task_like)}")
    print(f"      ⇒ 这些是 P0 的'同调盟友'，但它们的落点是'PSNR 与下游不相关'；"
          f"\n        我们的落点是'方法排名在多协议/多口径下不稳定'——互补而非重复。")

    summary = {
        "n_papers": n,
        "n_quantified_gain": len(quantified),
        "n_qualitative_only": len(qual),
        "n_with_code": len(with_code),
        "seed_sd_median_dB": SEED_SD_MEDIAN,
        "seed_sd_range_dB": list(SEED_SD_RANGE),
        "dataset_counts": dict(c),
        "seeds_or_stats_in_abstract": seeds_in_abs,
        "aggregation_mention_in_abstract": agg_in_abs,
        "task_or_protocol_oriented": task_like,
        "evidence_legend": {
            "A": "摘要/检索片段直接可见",
            "B": "正文片段可见（如完整指标表、明确退化设定）",
            "C": "需全文核对（未取得可核查片段）",
        },
        "papers": PAPERS,
    }
    with open(os.path.join(OUT, "audit_F_field_survey.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=1)
    print(f"\nwrote audit_F_field_survey.json  (n={n})")


if __name__ == "__main__":
    main()
