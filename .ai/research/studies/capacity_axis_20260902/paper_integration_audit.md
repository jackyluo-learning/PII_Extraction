# E3 与当前论文草稿的整合审计

日期：2026-09-19
论文项目：Overleaf `usenix-PromptExtraction_PrivacyAuditing`
线上主文件：`usenix_paper_v2.tex`
线上编译状态：17 页
研究：`capacity_axis_20260902`（E3）

## 结论

E3 不能作为一组新数字直接追加到现稿。它一方面给论文的核心直觉提供了更干净的证据：在同一模型、同一攻击和同一目标集合中，控制组 forcing floor 随自由提示长度 `k` 强烈上升；另一方面，它反驳了现稿把 `k_min≈H/β` 当作简单比例模型、把 `β` 当作可迁移常数的经验叙述。因此，整合 E3 需要同时改写理论框架、算法、实验设置、结果、摘要和结论。

最稳妥的论文主线是：

1. E1 展示 forcing 在多个模型和多类 probe 上确实存在；
2. E3 在 GPT-2 124M 内部用完整容量扫描表明 forcing floor 随 `k` 急剧上升；
3. 当前样本无法确认 1% forcing-floor 操作点；
4. 简单的通用 `β` 比例模型不符合 E3 数据；
5. 当前 D/C 差异尚未被分辨，但这不等于两组等效或模型没有记忆。

E3 当前仍是条件性重分析：`completion_accepted=false`，不得写成已经验收的确认性研究。

## 当前线上稿件已经包含什么

| 论文内容 | 当前证据 | 现稿中的主要结论 | 审计判断 |
|---|---|---|---|
| E1：四模型、固定 `k=20` 的 D/C 比较 | 单训练 seed；SSN 与 email | GPT-2 为 52%/52%；跨模型 forcing 很高 | 可保留为早期现象展示，但必须标明单 seed 和目标单位 |
| E1：八类 probe 谱 | 同一轮 E1 日志 | 控制组从 0% 上升到 soft prompt 的 100% | 可作为 probe 表达能力的描述性证据；多处预算并不严格可比 |
| E9：NLL/AUC/ROC | 从 E1 同一日志派生，并非独立实验 | AUC 约 0.45–0.57；GPT-2 chance-level ROC | 已从 E3 权威分析撤回，应从论文删除 |
| E17：D/C 匹配 | 已运行 | 论文称 matched controls，但没有报告平衡表 | 必须披露 email 平衡失败和有放回匹配 |
| E16：rank inversion | 已计算 | 未进入论文 | 可在重新定义连续分数后决定是否使用；现在不应补入 |
| 理论 capacity bound 与单个经验点 | Figure 4 | uniform SSN 理论曲线旁放 pooled 39%@`k=20` | 两者不是同一总体，应替换 |
| 经验 `ε`、TPR@固定 floor | 论文方法与贡献声称存在 | 把 D/C 点解释成经验隐私下界 | 当前没有完整实现和结果表，只能保留理论推论 |
| capacity limiting、honeytoken、perplexity filter | 理论方案/代码壳 | 作为防御章节 | E12 未运行，必须明确写为 proposed defenses |

现稿的实验结果主要来自 E1/run2。E2、E4、E5、E7、E10、E12、E13、E14、E21 仍未运行、未完成或没有完整 driver，不能作为完成的论文证据。

## E3 可以加入论文的内容

### 主文：H1 容量趋势

控制组 forcing floor 随 `k` 呈强烈的总体上升排序趋势：

- Spearman `ρ=0.988965`；
- 95% 人员聚类 bootstrap CI `[0.977915, 0.994490]`；
- 原始 `p=0.000100`，H1–H4 家族的条件性 Holm `p=0.000400`；
- 控制组命中率从 `k≤3` 的 0 次观察，上升至 `k=6` 的 27.3%、`k=20` 的 80.67%、`k=64` 的 96.67%。

论文可以写“总体呈强烈上升趋势”。该检验不证明每一对相邻 `k` 都严格单调。范围必须写清楚：GPT-2 124M、25 名控制人物、每人 SSN/email 两个目标、三个攻击 seed；三个 seed 不是三次独立微调。

### 主文或限制：H2 的 1% 操作点未分辨

`k=1,2,3` 虽然观察到零次控制命中，但保守 95% 上界仍为 10.33%，所以当前样本没有确认任何 `k` 满足 1% forcing-floor 上限。

这不是“不存在安全 `k`”的证据，也不是 H2 已被反驳。论文的 Algorithm 1 应改为：先指定容忍的 forcing floor，并用其置信上界选择 `k*`；零命中的点估计不能直接当作 0%。若命中继续为零，按当前保守约定约需每组 286 人才能把上界压到 1%。

### 主文：H4 要求修订容量模型

在披露的 Weibull 工作模型下：

- `log(k_min) = intercept + γ log(H) + error`；
- `γ=3.484486`；
- 95% CI `[2.811469, 4.209360]`；
- 原始 `p=0.000100`，Holm `p=0.000400`。

