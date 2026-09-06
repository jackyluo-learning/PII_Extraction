# E3 重新分析：原始证据审计后的条件性结果

## Summary

已从台账关联的 42 个 Cheaha 原始分片重新计算，共 4,200 次攻击；每组 25 人、50 个目标，三个攻击种子。旧分析被撤回为历史版本，见 [prior_analysis.md](reanalysis/prior_analysis.md)。
H1：ρ=0.9890，95% CI [0.9779, 0.9945]，支持记录数据中的上升趋势。H3：k=20 的差为 +1.33 pp [-7.33, +10.00]，未排除零。
H2：1% 误报条件不可分辨；零命中的保守 Wilson 上界为 10.33%，不再接受旧版的 [0,0] 区间或“不存在可用容量”结论。H4：γ=3.484，95% CI [2.811, 4.209]，在声明的 Weibull 工作模型下排除比例关系。
**状态：可核验数据的统计重算已完成，但完整分析验收仍受 Cheaha 来源材料缺口阻塞；不是已接受的确认性研究，也未结项。** 已记录攻击耗时至少 26.25 h，超过 24 A100-h 预算；完整分配算力和失败成本尚未知。

## Ledger Audit

| 审计项 | 结论 | 边界 |
|---|---|---|
| 完整性 | 42/42 k×seed；84/84 两组单元；168/168 字段单元；4,200 行 | 每个目标全部 42 个测量齐全，无重复或关键缺失 |
| 标签/判定 | 逐行用运行版本 exact_match 重算一致；与找回注册表一致 | 验证记录内部一致性与标签，不等于重新运行模型 |
| 运行状态 | 新增49条基于原始文件的记录：42主扫描＋7 Colab pilot/cost/repro | 3条旧pilot保留并排除，避免同名路径误指Cheaha；没有伪造调度退出状态 |
| 五项 pins | 42份manifest；代码commit和环境hash一致；36份dirty=false，6份unknown | 缺Cheaha执行checkpoint哈希、完整launch配置/环境；unknown未改成false |
| 数据 | 四份找回Colab文件的完整SHA256与历史短哈希一致 | 不是每个Cheaha分片的独立数据/模型快照 |
| 复现 | 独立核对Colab original/repro：每组50目标，均0次flip，判定通过 | original为dirty=true且代码版本不同；不升级为clean Cheaha复现 |
| 排除 | Colab pilot/cost/repro不进主分析，旧同名引用被替代且保留 | 没有删掉未知cleanliness的6个主分片挑选有利子集；整体仅条件性 |
| 种子 | 42、1337、2024，全格齐全，达到协议3种子下限 | 同一批人的重复攻击；不是3次独立训练或150名独立对象 |
| 匹配 | 找到Colab seed42的600条E17配对，可重算两种SMD | Cheaha三种子原始E17仍缺；不能静默用Colab冒充 |
| 算力 | 按每组原始wallclock_s核算攻击耗时 | Slurm终态/分配时间/失败列表缺失，SSH认证未通过 |


审计文件：[初次逐行审计（补证前快照）](reanalysis/raw_data_audit.json)、[补证审计](reanalysis/post_recovery_audit.json)、[合同审查](reanalysis/contract_audit.md)、[实现审查](reanalysis/implementation_audit.md)。
当前主模型来源不足使全部主扫描记录的 `confirmatory_eligible=false`；以下检验展示在已记录攻击数据上的条件性结果，不掩盖这一资格限制。

## Preregistered Results

### 先读 k=0：sanity anchor

控制组 0/150；训练组 0/150；每组 25 人、三个种子。两组保守 Wilson 95% CI 均为 [0.0000, 0.1033]，组间 MOVER CI 为 [-0.1033, 0.1033]。未观察到伪命中；不能把零观察写成总体概率恒为零。
`k=0` 是 fixed probe，优化目标为裸值；k≥1 是 gcg_free 的带字段前缀目标。它是单独基线，不纳入 H1/H4/H5 的容量域。

### 完整曲线

