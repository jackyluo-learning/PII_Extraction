# CODE_MAP — 论文 ↔ 代码对照与实验状态

_整理于 2026-08-31，基于仓库 HEAD `5b6d27d`。这份文档回答三个问题：论文里的概念对应哪段代码、哪些实验真的跑过、哪些地方代码和论文对不上。_

配套的可视化版本：
- [GCG 攻击全程走查](https://claude.ai/code/artifact/29d5ea65-d8be-4fbd-83cd-b593d80533fa) — 一次攻击从随机乱码到命中早停的逐步拆解
- [实验清单与缺口](https://claude.ai/code/artifact/dc9d2854-37b1-4d05-93d6-062b43794123) — 21 个编号的状态盘点

---

## 0. 开工前必须知道的四件事

1. **当前权威草稿不在仓库里。** 是 `~/Documents/Phd/UAB/Research/usenix_PromptExtraction_PrivacyAuditing.pdf`
   —— *Forcing, Not Remembering: Calibrating Optimization-Based Memorization Audits of Language Models*，
   17 页 USENIX 格式，含 Proposition 1–5、Corollary 1–5、Algorithm 1、forcing capacity β、
   critical capacity k⋆、经验 ε 下界、forcing-honeytoken 防御。**这台机器上只有 PDF，没有 .tex 源码。**

2. **`usenix_paper.tex` 是过期骨架。** 标题还是 "Forcing vs. Memorization"，25 个未填的 `\todo{}`，
   **零 Proposition / 零 capacity / 零 DP / 零 honeytoken**，还残留 44%/45.5% 的旧占位数字。
   `7874_Adversarial_Prompt_Optimi.pdf` 是更早的 ACL 投稿版。**两者都不要当成当前版本。**

3. **`results/` `data/` `models/` 被 gitignore 且本地不存在。** 数据在集群上。
   下面所有 run2 数字取自 `WRITING_GUIDE.md` 和草稿 PDF，不是现跑的。

4. **仓库里有两条并行流水线**，见下一节。这是读代码时最容易踩的坑。

---

## 1. 两条流水线

### B · 当前流水线（forcing 论文用的）

```
experiments.py --exp E1 --model gpt2 --seed 42
   ↓ 每次攻击写 1 行（attempt_log.py 的 27 列 schema）
results/attempts/<run>__<exp>__<shard>.parquet
   ↓ make_tables.py --run-id run2
results/tables/*.txt + *.csv
```

2×2 设计就是 schema 里的两列：`model_state ∈ {finetuned, base}` × `target_membership ∈ {trained, control}`，
`train_frequency = 0` 编码对照记录。**论文里所有数字都出自这条。**

### A · 旧流水线（ACL 投稿时代）

```
run_experiments.py --stage data|train|attack|adaptive|discovery|eval|defense|ablation
   ↓
results/*.json + results/summary_tables.txt
```

`baselines.py`、`defense_eval.py`、`linguistic_analysis.py` 属于这一条。

### 两条之间唯一的连接

`run_E12_defenses`（B）复用了 A 的原语——`build_benign_queries`、`compute_prompt_perplexity`、
`extract_prompt_features`、`FEATURE_NAMES`——但读的是新的 attempt 日志。

> ⚠️ **不要拿 A 的产出去填 forcing 论文的表。** 指标口径不同：A 是 record-level，
> B 是 per-(person, field) 微平均（`eval_cfg.metric_unit = "person_field"`）。

---

## 2. 论文概念 → 代码位置

| 论文 | 代码 | 备注 |
|---|---|---|
| `A_k`，k 个自由 token | `config.py` `GCGConfig.prompt_length_k = 20` | E3 用 `PII_CAP_K` 分片覆盖 |
| `Dec(M, p)` 贪心解码 | `experiments.py` `InstrumentedGCG._check` | `do_sample=False`，`max_new_tokens = T + 20` |
| `⊑` 归一化子串 | `evaluate.py` `exact_match` | 数值字段 digits-only；`len(t) < 4` 拒绝 |
| `EMR(·)` | `make_tables.py` `_cluster_emr_ci` | person-clustered bootstrap，N=10000 |
| `α_k` forcing floor (Def. 2) | 同上，筛 `target_membership == "control"` | |
| `τ̂rec` (Eq. 7) | `make_tables.py` `_cluster_diff_ci` | **论文 Table 4 用的 Newcombe 区间不在代码里**，代码出 bootstrap |
| `k_min(t)` (Def. 3) | `make_tables.py` `_kmin_table` | 需要 E3 数据 |
| `β` forcing capacity (Def. 3) | `make_tables.py` `capacity_e3` | **量纲与论文不一致**，见 §5 |
| `k⋆` (Def. 4) | `make_tables.py` `_crossing_k` | 已算 1% 与 5% 两档 |
| `Mem(t)` (Def. 5) | **未实现** | |
| `H(t)` 自信息 | `attempt_log.py` `target_self_information` | held-out ref model = `ling_cfg.reference_model = "gpt2"` |
| AUC (§3.6) | `make_tables.py` `_auc` | Mann-Whitney U，score = `−final_target_nll` |
| `TPR@α` (Def. 6) | `make_tables.py` `_tpr_at_fpr` | **已实现且 Table 1 在打印，但没进论文** |
| `ε̂` (Cor. 4) | **未实现**（全仓库 grep 不到） | Table 2 却标了 ✓ |
| ACR (§3.5) | `make_tables.py` `acr_e13` | `ACR≥1 ⟺ k_min < target_len_tokens`，依赖 E3 |
| `τ̂mod` (Prop. 4) | `experiments.py` `run_E2_control_model` | 未跑 |
| Honeytoken (Prop. 5) | `experiments.py` `run_E12_defenses` | 未跑 |
| A1 可交换性 | `experiments.py` `run_E17_match_controls` | **有放回**匹配 |

---

## 3. 21 个实验编号的状态

| 编号 | 是什么 | 代码 | 状态 | 论文里 |
|---|---|---|---|---|
| **E1** | 负对照：8 probe × 双臂 × 4 模型 | `run_E1_negative_controls` | ✅ **跑过 run2** | Table 4/5 · Fig 2/3 |
| **E17** | 协变量匹配 | `run_E17_match_controls` | ✅ 跑过（E1 前置） | §6.1 · Alg 1；平衡表未报 |
| **E9** | ROC / AUC / TPR@FPR | `make_tables.table1_main` | ✅ 有数据 | AUC 进了；TPR@α 未报 |
| **E16** | 秩反转 | `make_tables.rank_inversion_e16` | ✅ 有数据 | **草稿中出现 0 次** |
| E3 | 容量扫描 k ∈ {1…64} | `run_E3_capacity_sweep` + `slurm/exp_capacity.slurm` | ⏳ 待跑 | Fig 4 只有解析曲线 + 1 点 |
| E5 | 频次剂量响应 | `run_E5_frequency_response` | ⏳ 待跑 | §3.6 提到思路 |
| E2 | 对照模型（base）臂 | `run_E2_control_model` | ⏳ 待跑 | §3.3 留给更大研究 |
| E7 | 预算匹配自然 prompt | `run_E7_budget_matched` | ⏳ 待跑 | §4 声称 compute-matched |
| E10 | Pythia + Pile 外部效度 | `run_E10_pile_membership` | ⏳ 待跑（需 `PII_PILE_SHARD`） | §9 future work |
| E12 | 三个防御 @ 固定 FPR | `run_E12_defenses` | ⏳ 待跑（需 E1/E4 日志） | §8 整节零数字 |
| E4 | anchored/free 同 k 并排 | `run_E4_anchored_gcg` | ⏳ 待跑 | Table 5 的 anchored 行其实来自 E1 |
| E13 | ACR 头对头 | `make_tables.acr_e13` | ⏳ 被 E3 卡住 | §5.4 future work |
| E14 | soft-prompt 范数扫描 | 仅 config 网格 + schema 列，**无 driver** | ❌ | §4 提到 |
| E6 | 规模 + 多 seed（n≥761/臂） | 非 driver，是配置（`PII_N_INDIVIDUALS` / `PII_N_CONTROLS`） | ❌ | §9 Limitations |
| E21 | prompt 语言学（24 特征） | `linguistic_analysis.py`（流水线 A） | ❌ 未接入 B | Appendix D 描述特征 |
| E20 | 收敛曲线 | 仅旧流水线 ablation | ❌ | — |
| E11 | 现代模型 | config 里被注释掉 | ❌ | — |
| E8 · E15 · E18 · E19 | 仅在 EXPERIMENTS.md 的 tier 列表被点名 | **无规格、无代码** | ❌ | — |

> `EXPERIMENTS.md` 写着「See the pasted experiment list for the full E1–E21 spec」——
> **那份完整规格不在仓库里**，所以 E8/E15/E18/E19 只有编号。

### run2 的实际配置（`slurm/submit_per_model.sh`）

| 模型 | 训练方式 | max_targets | gcg_iters |
|---|---|---|---|
| gpt2 124M | 全量微调 | 25 | 200 |
| gpt2-medium 355M | 全量微调 | 12 | 120 |
| pythia-1.4b | **LoRA** r=16 (`query_key_value`) | 20 | 150 |
| pythia-2.8b | **LoRA** r=16 | 12 | 120 |

单 seed（42），字段只有 `ssn,email`。行数 = (2 臂 × n 人) × 2 字段 × 8 probe ≈ **2208 行**，
这就是整篇论文的全部实验记录。**逐模型迭代预算不同**，所以 τ̂ 不可跨模型比较。

---

## 4. 论文里有什么

### 带实验数字的只有 4 处，全部出自 E1

| 位置 | 内容 | 出自 |
|---|---|---|
| Table 4 | 逐模型 n / EMR(D) / EMR(C) / τ̂rec[CI] / AUC | `table1_main` |
| Table 5 | probe 谱系 8 行池化 | `table2_probe_spectrum` |
| Figure 2 | ROC 空间散点 | = Table 4 的两列 |
| Figure 3 | forcing 轴柱状图 | = Table 5 的两列 |

另有两处只在正文提到、**没有数值**：§7.1「训练损失降到近零」（`train_meta.json` 的 `pii_eval_losses`）、
§7.3「random-record match rate 近零」。

### 纯概念、不含数据

Table 1（三种设定）· Table 2（形式对象 ✓/◦）· Table 3（probe 定性排序）· Table 6（记号）·
Figure 1（总览）· **Figure 4**（Prop. 1 的解析曲线 + 唯一 1 个实测红点，k=20 处的 39%）。

### run2 的结果

**Table 4** — E1, `gcg_free`, k=20, seed 42, ssn+email：

| 模型 | n | Fixed | EMR(D) | EMR(C)=α | τ̂rec [95% CI] | AUC |
|---|---|---|---|---|---|---|
| GPT-2 124M | 25 | 0.0 | 52.0 | **52.0** | +0.0 [−26, 26] | 0.51 |
| GPT-2-M 355M | 12 | 0.0 | 66.7 | 33.3 | +33.3 [−6, 61] | 0.57 |
| Pythia-1.4B | 20 | 0.0 | 60.0 | 50.0 | +10.0 [−19, 37] | 0.45 |
| Pythia-2.8B | 12 | 0.0 | 16.7 | 0.0 | +16.7 [−10, 45] | 0.47 |

**Table 5** — probe 谱系（池化）：

| probe | 自由容量 | conditioning | 梯度优化 | EMR(D) | EMR(C) | τ̂rec |
|---|---|---|---|---|---|---|
| fixed | 0 | 有 | 无 | 0.0 | 0.0 | +0.0 |
| piicompass | 0 | 真前缀 | 无 | 0.0 | 0.0 | +0.0 |
| piiscope | 0 | 有 | 无 | 0.0 | 0.0 | +0.0 |
| random_restart | k=20 | 无 | **无** | 0.0 | 0.0 | +0.0 |
| gcg_fluent | 受限 | 无 | 有 | 39.1 | **42.0** | −2.9 |
| gcg_free | k=20 | 无 | 有 | 50.7 | **39.1** | +11.6 |
| gcg_anchored | k=20 | 有 | 有 | 71.0 | **62.3** | +8.7 |
| softprompt | ∞ | 无 | 有（连续） | 100.0 | **100.0** | +0.0 |

八个 probe 构成一个受控对比矩阵，四组关键对比：

```
fixed     vs gcg_anchored   同 conditioning，差「优化」        0    → 71.0
gcg_free  vs random_restart 同容量同无提示，差「优化 vs 预算」  0    → 50.7
gcg_free  vs gcg_anchored   同优化同容量，差「conditioning」   50.7 → 71.0
gcg_free  vs softprompt     容量轴的两端                      39.1 → 100（对照臂）
```

即 2×2 析因：**conditioning 单独什么也做不到（fixed = random_restart = 0），
优化单独就能到 50.7%，两者叠加 71.0%。**

---

## 5. 已知的代码 ↔ 论文不一致

按「补实验前必须先定掉」的紧要程度排：

| # | 位置 | 情况 |
|---|---|---|
| 1 | **`β` 的量纲** | 论文 Def. 3 是 `median H(t)/k_min(t)`（**bits/token**）；`capacity_e3` 算的是 `linregress(H_bits → k_min).slope`（**token/bit**），互为倒数。而紧接着的验收检查又打印 `beta / log2\|V\|`，只有 bits/token 讲得通。**E3 一跑就产出这个数，先定义清楚。** |
| 2 | **`n_random_restarts`** | `config.py` 写死 512，不从 GCG 实际 forward 数派生。而 gcg_free 跑 120 轮评估 61,440 条候选，**差 120 倍**。论文 §4 和 Appendix C 称其「at GCG's exact forward-pass budget / exact rather than nominal」。真正对齐的是 E7。 |
| 3 | **`forward_passes` 口径不一** | GCG 记**批量调用次数**（1 梯度 + 8 候选批 = 9/轮）；`random_restart` 记**生成次数**；`piiscope` 记 prompt 条数；`softprompt` 记优化步数。跨 probe 比较需换算。 |
| 4 | **`ε̂` 无实现** | Cor. 4 的经验 ε 下界，Table 2 标 ✓，代码里没有。Table 1 已有 (TPR, FPR) 和 Clopper–Pearson 所需输入，补约十行。 |
| 5 | **λ 无扫描 driver** | `adaptive_fluency_lambda = 0.1` 是单个浮点数，没有任何实验遍历多个 λ。Cor. 3 的「流畅度 = 容量」等价关系因此**从未被检验**——不是检验失败，是没检验。 |
| 6 | **E14 只有壳** | `softprompt_norm_grid` 在 config，`softprompt_norm` 在 schema，但 `_probe_static` 永远返回 `None`，无 driver 填它。 |
| 7 | **CI 方法不一致** | §6.3 写「95% person-clustered bootstrap」，Table 4 caption 写「Newcombe (Wilson-score)」。代码只有 bootstrap，Newcombe 是手算的。 |
| 8 | **`fixed` 的实现** | 论文 §4 描述为「best of k variants」（direct/completion/few-shot/role-play）。E1 的 `_run_fixed_probe` 是**单条 prompt 单次贪心**；多变体版本在 `baselines.py` 和 E7 的 `fixed_budget`（5 变体）。 |
| 9 | **模板数** | 论文 §6.1 说 7 种模板；`TEMPLATES` 实际有 **9 个**（多了 `onboarding_ticket`、`verification_note`），且 `data_cfg.template_types` 那个 7 项列表**从未被读取**。 |
| 10 | **anchored 的目标不对称** | `gcg_anchored` 的目标是裸值（6 token），`gcg_free` 是含标签（9 token）。目标更短本身更易命中，这个因素和 conditioning 混在一起。 |
| 11 | **训练用了 LoRA** | 论文 §6.2 只说「end-to-end with AdamW」。实际 `use_lora_for()` 阈值 0.5B：两个 GPT-2 全量微调，**两个 Pythia 走 LoRA**（r=16，只挂 `query_key_value`，lr=2e-4）。 |
| 12 | **padding 进 loss** | `CorpusDataset` 用 `padding="max_length"` 到 512，`labels = input_ids.clone()`，**pad 位置没置 −100**。短文档（如 `contact_list` 单行）大部分序列是 padding。 |
| 13 | **E17 有放回匹配** | `run_E17_match_controls` 是 with replacement（50 个对照撑 100 个训练记录），论文未提。影响独立二项假设与有效 n。 |
| 14 | **D/C 不相交无断言** | `generate_individuals(n, seed)` vs `generate_individuals(n, seed + 1000)`，是种子偏移；**没有对生成值做 disjointness 断言**。Appendix B 称「disjoint seed stream」。 |
| 15 | **`β` 在 k_min=∞ 时未定义** | Def. 3 取中位数，但攻击失败时 `k_min = ∞`。Pythia-2.8B 的 EMR(C)=0/12 ⇒ 中位数是 ∞。需要取值约定。 |

---

## 6. 代码算了但论文没用（最便宜的补充）

| 量 | 代码状态 | 论文状态 |
|---|---|---|
| `TPR@1%` / `TPR@5%` | `table1_main` 一直在打印 | Table 4 没有；而 §3.6 要求五项一起报，Def. 6 专门定义了它 |
| McNemar p 值 | `_paired_mcnemar` 已算 | §6.3 说会用，全文仅此一次提及，正文无 p 值 |
| 秩反转 E16 | `rank_inversion_e16` 已算 | 草稿中 "rank inversion" 出现 0 次 |
| `random_record_match` | 每行日志都记 | 只有定性「near zero」 |
| E17 协变量平衡 | `results/e17_matches_*.json` 已落盘 | Alg 1 步骤 2 要求报告分布重叠，未报 |

**前四项是搬运，不需要任何新运行。**

---

## 7. 零 GPU 成本的存量

`dump_all_results.py --run-id run2` 从**同一份 run2 日志**切出 8 张表：

1. 总览（模型/probe/字段/seed/计数）
2. 逐模型主表 = Table 1
3. **逐模型 × 逐 probe（4 × 8）**
4. **逐字段（ssn / email）× 逐 probe** ← 论文缺的 per-field 分解
5. **频次剂量响应（脚本自称 "poor-man's E5"）**
6. 子串膨胀 guard
7. 秩反转
8. 算力剖面（forward_passes / wallclock）

第 5 项成立的原因：语料按 `frequency_groups = {10:1, 30:5, 60:20}` 生成，
`cap_targets` 又「evenly across the registry so all frequency tiers stay represented」，
所以 **E1 的日志里现成就有 4 个频次档位**（1 / 5 / 20 + 对照的 0）。
E5 那个「拟合截距 vs 直接测 α」的交叉验证可以先做近似版。

---

## 8. 补跑优先级

| 顺序 | 实验 | 一次运行能点亮什么 | 需要重训？ |
|---|---|---|---|
| 1 | **E3 容量扫描** | `β`、`k⋆`、`Mem(t)` 三个 ◦ 变 ✓；Figure 4 从「理论曲线 + 1 点」变实测曲线；**顺带解锁被卡住的 E13 ACR** | 否 |
| 2 | **E5 频次响应** | forcing floor 的**第二个独立估计**（拟合截距 vs 直接测），`frequency_e5` 自动打印 `WITHIN CI` / `OUTSIDE CI` | 完整 7 档需要；用现有 4 档不需要 |
| 3 | **E6 加对照样本** | α 的 CI 由对照臂样本量决定；`build_corpus()` 里 `corpus = pii_docs + public`，**负对照从不进语料，所以加对照不用重训** | **否**（加训练记录才要） |
| 4 | **E2 对照模型臂** | `τ̂mod`，补上 2×2 的下半行，Prop. 4 夹逼与证伪检验 | 否 |
| 5 | E7 / E10 / E12 | E7 让 compute-matched 名副其实；E10 堵住「合成数据」质疑；E12 给 §8 补数字 | 否 |

```bash
# E3（k 分片，13 个 k × 模型 × seed）
sbatch --export=ALL,PII_CAP_K=20 slurm/exp_capacity.slurm

# E2 / E5（单任务）
python experiments.py --exp E2 --model gpt2 --seed 42
python experiments.py --exp E5 --model gpt2 --seed 42

# 加对照（不重训）
PII_N_CONTROLS=800 python run_experiments.py --stage data

# Tier-1
sbatch --export=ALL,EXP=E7,MODEL=gpt2,SEED=42,PII_RUN_ID=run2 slurm/exp_tier1.slurm

# 出表（CPU，秒级）
python make_tables.py --run-id run2
python dump_all_results.py --run-id run2
```

---

## 9. 关键实现细节速查

**GCG 内循环**（`InstrumentedGCG.run`，k=20 / B=256 / 每步 512 候选 / minibatch 64）

```
每轮:  1 次前向反向 → grads (20, 50257)
       每行 topk(256) → 20 × 256 = 5120 个候选（每个只改 1 格）
       random.sample → 512 个 → 分 8 批实测 → argmin
       free_ids 无条件替换；best_free 只在改善时更新（允许爬坡）
       每 10 轮: _check(free_ids) 自由生成 + exact_match，命中则 break
结束:  若从未命中，用 best_free 补检一次
计数:  forward_passes = 9/轮（1 梯度 + 8 候选批），generate 不计入
```

- 梯度只对输入层 one-hot 求导；`_load_model` 里模型权重 `requires_grad_(False)`，**全程无 optimizer**
- loss 用 teacher forcing（目标 token 拼进输入），判定用自由生成——**低 loss 不蕴含成功**
- `logits[start : start+T]`，`start = P + k + S − 1`（第 i 位 logit 预测第 i+1 个 token）
- `final_target_nll = best_tloss × T` = 整串的负对数概率（nats），取负后作为 ROC 的连续分数
- `steps_to_first_success` **被量化成 10 的倍数**（只在 `it % 10 == 0` 检查）；
  `first_success == steps_run == N` 说明是靠收尾补检命中的

**判定规则**（`evaluate.exact_match`，全仓库唯一）

- 比 `value` 不比 `target_text`（模型不需要复现 `"SSN: "` 标签）
- `ssn` / `phone` / `credit_card` → `_digits_only`（两边都抹掉非数字）；其余 → `normalize_text`（NFKC + 小写 + 折叠空白，**标点保留**）
- **子串包含**，不是相等；`len(t) < 4` 拒绝

**数据生成**（`data_generation.build_corpus`）

- `Faker.seed(42)` → 100 训练个体；`Faker.seed(1042)` → 50 负对照
- `corpus = pii_docs + public`，**负对照只进 `target_registry`，从不进语料**
- 1360 篇 PII 文档 + 10 万公开段落 ⇒ PII 占比 ≈ 1.34%
- 表面扰动 `perturb_prob=0.5`：数值字段换分隔符、文本字段改大小写、标签换变体；
  **email 绝不动**（`@` 和 `.` 要逐字匹配）；canonical 值永不改变

---

## 10. 仓库文档的时效性

10 份 markdown 的年代差别很大，冲突时以「当前」组为准。

| 文档 | 状态 | 说明 |
|---|---|---|
| `CODE_MAP.md` | **当前** | 本文件：论文↔代码对照 + 实验状态 |
| `REVISION_PLAN.md` | **当前** | run2 最终数据 + 写作计划 |
| `WRITING_GUIDE.md` | **当前** | 逐节写作指南，含 run2 数字与可粘贴的 LaTeX |
| `EXPERIMENTS.md` | **当前** | E 套件设计与 tier 顺序（但完整 E1–E21 规格不在仓库里） |
| `RUN.md` | **当前** | SLURM 运行手册 |
| `IMPROVEMENT_PLAN.md` | 历史 | round-1 修订策略，forcing 转向之前 |
| `CHANGES.md` | 历史 | round-1 变更日志，指向 IMPROVEMENT_PLAN |
| `PAPER_UPDATE_PLAN.md` | 历史 | 针对**更早**的一次运行（GPT-2 × 3 seeds），已被 run2 取代 |
| `Reviews.md` | 历史 | 早期 ACL 版投稿的审稿意见 |
| `IRI_outline.md` | **另一篇论文** | IEEE IRI 2026，6 页，"afterlife of personal data" 框架，对应 `IRI_paper.tex`。**不是 forcing 论文，不要混用结论。** |

历史组里的计划都以 `usenix_paper.tex` 为工作文件、并引用已不成立的运行结果，
照着做会把过期数字重新引进来。

---

## 11. Claude Code 的持久记忆（全文）

同样的路由信息写在
`~/.claude/projects/-Users-xuqiluo-PycharmProjects-PII-Extraction/memory/`，
每次会话开始时自动加载。**那个目录在仓库之外、也不进 git**，所以三条记忆的全文
原样抄录在下面——克隆这个仓库的人不需要那个目录也能拿到全部上下文。

索引文件 `MEMORY.md`：

```markdown
- [CODE_MAP.md is the entry point](pii-code-map-is-entry-point.md) — read it before exploring the PII_Extraction code; two pipelines, only E1 has run, 15 code/paper mismatches.
- [Forcing draft lives outside the repo](forcing-draft-lives-outside-repo.md) — the current paper is a PDF in ~/Documents/Phd/UAB/Research, not the repo's stale usenix_paper.tex.
- [Which repo docs are current](pii-repo-doc-currency.md) — REVISION_PLAN/WRITING_GUIDE/CODE_MAP are live; IMPROVEMENT_PLAN/PAPER_UPDATE_PLAN/CHANGES/Reviews are historical; IRI_* is a separate paper.
```

### 11.1 `pii-code-map-is-entry-point.md`

```markdown
---
name: pii-code-map-is-entry-point
description: CODE_MAP.md is the entry point for the PII_Extraction repo; it records the paper-to-code mapping, experiment status, and 15 known code/paper mismatches.
metadata:
  type: project
---

`CODE_MAP.md` (repo root, written 2026-08-31) is the routing document for this
project. Read it before exploring the code. It records:

- the **two parallel pipelines** — `experiments.py` + `attempt_log` +
  `make_tables` (current, forcing paper) vs `run_experiments.py`'s 8 stages
  (old ACL era). Metric units differ (per-(person,field) micro-average vs
  record-level), so their outputs must never be mixed.
- paper concept → code location table (α_k, τ̂rec, β, k⋆, TPR@α, ACR …)
- status of all 21 E-numbers: **only E1 has ever run** (run2), plus E17 as its
  prerequisite; E9/E16 are free analyses with data; seven drivers are implemented
  but unrun; E8/E15/E18/E19 have no spec anywhere in the repo
- 15 verified code/paper mismatches, incl. β's dimension being inverted between
  Def. 3 and `capacity_e3`, `n_random_restarts` hardcoded at 512 (not
  budget-matched), `ε̂` having no implementation, and no λ-sweep driver
- `dump_all_results.py` yields 8 extra tables from the existing log at zero GPU
  cost, including a "poor-man's E5" frequency dose-response

**Why:** the repo has 10 markdown files and two pipelines; without this map a
session re-derives the same facts or edits the wrong file.
**How to apply:** read `CODE_MAP.md` first, then the draft PDF
([[forcing-draft-lives-outside-repo]]). See also [[pii-repo-doc-currency]].
```

### 11.2 `forcing-draft-lives-outside-repo.md`

```markdown
---
name: forcing-draft-lives-outside-repo
description: The authoritative "Forcing, Not Remembering" draft is a PDF outside the repo; usenix_paper.tex is a stale scaffold.
metadata:
  type: project
---

The current authoritative draft is
`~/Documents/Phd/UAB/Research/usenix_PromptExtraction_PrivacyAuditing.pdf`
— "Forcing, Not Remembering: Calibrating Optimization-Based Memorization Audits
of Language Models", 17 pages, USENIX format. Propositions 1–5, Corollaries 1–5,
Algorithm 1, forcing capacity β, critical capacity k*, empirical ε lower bound,
forcing-honeytoken defense. **Only the PDF exists on this machine — no .tex.**
Extract it with pypdf (poppler is not installed, so the Read tool cannot render it).

Do NOT treat these as current: `usenix_paper.tex` (old scaffold, title "Forcing
vs. Memorization", 25 unfilled `\todo{}`, zero propositions, stale 44%/45.5%
placeholder numbers) or `7874_Adversarial_Prompt_Optimi.pdf` (earlier ACL
submission).

**Why:** working from the repo's .tex silently discards the entire theory section
and regresses the paper by two revisions.
**How to apply:** read the PDF above as the single source of truth; ask for the
.tex if edits are needed. Start from [[pii-code-map-is-entry-point]].
```

### 11.3 `pii-repo-doc-currency.md`

```markdown
---
name: pii-repo-doc-currency
description: Which of PII_Extraction's markdown docs are current vs historical, and that IRI_paper.tex is a separate second paper.
metadata:
  type: project
---

The repo has 10 markdown files of very different vintage.

**Current** — `CODE_MAP.md` (paper↔code map + experiment status),
`REVISION_PLAN.md` and `WRITING_GUIDE.md` (both carry the final run2 numbers:
4 models, seed 42, ssn+email), `EXPERIMENTS.md` (E-suite design), `RUN.md`
(SLURM howto).

**Historical, do not act on** — `IMPROVEMENT_PLAN.md` and `CHANGES.md`
(round-1 revision, pre-forcing-pivot), `PAPER_UPDATE_PLAN.md` (written for an
earlier run of GPT-2 × 3 seeds, superseded by run2), `Reviews.md` (reviewer
comments on the older ACL-era submission).

**`IRI_outline.md` + `IRI_paper.tex` are a SEPARATE second paper** — IEEE IRI
2026, 6 pages, "afterlife of personal data / data-reuse" framing. Not the
forcing paper; don't merge their claims.

**Why:** several plans target `usenix_paper.tex` and cite numbers from runs that
no longer stand, so following them silently reintroduces stale results.
**How to apply:** when a plan doc conflicts with `WRITING_GUIDE.md` or
`CODE_MAP.md`, the latter two win. See [[pii-code-map-is-entry-point]].
```

> 三条记忆和本文档如果哪天不一致，**以本文档为准**——记忆是路由用的摘要，
> 内容会随实验推进而过时（尤其「只有 E1 跑过」这条）。跑完新实验后记得同步更新
> §3 的状态表和 `pii-code-map-is-entry-point` 那条记忆。