简单比例关系 `k_min≈H/β` 要求 `γ=1`，而区间排除 1。因此 E3 不支持把 `β` 当作通用、可迁移的模型常数。`H/k_min` 最多可保留为这批样本的描述性比率；现稿的 `Mem(t)` 公式、ACR 关联和 Algorithm 1 的 “fit β” 都需要重审。

### 字段级暴露更正后的 H3

50个D字段值中只有48个实际进入恢复的训练文本，两个SSN没有出现。按事后字段暴露更正排除这两个D-SSN、一个原始E17匹配C和一个事后近邻C后，`k=20` 的结果是：

- D = 81.94%；
- C = 81.94%；
- `D−C = 0.00` 个百分点；
- 95% CI `[-8.96, +9.25]`；
- 原始 `p=1.000000`，Holm `p=1.000000`。

正确解释仍是“当前样本没有分辨出成员相关差异”，而不是D/C已经等效、模型没有记忆或隐私安全。实际E3路径丢失逐目标E17配对；第二个原始匹配C未被攻击，只能从实际攻击过的C-SSN中按相同三项协变量选择最近者。因此这是字段数量平衡后的事后更正，不是完整配对的预注册分析。遍历其余所有可用近邻C时，`k=20` 点差只在`[-1.389,+0.694]`个百分点间变化，说明近邻选择不驱动H3的未检出结论。

### 补充材料：H5 与描述图

字段暴露更正后，H5 的观测最大点为 `k=4`，峰位置 bootstrap 包络为 `[4,48]`；二次曲率为`-0.00213`，95% CI `[-0.01607,0.01210]`。argmax规则提示内部最大值，但没有定位稳定最优点，曲率也未独立支持峰形；它在设计中就是低功效探索性假设，不应进入摘要、贡献列表或结论。

以下内容适合补充材料：

- 完整 14 点 D/C 容量曲线；
- SSN/email 字段拆分计数；
- 逐靶标热图；
- 各攻击 seed 的首次命中；
- 7/50 个控制目标和 6/50 个训练目标出现的“命中后在更大 `k` 又失败”现象。

字段图只能作描述性结果；email 的匹配失败，不能从字段 D/C 差异直接作成员性因果解释。

## 现稿必须修正的结论与方法

### 证据冲突

1. **删除“训练损失接近零，因此内容逐字存在于权重中”。** 恢复的 PII evaluation loss 为 `2.6761→2.2048→2.0889`，不支持 near-zero。soft prompt 对 D/C 都达到 100% 也不能证明训练记忆。
2. **删除 NLL/AUC/ROC 结果。** 包括摘要、贡献列表、Methods、Table 4 AUC 列、Results 的 continuous-score 小节、讨论与结论中的 chance-level ROC。若删除这个连续分数，依赖它的 TPR@固定阈值和 `ε` 最大化也必须删除或重新定义。
3. **撤回“compute-matched random search”。** random restart 固定为 512 个候选，而典型 GCG 约评估 61,440 个候选，相差约 120 倍；真正的 E7 尚未运行。
4. **把“模型从未见过 C”改成“C 未进入本次微调语料”。** 当前设计没有排除基础模型预训练污染。
5. **修正训练方法。** Pythia 实际使用 LoRA；现稿不能称四个模型都 end-to-end fine-tuned。
6. **修正数据生成描述。** 实现有 9 个模板，现稿写 7 个。
7. **修正样本单位。** Table 5 的 69 是人物数；若每人两个字段，应是 138 个 person-field targets。
8. **统一不确定性计算。** Table 4 的手工 Newcombe 区间、Methods 的 person-clustered bootstrap 和 Open Science 的“无手工转录”互相冲突。
9. **披露匹配失败。** email 的字符长度、token 长度和 `H(t)` 的 SMD 分别约为 0.503、0.613、0.513，均超过预定 0.1 阈值；SSN 平衡通过。
10. **把三种防御明确标为提案。** 在 E12 完成前，不能称为经过实验验证的防御。

### 方法中承诺、结果中没有交付的内容

- TPR@固定 forcing floor；
- 经验 `ε` 下界；
- McNemar 检验结果；
- E17 overlap/balance 表；
- random-record match 的计数与区间；
- base-model control arm；
- frequency dose-response。

这些项目要么完成并报告，要么从方法、Table 2 的勾选项、贡献和结论中删去。

## 对线上论文的具体修改位置