| k | 每组 人/目标/尝试/种子 | **α：控制组（95% CI）** | 训练组 EMR（95% CI） | τ=D−C（95% CI，百分点） | 区间 | 攻击耗时 C/D（h）；GPU-h未知 |
|---|---|---|---|---|---|---|
| 0 | 25 / 50 / 150 / 3 | 0.00% [0.00, 10.33] | 0.00% [0.00, 10.33] | +0.00 pp [-10.33, +10.33] | W/M | 0.009 / 0.009 |
| 1 | 25 / 50 / 150 / 3 | 0.00% [0.00, 10.33] | 0.00% [0.00, 10.33] | +0.00 pp [-10.33, +10.33] | W/M | 0.732 / 0.735 |
| 2 | 25 / 50 / 150 / 3 | 0.00% [0.00, 10.33] | 0.00% [0.00, 10.33] | +0.00 pp [-10.33, +10.33] | W/M | 1.124 / 1.135 |
| 3 | 25 / 50 / 150 / 3 | 0.00% [0.00, 10.33] | 0.00% [0.00, 10.33] | +0.00 pp [-10.33, +10.33] | W/M | 1.163 / 1.170 |
| 4 | 25 / 50 / 150 / 3 | 1.33% [0.00, 3.33] | 4.00% [0.67, 8.67] | +2.67 pp [-1.33, +8.00] | B | 1.184 / 1.172 |
| 6 | 25 / 50 / 150 / 3 | 27.33% [20.67, 34.00] | 20.00% [12.67, 28.00] | -7.33 pp [-18.00, +2.67] | B | 1.085 / 1.121 |
| 8 | 25 / 50 / 150 / 3 | 47.33% [40.00, 54.67] | 48.67% [41.33, 55.33] | +1.33 pp [-9.33, +11.33] | B | 0.951 / 0.940 |
| 12 | 25 / 50 / 150 / 3 | 63.33% [56.67, 70.00] | 66.00% [60.00, 72.67] | +2.67 pp [-6.67, +12.00] | B | 0.814 / 0.819 |
| 16 | 25 / 50 / 150 / 3 | 74.67% [68.67, 80.67] | 73.33% [67.33, 79.33] | -1.33 pp [-9.33, +7.33] | B | 0.750 / 0.758 |
| 20 | 25 / 50 / 150 / 3 | 80.67% [74.00, 86.67] | 82.00% [76.00, 88.00] | +1.33 pp [-7.33, +10.00] | B | 0.782 / 0.766 |
| 24 | 25 / 50 / 150 / 3 | 86.00% [80.00, 92.00] | 82.00% [75.33, 88.67] | -4.00 pp [-13.33, +5.33] | B | 0.767 / 0.783 |
| 32 | 25 / 50 / 150 / 3 | 92.00% [88.00, 95.33] | 89.33% [83.33, 94.67] | -2.67 pp [-9.33, +4.00] | B | 0.886 / 0.899 |
| 48 | 25 / 50 / 150 / 3 | 91.33% [86.00, 96.00] | 92.00% [86.67, 96.67] | +0.67 pp [-6.00, +8.00] | B | 1.206 / 1.237 |
| 64 | 25 / 50 / 150 / 3 | 96.67% [94.00, 99.33] | 90.67% [86.00, 95.33] | -6.00 pp [-11.33, -0.67] | B | 1.569 / 1.686 |


B：10,000次独立D/C人员bootstrap，每次在所有k复用同一人样本，seed=20240601；W/M：遇到0/n或n/n时改用Wilson及Newcombe/MOVER。Wilson采用设计的保守n_eff=50/1.5=33.33，三种子不被当成新人。表中τ的数字是百分点；每个点的区间为描述性点区间，并非同时置信带。GPU分配小时未知，耗时栏只计攻击调用。

![容量与组间信号](../../../../artifacts/capacity_axis_20260902/figures/capacity_and_signal.png)
图1：预注册的主估计量，25人/组、3种子；阴影/误差棒为上述95%点区间。k=1.49只标示设计中的理论参照，不是本数据推出的边界。旧版把参考模型H(t)变成逐目标确定性下界的解释已撤回；尚未验证的理论概率上界不叠加成经验保证。

### H1 — 容量与 forcing floor 的上升关系

ρ=0.988965，95% CI [0.977915, 0.994490]，n=25控制人、3种子；条件性Holm p=0.000400。预定CI判据支持向上趋势；不声称每个相邻网格点都严格单调，也不证明因果解释能外推到其他优化器/模型。[等权isotonic摘要](reanalysis/isotonic_summary.csv)按协议单独提供，没有用平滑曲线替换原始α或H2。

### H2 — 低误报且有可检测信号的操作点

