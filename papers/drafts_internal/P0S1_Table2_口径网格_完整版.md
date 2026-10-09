# P0-S1 / Table 2 完整版：协议口径敏感性网格

> 数据源：`E:\论文5\audit\out\audit_B_protocols.json`（`s1_audit_core.py` 生成，`run_audit_chain.py` 可复算）
> 生成日期：2026-10-09
> 说明：ρ = 该口径下方法排名与 `psnr_mean` 排名的 Spearman 秩相关；**FLIP** = 冠军（top-1）与 `psnr_mean` 冠军不同。

---

## 主表（论文 Table 2 直接可用）

| 口径 | AID (46 runs) | RSSCN7 (39) | UCMerced (39) | WHU-RS19 (36) |
|---|---|---|---|---|
| `psnr_mean`（参考） | 1.000 | 1.000 | 1.000 | 1.000 |
| `psnr_trim10` | 0.979 | 0.987 | **0.996** | 0.934 |
| `psnr_trim25` | 0.962 | 0.986 | 0.981 | 0.833 |
| `ergas_mean` | 0.943 | **0.982** ✗ | 0.945 | 0.944 |
| `psnr_median` | **0.882** ✗ | **0.502** ✗ | **0.818** ✗ | **0.749** ✗ |
| `ssim_mean` | 0.868 | **0.957** ✗ | 0.747 | 0.807 |
| `sam_mean` | 0.813 | **0.535** ✗ | 0.793 | **0.272** ✗ |
| `lpips_mean` | **0.534** | **0.894** ✗ | **0.549** | 0.860 |

✗ = 该口径下冠军被翻掉。

**翻转计数**：`psnr_median` **4/4**；`ssim_mean` 1/4；`ergas_mean` 1/4；`sam_mean` 2/4；`lpips_mean` 1/4。合计 **9 次翻转**，其中 `psnr_median` 一个口径贡献了 4 次。

---

## 冠军身份明细（用于论文正文说明"换成哪个方法"）

| 数据集 | `psnr_mean` 冠军 | 被翻成 |
|---|---|---|
| AID | `rcan_small_aid_s2028` | `rcan_small_aid_s2027`（同族，换 seed） |
| RSSCN7 | `rcan_small_rsscn7_s2027` | `rcan_small_rsscn7_s2028` / `…_s2026`（同族，换 seed） |
| UCMerced | `rcan_small_ucmerced_s2028` | `rcan_small_ucmerced_s2027`（同族，换 seed） |
| **WHU-RS19** | `rcan_small_whurs19_s2028` | **`litecnn_whurs19_s2028`（换模型族）** |

**⚠️ 这个明细必须写进论文，且必须诚实处理**：

- AID / RSSCN7 / UCMerced 的 `psnr_median` 翻转**发生在同一方法族的不同 seed 之间**（`rcan_small_*_s2026/2027/2028`）。
  ⇒ 这仍是有意义的结论：**在 0.018–0.039 dB 的中位效应量级下，"同族换 seed"就足以改写冠军** —— 也就是"冠军"这个头衔本身不稳定。
  ⇒ 但**不可**写成"中位数会让 A 方法打败 B 方法"这种跨族反转（那只有 WHU-RS19 的 `sam_mean` 成立）。
- **WHU-RS19 的 `sam_mean` 是唯一的跨族翻转**：`rcan_small`（注意力族）→ `litecnn`（轻量 CNN 族），ρ=0.272。
  ⇒ 这是全表最强的单一证据，论文正文应以此为主例。

---

## 三条论文级结论

### 结论 1：中位聚合在 4/4 数据集上翻掉冠军，而截断均值不翻

`psnr_median` 翻转 4/4；`psnr_trim10` / `psnr_trim25` 保持 ρ ≥ 0.833（多数 ≥ 0.93），且**一次都不翻**。

**判读**：两者都是稳健聚合，差别在于——中位数依赖**中间序统计量**（对分布中心的轻微偏移敏感），截断均值保留**主体平均**（继承了均值对中心偏移的不敏感性）。因此**不稳定源位于分布尾部与中心附近，不在整体形状**。

**可操作诊断**：某数据集排名对口径高度敏感时，先查**逐图分数分布**，而不是换指标。

### 结论 2：`sam_mean` 在 WHU-RS19 上 ρ=0.272 —— 全研究最低

且它是唯一跨模型族的翻转点。WHU-RS19 同时是**最小测试集（101 张）**——与 §4.3 的"噪声随测试集规模单调下降"互为印证。

### 结论 3：语义/感知类指标（`sam` / `lpips`）与 PSNR 排名脱节最严重

`lpips_mean` 在 AID（0.534）与 UCMerced（0.549）跌到 0.55 附近，`sam_mean` 在 WHU-RS19 跌到 0.272。
⇒ **保真度指标族与感知指标族给出的排名几乎是两套排名**。这在实践中意味着：论文若只报 PSNR 排名而宣称"重建质量最好"，与感知意义的"最好"是两回事。

---

## 复算备忘

```bash
# 复算本表
cd E:/论文5/audit/code
"C:/Users/陈正洋/.workbuddy/binaries/python/versions/3.13.12/python.exe" run_audit_chain.py
# 产物：E:/论文5/audit/out/audit_B_protocols.json
```

口径定义（`s1_audit_core.py`）：
- `psnr_mean` / `ssim_mean` / `ergas_mean` / `sam_mean` / `lpips_mean`：逐图指标取算术平均后排名。
- `psnr_median`：逐图 PSNR 取中位数。
- `psnr_trim10` / `psnr_trim25`：逐图 PSNR 去掉最低/最高各 10%（或 25%）后取均值。
- 排名方向：psnr / ssim 越大越好；ergas / sam / lpips 越小越好（已在脚本内统一为"越好排名越前"）。