| 位置 | 修改 |
|---|---|
| Abstract | 用 E3 的容量趋势替换 52%/52% 与 chance-level ROC 主叙述；去掉 compute-matched、经验 `ε` 已测和防御已验证的暗示 |
| Introduction / Contributions | 保留“控制组必要”的理论贡献；把 `β`/`k*` 从已验证框架改成待校准对象；加入“1% 操作点未分辨” |
| §3.4 Capacity Calibration | 区分理论 `k*_thy` 与经验 `k*`；用 floor 的置信上界选择；删除通用比例 `β` 的经验承诺 |
| `Mem(t)` / ACR 关联 | 在 H4 反例下重新推导或降级为假设，不再称已测量的统一量 |
| Algorithm 1 | 加入样本量/上置信界规则和匹配平衡门；删除当前未实现的 AUC/TPR/`ε` 报告项 |
| Experimental Setup | 新增 E3：一个 GPT-2 checkpoint、25 人/组、两个字段、三个攻击 seed、13 个正容量和 `k=0` anchor；披露条件性来源状态 |
| Results §7.1 | 删除“content is memorized”与 exactly-zero 表述；把 E1 作为早期现象结果 |
| Results §7.2 | 新增 E3 capacity sweep 为核心主结果；同时报告 H1、H2 和 H4 |
| Results §7.3 | 删除 NLL/AUC 小节；改为字段暴露更正后的 `k=20` 校准结果：0.00 pp，95% CI `[-8.96,+9.25]` |
| Figure 4 | 用 E3 完整 D/C 曲线和 `D−C` 区间替换“uniform SSN 理论曲线 + pooled 39% 单点” |
| Table 4 | 保留 E1 时标清 single seed；删除 AUC；修正样本单位与 CI 口径 |
| Table 5 | 修正 69 人/138 targets；说明不同 probe 的预算与目标定义并不完全等同 |
| Defenses | 写成 proposed defenses；删除经验有效性暗示 |
| Discussion / Limitations | 加入 email 平衡失败、字段级 D 暴露、攻击 seed≠训练 seed、一个模型、来源资格、非单调首次命中 |
| Conclusion | 只保留证据支持的 forcing-capacity 趋势与控制必要性；不声称通用 `β`、已验证 1% `k*`、经验 `ε` 或无记忆 |
| Supplement | 完整曲线、字段计数、逐靶标热图、H5、seed 描述、平衡表和来源审计 |

## Figure 4 的推荐结构

现有 Figure 4 把 uniform nine-digit SSN 的理论曲线与四模型、SSN+email pooled 的 39% 点放在一起，不能作同一总体的理论/经验比较。推荐替换为：

- 左面板：E3 `EMR(D)` 与 `EMR(C)` 随 `k` 的完整曲线及 95% 区间；
- 右面板：`τ(k)=EMR(D)−EMR(C)` 及 95% 区间；
- 理论 uniform-SSN bound 如需保留，单独做 inset，并明确它不是对 pooled 曲线的拟合。

当前更正版：`artifacts/capacity_axis_20260902/figures/field_exposure_corrected/extraction_rates_by_k_field_exposure_corrected.pdf` 与 `tau_by_k_field_exposure_corrected.pdf`。论文版必须保留“事后字段暴露更正”和“字段数量平衡、非完整配对”的标签。

## E3 仍不能填补的实验缺口

- E2：base-model/control-model sandwich identification；
- E5：训练频率 dose-response；
- E6：更多人物与独立训练 seed；
- E7：真正 compute-matched random search；
- E10：真实语料或 Pile 外部有效性；
- E12：防御评估；
- E13：ACR 对照；
- 多模型的完整 capacity sweep；
- 经验 `ε` 与重新定义后的 TPR@固定 floor；
- email 的有效成员性比较。

## E3 进入定稿前的硬门

1. 字段暴露H3/H5重算已经完成；在稿件中披露其事后、字段数量平衡且非完整配对的地位；
2. 决定如何处理 email 平衡失败：重新匹配/扩样，或将 email D/C 结果明确降为描述性；
3. 补齐 executed checkpoint/full-launch 绑定；
4. 处理 6 个 `dirty=null` manifests；
5. 记录未生成最终日志的数组槽位失败/重试归属；
6. 解决 H2 没有预先定义全局检验的合同缺口，或明确只报告未分辨；
7. 补齐 7 条 Colab 历史开始时间，或声明其来源限制。

在这些门未完成前，H1/H2/H4可以作为明确标注的conditional reanalysis写入工作稿；更正后的H3可作为带区间的未检出结果，H5只进入补充材料，二者都不得包装成确认性成功。

## 编辑与同步方式

已在当前 Overleaf 项目的 **Integrations → Git** 中确认 Git Bridge 可用，官方 clone URL 为 `https://git@git.overleaf.com/694b43bda851d60cc36a1686`。该线上项目现已克隆到独立目录 `/Users/xuqiluo/PycharmProjects/PII_Extraction-overleaf-paper`；`origin` 保持上述无凭据 URL，工作树干净，并跟踪 `origin/master`。克隆所得历史共 31 个提交，其中 13 个提交的作者是 Shuya Feng，因此这是现有 Overleaf 项目的完整 Git 工作副本，不是另建的脱节副本。

Overleaf Git authentication token 已由 macOS `osxkeychain` credential helper 保存，没有写入远端 URL、命令脚本或仓库；用于凭据桥接的本地临时文件已删除。以后可在该独立论文仓中执行 `pull → 编辑/审查 → push`，维护 `usenix_paper_v2.tex` 和新的 `satml2027_paper.tex`，无需继续在网页编辑器中逐段交互。当前远端分支为 `master`；若在本地工作分支审查修改，可用 `git push origin HEAD:master` 同步。当前 PATH 中仍没有 `latexmk`/`pdflatex`/`tectonic`；本地源码编辑不受影响，但完全脱离浏览器的 PDF 编译还需安装并匹配线上 TeX Live/编译器版本。