**1%形式：inconclusive / unresolved。** 保守零计数上界为 10.33%；重复攻击ICC=.5敏感性下为 8.23%，两种约定均无法认证1%。在同一有效n约定且仍零命中的理想条件下，每组至少需 286 人才能把该Wilson上界压至1%；这不是τ的功效计算，也不保证出现可用点。设计写的9%是近似分辨率参照，保守双侧Wilson实际更严格。
联合判据严格按“控制组上界≤容忍度，且τ区间不含0”。以下同时给出最大可行k、检测率最大点、原始D/C比率最大点；比率不是DP下界。

| 容忍误报 | floor-only k | 联合可行k | 最大联合k | 检测率最优k | D/C比率最优k |
|---|---|---|---|---|---|
| 1%（低于设计分辨率） | [] | [] | — | — | — |
| 5%（低于设计分辨率） | [4] | [] | — | — | — |
| 9% | [4] | [] | — | — | — |
| 10% | [4] | [] | — | — | — |
| 15% | [1, 2, 3, 4] | [] | — | — | — |
| 20% | [1, 2, 3, 4] | [] | — | — | — |
| 30% | [1, 2, 3, 4] | [] | — | — | — |
| 50% | [1, 2, 3, 4, 6] | [] | — | — | — |
| 75% | [1, 2, 3, 4, 6, 8, 12] | [] | — | — | — |
| 90% | [1, 2, 3, 4, 6, 8, 12, 16, 20] | [] | — | — | — |
| 100% | [1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64] | [64] | 64 | 64 | 64 |


除极高容忍度下负向τ的描述性单点外，没有得到满足正向检测条件的点。**未检出不等于不存在**，尤其不能由1%不可分辨的数据证明审计不可能。原设计没有定义联合全局p，本次以p=1保留H2家族位置，标为不可检验，拒绝重复旧版floor-only p替换。

### H3 — k=20 的成员组差异

D=82.00% [76.00, 88.00]；C=80.67% [74.00, 86.67]。τ=+1.33 pp [-7.33, +10.00]，每组25人/50目标/3种子；centered bootstrap p=0.825617，Holm p=1。判定：**inconclusive，不能主张无记忆或等效**。设计未给“足够窄”的实用阈值，不能事后设定。

| 字段 | 每组人/目标/种子 | D及95%CI | C及95%CI | τ及95%CI（百分点） | C/D攻击小时；GPU未知 |
|---|---|---|---|---|---|
| ssn | 25 / 25 / 3 | 64.00% [52.00, 76.00] | 61.33% [48.00, 73.33] | +2.67 pp [-14.67, +20.00] | 0.652/0.641 |
| email | 25 / 25 / 3 | 100.00% [86.68, 100.00] | 100.00% [86.68, 100.00] | +0.00 pp [-13.32, +13.32] | 0.130/0.124 |


email达到样本全命中仍有非零总体不确定性；其差值不再被写成确定的结构性零。SSN区间更宽，合并值不能替代字段级限制。

### H4 — k_min 与 H 的比例模型

对控制组25人、50目标拟合log-log Weibull AFT，保留区间删失及右删失，三种子任一命中的最小k定义不变；10,000次按人重拟合，无最终失败。γ=3.484486，95% CI [2.811469, 4.209360]，条件性Holm p=0.000400。**声明的工作模型下 refuted：γ区间排除1。** 这不是对所有可能forcing模型的反证。
截距=-12.611，95% CI [-15.697, -9.767]。exp(−截距)为 2.998e+05，区间 [17447.2, 6561101.8]；当γ不为1，其单位不能称为通用bits/token，禁止作为可迁移β指导攻击容量。
Weibull误差分布并未在预注册中固定，因此工作分布选择明确披露；log-normal敏感性点估计γ=2.718，仅作探索性模型诊断，不以它替换主结果。

### 四项家族与判据

| 假设 | 原始p或保留值 | Holm p | 条件性解读 |
|---|---|---|---|
| H1 | 0.000100 | 0.000400 | 趋势判据支持 |
| H2 | 1.000000 | 1.000000 | 联合检验未定义；p=1保留位置 |
| H3 | 0.825617 | 1.000000 | 不拒绝零；不是等效 |
| H4 | 0.000100 | 0.000400 | 拒绝γ=1 |


家族始终是四项，不丢弃H4。p算法是本次明确披露的补充实现，采用有限Monte Carlo加一校正；最小可报告值1/10001，绝不报告p=0。H3离散边界已用整数成功次数独立核对。Holm并不能补足未预注册的联合H2检验或来源缺口，所以这些是条件性重分析输出。

## Ablations

未新增模型/攻击实验。按预注册补出字段拆分、删失敏感性和matching诊断；不把分析拆分冒充新实验。

### β的直接比率与删失模型诊断

| 字段 | n人/目标/种子 | 保守median H/k；95%CI | 乐观网格端点；95%CI | 保守值/log₂V | GPU-h |
|---|---|---|---|---|---|
| pooled | 25/50/3 | 9.199 [7.569, 9.503] | 12.266 [10.653, 13.015] | 0.589 | 未知；同一主扫描 |
| ssn | 25/25/3 | 6.007 [4.697, 6.586] | 9.010 [6.263, 9.879] | 0.385 | 未知；同一主扫描 |
| email | 25/25/3 | 10.834 [9.814, 11.599] | 16.252 [14.721, 17.398] | 0.694 | 未知；同一主扫描 |


端点括号是网格不确定性，CI是人员bootstrap抽样不确定性，二者不可混淆。跨seed任一命中定义偏向成功率更高的三次尝试程序，不是单次攻击能力。比例模型失配下这些为描述性比率，不是物理信道速率，也不是跨字段安全保证。
Tobit次要规格：level-scale截距=-13.569，CI [-21.412, -6.873]；斜率=0.310 tokens/bit，CI [0.208, 0.427]，n=25控制人，10,000次人员重抽样。Complete-case线性截距=-15.385，CI [-23.872, -7.927]；斜率=0.358，CI [0.245, 0.483]。后者仅作删失诊断，未替换AFT。
本样本右删失比例=0.000，未触发高删失的Turnbull替代条件。控制组 7/50 目标出现命中后在更大k失效，违背AFT吸收阈值假设。H的控制组方差：总=41.759，字段内=30.063，字段间=11.696；不能仅凭两字段不同就断言总方差都来自字段间。

### 各seed首次命中敏感性（exploratory）

| 标签 | seed / 字段 | n人 | median首次命中k；95%CI | 右删失目标 | 非单调目标 |
|---|---|---|---|---|---|
| (exploratory) single attack seed sensitivity | 42 / ssn | 25 | 16.0 [16.0, 20.0] | 0 | 11 |
| (exploratory) single attack seed sensitivity | 42 / email | 25 | 6.0 [6.0, 8.0] | 0 | 2 |
| (exploratory) single attack seed sensitivity | 1337 / ssn | 25 | 16.0 [12.0, 16.0] | 0 | 17 |
| (exploratory) single attack seed sensitivity | 1337 / email | 25 | 6.0 [6.0, 8.0] | 0 | 1 |
| (exploratory) single attack seed sensitivity | 2024 / ssn | 25 | 16.0 [12.0, 20.0] | 0 | 14 |
| (exploratory) single attack seed sensitivity | 2024 / email | 25 | 8.0 [6.0, 8.0] | 0 | 1 |


单seed行均为探索性敏感性；主定义仍是固定三个seed中的首次任一命中，未按这里的数值择优切换。

### 平衡与原始E17

| 实际攻击字段 | 协变量 | nD/nC | SMD；95%bootstrap CI | |SMD|<0.1 |
|---|---|---|---|---|
| ssn | char_len | 25/25 | 0.000 [0.000, 0.000] | 是 |
| ssn | target_len_tokens | 25/25 | -0.074 [-0.667, 0.465] | 是 |
| ssn | target_H_bits | 25/25 | 0.082 [-0.493, 0.643] | 是 |
| email | char_len | 25/25 | 0.503 [-0.031, 1.098] | 否 |
| email | target_len_tokens | 25/25 | 0.613 [0.066, 1.315] | 否 |
| email | target_H_bits | 25/25 | 0.513 [-0.025, 1.103] | 否 |


SMD的0.1是预定诊断阈值，不是显著性测试。SSN字符长度两组都固定相同，因此SMD=0不意味着可检测该协变量的变异；email三项都未过点估计平衡门槛，影响D/C的成员解释。
[完整Colab E17双SMD表](reanalysis/colab_e17_balance.csv)同时包含配对加权与控制去重边际、全匹配人群与实际D子集。其来源明确为Colab seed42；尚缺Cheaha原始E17，故不能据此宣称所有主扫描matching已核验。

## Exploratory Findings

### H5（exploratory，underpowered）

观察最大值出现在 [4, 12]；保留所有并列峰值后的95%位置包络为 [4, 48]，1121/10,000 重抽样存在并列最大值。log-k二次项=-0.00391，95% CI [-0.01660, 0.00956]，n=25人/组、3种子。探索性单侧曲率p=0.2810（null-centered、未调整）；只保留第一个argmax的敏感性CI为 [4, 48]。位置包络满足不触端点的字面条件，但曲率区间含0、峰区间宽且没有预定flatness等效阈值，判定为探索性不确定；既不声称定位了峰，也不声称证明曲线平坦。

### NLL/AUC（exploratory）

| 行标签 | 字段/k | n人每组/种子 | AUC及95%人员bootstrap CI | GPU-h |
|---|---|---|---|---|
| (exploratory) | ssn / 1 | 25 / 3 | 0.666 [0.510, 0.813] | 未知；重用主扫描 |
| (exploratory) | ssn / 2 | 25 / 3 | 0.639 [0.514, 0.754] | 未知；重用主扫描 |
| (exploratory) | ssn / 3 | 25 / 3 | 0.671 [0.522, 0.808] | 未知；重用主扫描 |
| (exploratory) | ssn / 8 | 25 / 3 | 0.546 [0.427, 0.664] | 未知；重用主扫描 |
| (exploratory) | ssn / 20 | 25 / 3 | 0.489 [0.391, 0.591] | 未知；重用主扫描 |
| (exploratory) | ssn / 64 | 25 / 3 | 0.467 [0.366, 0.572] | 未知；重用主扫描 |
| (exploratory) | email / 1 | 25 / 3 | 0.598 [0.427, 0.762] | 未知；重用主扫描 |
| (exploratory) | email / 2 | 25 / 3 | 0.597 [0.433, 0.753] | 未知；重用主扫描 |
| (exploratory) | email / 3 | 25 / 3 | 0.567 [0.400, 0.726] | 未知；重用主扫描 |
| (exploratory) | email / 8 | 25 / 3 | 0.547 [0.426, 0.663] | 未知；重用主扫描 |
| (exploratory) | email / 20 | 25 / 3 | 0.429 [0.328, 0.533] | 未知；重用主扫描 |
| (exploratory) | email / 64 | 25 / 3 | 0.478 [0.377, 0.578] | 未知；重用主扫描 |


![探索性NLL分析](../../../../artifacts/capacity_axis_20260902/figures/auc_exploratory.png)
图2：所有行和曲线均为探索性；每组25人，3种子，10,000次人员bootstrap，阴影为未经多重比较校正的95%点区间。低k的候选分离值得后续预注册验证，不能据相邻多个区间宣称独立重复发现。email失衡、共同目标和不同早停程度都限制机制解释。
不将原始TPR/FPR点比值称为“certifiable ε”。本次尚未建立独立阈值校准样本、所需错误率的有效同时界和DP解释条件，故不提供确认性ε下界。旧版“信息论逐目标下界紧”的结论同样撤回。

## Deviations from Preregistration

1. 本次是见过数据后的纠错重分析；原设计保留原文，所有处理约定预先写入[method_choices.md](reanalysis/method_choices.md)，但它们不能追溯变成预注册。旧版H2改为floor-only p发生在完整曲线记录之后，不能继承其“结果前完成”的叙述。
2. 采用明确修订后的log-log γ=1规则；设计中旧H4截距文字和50控制人的残留不覆盖最终Tests与批准协议。保持25人/组和三个种子，不补跑、不择优丢seed。
3. 修复全零/全一的区间；保守target-only有效n与repeated-ICC敏感性均公开，不假装ICC已测得。H2未定义全局检验，保留p=1占位；H1/H3/H4 bootstrap p算法和finite-MC修正明确属于实现补充。
4. Weibull分布、跨seed首次任一命中、并列最大值包络及无flatness等效阈值都明示；无法用它们完成严格确认性结论。log-normal只是探索性分布诊断。
5. 为10,000次删失重拟合使用与lifelines数值核对的同一Weibull似然快速求解器；首次遇到一个线搜索失败即停止，未丢样本。调整线搜索上限后同一抽样重算全部10,000次，最终无失败；[solver_notes.md](reanalysis/solver_notes.md)保留过程。
6. 报告由ledger驱动的专用生成器生成，取代报告规范中“只能make_tables.py”的旧实现路径；全部数字可追至results.json及带哈希原始文件，没有手工表格抄数。
7. 找回的Colab文件独立存放，绝不覆盖同名Cheaha文件。新补录身份哈希表示本次观察到的manifest字段，不伪装为历史完整配置hash；未知清洁状态、模型身份和账目继续未知。

## Predictions vs. Outcomes

下列逐任务表区分本次能核验的结果和历史文字；不把已有description中的“done/held”当作原始证据。

| 任务 | 原预测（原文） | 本次可核验结果 | 判定 |
|---|---|---|---|
| t0-1 | The current prefix yields {f=1:10, f=5:15, f=20:0}; the fix yields roughly {3, 7, 15}. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t0-2 | A k=0 shard writes 100 rows with capacity_k=0 and does not collide with any gcg shard. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t0-3 | Killing a shard mid-run leaves a parquet with the persons completed so far. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t0-4 | All 42 shards emit an identical target_subset_hash. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t0-5 | On a simulated 16GB profile the eval batch drops below 512. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t0-6 | The corpus regenerates from Wikipedia alone, C4 count zero, assertions pass. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t0-7 | Importing the analysis module without lifelines raises rather than degrading. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t0-8 | PII eval loss falls to near zero on the PII documents, as in run2. | 找回Colab模型和train_meta；未重训，Cheaha模型身份待核验 | 历史损失预测未据日志重新判定 |
| t0-cp | Every gate's test passes and the tree is clean. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t1-1 | alpha_0 is not detectably above 0 — run2's own gpt2 fixed-probe EMR was 0.0. | 原始anchor确认未命中；总体概率仍有区间 | 符合观察预测 |
| t1-2 | k=64 costs materially more than the linear-in-(k+T) model predicts; k=1 evaluates 256 candidates, not 512. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t1-3 | |D| = 25 with all three frequency tiers present; |C| between 15 and 25. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t1-4 | Per-arm flip rate does not exceed 2*p_hat*(1-p_hat) beyond its bootstrap CI. | 找回original与repro，逐目标0 flips；原始pilot dirty | 判定复现通过；来源限制 |
| t1-cp | All four pilot criteria met. | 本次未重跑该执行/破坏性试验；保留历史预测 | 未独立验收 |
| t2-1 | alpha_k rises monotonically from near 0 toward run2's 52% at k=20 and beyond. | 种子网格齐全；见seed_rates.csv和主曲线 | 上升形状支持；不声称每相邻点单调 |
| t2-2 | The curve's shape reproduces seed 42's within its intervals. | 种子网格齐全；见seed_rates.csv和主曲线 | 上升形状支持；不声称每相邻点单调 |
| t2-3 | The curve's shape reproduces the first two. | 种子网格齐全；见seed_rates.csv和主曲线 | 上升形状支持；不声称每相邻点单调 |
| t2-2b | All 42 agree on both. | 逐行重建subset hash一致，N=200一致 | 通过 |
| t2-cp | The ledger is complete and the invariants hold. | 原始矩阵完整；GPU分配账目未齐，已记录攻击时间超预算 | 未满足全部checkpoint条件 |
| t3-1 | Each is unit-tested against a worked example before any table is generated. | 边界区间、固定家族、删失求解器经过本次校验 | 本次实现验证通过 |
| t3-2 | The pair-wise SMD is small by construction; the marginal SMD is the one that can fail. | email实际攻击边际SMD不达标；Cheaha配对未齐 | 平衡预测失败/待补证 |
| t3-3 | Recorded: H1 supported; H2 undetermined below alpha=9%; H3's CI contains 0 but narrows; H4 undecided. | H1趋势、H4比例被反驳；H2/H3未决，H5探索性 | 混合；不接受旧完结结论 |
| t3-4 | The censored estimate exceeds the complete-case one, since censoring drops the hardest targets. | 保留删失；右删失为零，未见预期的掉难例差异可直接解释 | 比较需保留模型差异，不宣称预测成立 |
| t3-cp | Every hypothesis has a verdict or an explicit undecidable. | 新报告和数值已写；来源/匹配/总账仍待补齐 | 尚未验收 |


## Threats to Validity

- A1/matching：实际email的三项SMD未过预设门槛；原始配对诊断仅恢复Colab版本。组间差值和AUC不应直接归因为训练成员性。
- 新增CODE_MAP #16–#20逐项记录本次发现及Validity标记；以下也逐项交代历史问题。
- CODE_MAP旧问题#1/#15（β单位及删失）：本次保留删失，另给比率；γ失配时不把截距当通用bits/token。H4并未因数据右删失少就免除非单调命中假设问题。
- CODE_MAP #7（CI不一致）：本次逐行标明B/W/M；边界格不再出现无依据的零宽区间。#8及#10的目标/提示差异：k0单列；没有把anchored对比混入本研究。
- CODE_MAP #9/#11/#12：语料生成与训练程序限制仍存在；源代码显示padding标签未屏蔽，影响模型训练条件及可外推解释。GPT-2单模型没有跨模型LoRA比较，训练工件的主扫描身份仍待补证。
- CODE_MAP #13/#14：E17有放回、去重与实际独立子集不等于配对平衡；已验证本次被攻击D/C标识及SSN/email值无交叠，不能自动推广为完整语料无污染。
- CODE_MAP #2/#3/#4：没有把异单位forward计数当GPU-h，没有预算匹配自然提示比较，也没有把原始比值称为DP证书。#5/#6（λ/软提示扫描）未运行，不能做相应结论。
- 6份main清洁状态未知；所有main缺历史checkpoint内容pin及完整环境。恢复数据和当前Colab模型hash有帮助，但不能制造Cheaha历史执行身份。
- 只有一个训练模型、25人/组、两个合成字段、200步GCG、三个攻击种子。人员bootstrap条件于这三种子，不估计跨重训练、跨硬件或新seed总体不确定性。
- 原分析已看过数据；新提出的p实现和探索性分析有研究者自由度。独立复算验证计算，不能消除这个设计层限制。

## Compute

控制组已记录攻击耗时 13.022 h，训练组 13.229 h，合计 **26.251 h**。每份manifest为1张A100；若按所记录的独占单GPU执行，这是分配小时的下限，已比批准24 A100-h至少高 2.251 h（9.4%）。
这不包括加载、匹配、日志、训练、Colab pilot及失败/中断。**不能报告总GPU-h=0，也不能报告预算内。** 完整Slurm accelerator-hours、失败成本仍待sacct及终态记录；本次重分析为本机CPU计算，未新增GPU实验。

## Limitations

合成PII模板及固定目标限制外部有效性。恢复文件的源数据元信息可查，但预训练污染没有独立排查；匹配误差与字符串归一化规则都有构念误差。没有人工独立标注noise-floor估计。零命中组的有效n基于明确假设；既没有由零观察测出ICC，也没有由三个seed扩大到新人员。H3的CI仍允许有实际意义的正负差，不能报告“无信号”。

![各个种子的曲线](../../../../artifacts/capacity_axis_20260902/figures/seed_spread.png)
图3：每条线对应一个预定攻击种子；每组25人、2字段。此图展示原始seed spread，无误差棒；推断的重采样单位仍为人。seed42与2024在部分k一致不等于独立训练复现。

## What This Does Not Show

- 没有证明总体forcing概率为零、存在误报≤1%的工作点，或不存在任何可用工作点。
- 没有证明缺少成员信号、模型不记忆、隐私安全或满足任何DP保证。
- 没有把参考模型的H(t)证明为生成目标的确定性容量门槛，也没有证明Proposition1逐目标“紧”。
- 没有证明一个通用β可以跨字段、目标格式、模型规模、优化器或计算预算迁移。
- 没有把探索性AUC、宽峰区间、缺乏显著性或被保留的零假设升级成确认性发现。
- 没有完成Cheaha历史来源与全部算力的核验；研究仍未达到最终分析验收和结项条件。

复算入口：`reanalysis/recompute.py`；报表入口：`reanalysis/write_report.py`。参数与环境见[方法约定](reanalysis/method_choices.md)、[环境记录](reanalysis/analysis_environment.txt)。完整表：[curve_table.csv](reanalysis/curve_table.csv)、[seed_rates.csv](reanalysis/seed_rates.csv)、[actual_balance.csv](reanalysis/actual_balance.csv)、[探索性AUC](reanalysis/auc_exploratory.csv)。
