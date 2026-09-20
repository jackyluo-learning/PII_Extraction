# 当前论文逐节研读、中文释义与 E3 改写方案

日期：2026-09-19
研读对象：Overleaf 线上主稿 `usenix_paper_v2.tex` 及其 17 页编译 PDF
目标投稿：IEEE Conference on Secure and Trustworthy Machine Learning（SaTML）2027 Research Paper
配套材料：[`paper_integration_audit.md`](paper_integration_audit.md)、[`satml2027_submission_requirements.md`](satml2027_submission_requirements.md)

## 先读这一页：当前论文到底在说什么

当前稿件的核心论点是：当审计者已经知道一个目标字符串，并用 GCG 等优化器搜索能够让模型输出该字符串的 prompt 时，“成功输出”同时混合了两种机制：模型因为微调见过该记录而发生的 **recall**，以及优化器即使面对未加入微调语料的目标也能把模型推向该输出的 **forcing**。因此，单独报告训练目标组 D 的抽取率，不能说明其中多少来自训练记忆。论文建议对匹配的控制目标组 C 运行完全相同的攻击，以 `EMR(C)` 测量 forcing floor，并用 `EMR(D)-EMR(C)` 表示与微调成员身份相关的差异。

E3 使这条主线更强，同时推翻了现稿中的一部分扩展叙述：

1. E3 在同一 GPT-2 124M checkpoint、同一批目标和三个攻击 seed 上扫描 `k=0,1,2,3,4,6,8,12,16,20,24,32,48,64`，直接显示控制组命中率随自由 token 数 `k` 强烈上升。H1 的 Spearman `ρ=0.988965`，人员聚类 bootstrap 95% CI `[0.977915, 0.994490]`。
2. `k=1,2,3` 虽然观察到零次控制命中，但保守 95% 上界仍是 10.33%。因此，E3 没有验证任何 `k≥1` 能把 forcing floor 控制在 1% 以下。
3. 字段暴露更正后，`k=20` 的D与C都为81.94%，差值`0.00`个百分点，95% CI `[-8.96,+9.25]`。它表示“当前样本没有分辨出D/C差异”，不表示两组等效、模型没有记忆或模型具有隐私保证。更正排除了两个未进入训练文本的D-SSN和两个C-SSN；由于执行路径丢失逐目标E17配对，第二个C只能事后按相同协变量从实际攻击目标中选最近者，因此结果是字段数量平衡的事后敏感性分析。
4. 现稿提出 `k_min≈H/β` 并把 `β` 解释为可迁移的模型常数。E3 的删失 Weibull 工作模型得到 `γ=3.484486`，95% CI `[2.811469,4.209360]`；简单比例模型要求 `γ=1`，因此该模型被当前数据否定。`H/k_min` 只能作为本批数据的描述性比率。
5. 字段暴露更正后，H5 的观测最大点为`k=4`，bootstrap包络为`[4,48]`，曲率区间包含0。argmax规则提示内部最大值，却没有定位稳定最优点；它适合补充材料，不适合摘要或主结论。

推荐把整篇论文的中心命题改写为：

> 优化式确认审计把微调相关 recall 与目标 forcing 混在同一个成功率里。分布匹配的未微调控制目标是解释该成功率所必需的。E3 表明 forcing 随 prompt 容量急剧上升，但当前数据既没有确认 1% forcing-floor 操作点，也不支持用一个通用的熵—容量比例常数选择该操作点。

这里的“中文翻译”采用忠实释义：保留每节的论证结构和关键数学含义，但不逐句复制英文。

---

## Abstract（摘要）

### 当前内容的中文释义

微调语言模型会记住个人信息，GCG 等基于梯度的 prompt 优化已被用于审计这种泄漏。现有审计通常把“优化器成功让模型输出已知记录”直接记为可抽取，但这一成功本身不能证明模型记住了该记录，因为足够强的优化器也可能迫使模型输出没有进入微调数据的任意目标。

稿件随后用一个容量论证解释风险：长度为 `k` 的离散 prompt 最多索引 `|V|^k` 个输入，因此名义容量为 `k log2|V|` bits。默认的 `k=20` 对 GPT-2 约为 312 bits，而九位 SSN 约为 30 bits；在这种区域，理论上界已经失去约束力。稿件定义控制组命中率为 forcing floor，并主张只看训练目标无法区分 recall 与 forcing。

摘要再给出旧 E1 结果：固定 prompt 与所谓 compute-matched random search 为 0%，梯度攻击在控制组达到 39%–62%，soft prompt 达到 100%；GPT-2 的 D/C 都是 52%，并声称 ROC 接近随机。最后把 D/C 差值解释为 membership distinguisher advantage 和经验 `ε` 下界，并提出将未使用的控制目标作为 honeytoken。

### 中心思想

摘要想让读者接受一个判断：**优化成功不是训练记忆的充分证据，必须用未进入微调语料的匹配控制目标测量攻击本身的 forcing 能力。**

### E3 后应如何修改

- 保留问题、负控制和容量扫描这三件事，把 E3 的完整 `k` 曲线作为摘要的主要实证证据。
- 把“information-theoretic floor”改成更精确的说法。现有命题给出 `α_k` 的上界；上界在大 `k` 时变得 vacuous，说明理论不再提供安全保证，却不能单独证明 forcing 必然大于零。E3 才提供正 forcing floor 的经验事实。
- 删除 NLL/AUC/ROC、chance-level ROC、经验 `ε` 已经测得的叙述。它们已经从权威 E3 分析中撤回。
- 删除 “compute-matched random search”。旧 random restart 只有 512 个候选，而典型 GCG 约评估 61,440 个候选，并未匹配计算量。
- 把 “never saw” 改成 “not included in the fine-tuning corpus”。实验不能证明基础模型预训练阶段从未接触同一字符串。
- 不在摘要中声称 `β`、`k*` 或防御已经验证。E3 反驳简单 `β` 模型，H2 也没有确认 1% 操作点。
- 摘要可报告 H1 的趋势和 H2 的限制；H3若出现，必须使用字段暴露更正后的`0.00 pp [-8.96,+9.25]`并明确其事后、非完整配对地位。

### 推荐的新摘要信息顺序

1. 问题：优化式 confirmation audit 混合 recall 与 forcing。
2. 方法：对 D/C 执行完全相同的攻击，并扫描自由 prompt 长度。
3. E1：forcing 在多个模型/探针上存在，作为现象展示。
4. E3：在 GPT-2 124M 上，控制命中率随 `k` 强烈上升；低 `k` 的样本不足以确认 1% floor。
5. 反例：简单 `k_min≈H/β` 校准模型不符合数据。
6. 含义：审计必须报告控制 floor 及不确定性，且安全操作点需要在具体模型和目标分布上实测。

---

## 1. Introduction（引言）

### 当前内容的中文释义

引言先说明使用场景：机构会在客户记录、客服文本和内部文档上微调模型，数据是否留在权重中会影响合规和部署。审计给出的数字会触发补救或放行，因此数字必须真的测量模型记忆。

接着指出目标审计的逻辑漏洞。手写 prompt 失败不能证明没有记忆，所以近期工作改用优化搜索；审计者已经持有目标记录，优化 prompt 以最大化逐字输出目标的概率。但优化器本身获得了很大的搜索容量，成功可能来自 forcing。

“Forcing has an information-theoretic floor” 段用 `k log2|V|` 与目标熵比较，说明 `k=20` 已远超 SSN 的名义信息量。稿件由此主张大容量区间无法从训练组成功率中识别记忆，并用旧 E1 的 39% 控制命中和 soft prompt 100% 作为证据。

“A distinguisher advantage and a privacy bound” 段把 D 视为 member、C 视为 non-member，于是 `EMR(D)-EMR(C)` 等于某个二元成功规则的 `TPR-FPR`。在满足因果识别假设时，这也可解释为微调语料包含该记录对可诱导性的平均影响。稿件进一步把这对率放入 DP hypothesis-testing region。

后面三段分别把本工作连接到 canary/DP auditing、ACR 和论文贡献。稿件称负控制恢复了 prompt-based extraction 中丢失的校准；提出控制模型构成 2×2 设计；提出 `β`、`k*`、`Mem(t)`；最后把 honeytoken 作为防御。

### 中心思想

引言建立的是一条因果链：优化器有容量 → 它可以制造输出 → raw extraction rate 混合两个机制 → 未训练控制组是识别记忆归因所必需的。

### E3 后应如何修改

- Figure 1 仍可作为全篇概览，但图中“yields an empirical ε lower bound”应改成理论联系；当前实验没有完成可作为主结果的经验 `ε` 分析。
- 把理论和经验的角色分开：理论说明何时 **没有先验保证**，E3 说明实际 forcing floor 如何随 `k` 变化。
- 用 E3 的 14 点容量曲线替换 `k=20, 39%` 单点作为引言的核心实证预告。
- 删除“greater probe expressivity yields a higher floor”由 soft prompt 单点“验证”的表述；E3 的 H1 才是同一模型、同一目标、同一优化器内的直接趋势证据。
- `β`、`k*` 和 `Mem(t)` 不再作为已经建立的贡献。可以保留“我们检验了通用容量校准是否成立，并发现简单比例模型失败”这一负结果。
- `k*_thy=1` 只表示由最坏情况上界得到的充分安全条件，不能表述为经验上可用的审计点。E3 对 1% floor 未分辨。
- “39% of records the model provably never saw” 改为“39% of controls absent from the fine-tuning corpus”。
- 贡献列表建议收缩为三项：理论上的非识别条件与先验上界；D/C 相同攻击协议；E1+E3 对 forcing 存在和容量响应的实证，以及通用比例校准失败的负结果。
- Scope 中明确：当前外推范围主要是受控合成语料、GPT-2 124M 完整容量扫描；多模型 E1 只是初步复现，不支持规模规律。

---

## 2. What Does an Extraction Attack Measure?（抽取攻击究竟测量什么）

### 2.1 Setting and Notation（设定与符号）

#### 当前内容的中文释义

本节把攻击类 `A_k` 定义为拥有 `k` 个自由 token 位置的 prompt 集合。`S` 表示攻击类中是否存在一个 prompt 能让模型的 greedy decoding 包含目标，`Ŝ` 表示实际优化器找到的 prompt 是否成功。因为优化器可能找不到所有可达输出，所以 `Ŝ≤S`。EMR 是以“人物×字段”为单位的 exact-match 平均成功率，D 和 C 使用完全相同的判定规则。

#### 中心思想

区分“理论可达”与“优化器实际找到”，并固定全文的观测单位和成功规则。

#### E3 修改

- 保留这一节，但增加 E3 的统计单位：25 人×2 字段×2 组×3 攻击 seed×14 个 `k`，共 4,200 次攻击。
- 明确三个攻击 seed 是对同一 fine-tuned checkpoint 的优化重启，不是三个独立训练模型。
- 说明跨 seed 的聚合规则；当前“任一 seed 命中”会测量三次尝试程序，而非单次攻击能力。
- 将 substring normalization、decode length 和带不带字段标签的目标形式写成可复现规则，避免不同探针实际目标不一致。

### 2.2 Audit Setting and Auditor Knowledge（审计场景与审计者知识）

#### 当前内容的中文释义

论文研究的是 confirmation audit：机构持有微调语料和模型，也知道要检查的目标记录，并拥有 white-box 权限。它不同于不知道目标的 discovery attack，也不同于直接判断成员身份的 membership inference。已知目标使逐记录可诱导性可以被完整评估，但并不自动把成功变成记忆证据。

#### 中心思想

限定 threat model，避免把“验证一个已知目标能否被诱导”误写成“从模型中发现未知 PII”。

#### E3 修改

- 保留三种 setting 的区分。
- 收紧“confirmation upper-bounds adaptive adversary”一类表述；知道完整目标并直接优化 NLL 是很强的审计者，和只知道姓名、字段格式或前缀的真实攻击者不等价。
- 在 SaTML 版本中把这种强审计者解释为安全测试的 worst-case instrument，而不是实际攻击成功率估计。

### 2.3 A Worked Example, and Its Twin（示例及其控制孪生）

#### 当前内容的中文释义

稿件用 John Smith 的 `SSN: 123-45-6789` 举例。审计者知道目标，用 GCG 最小化目标 token 序列的负对数似然并搜索随机后缀；如果生成中逐字出现目标，就记为成功。然后对来自同一生成器、未加入微调语料的 Jane Doe 运行完全相同的程序。如果 Jane 的目标也能被输出，John 的成功不能单独证明微调记忆。

#### 中心思想

用一对直观案例解释 D/C 的唯一差别应当是是否进入微调语料。

#### E3 修改

- 保留，这是全文最容易理解的解释。
- 把“never added to the corpus”统一为“absent from the fine-tuning corpus”。
- 增加一个实际 E3 prompt/目标示例，并分别展示 D 和 C 的完整输入、优化后 suffix、decode 和 exact-match 判定；这能回应读者对“如何诱导模型”的疑问。
- 强调 C 不是把 D 的同一值再次标成控制。若目标字符串完全相同，模型无法同时“见过”和“没见过”它；C 应是不同人物的不同值，但在字段类型、长度等影响 forcibility 的变量上与 D 可比。

### 2.4 Prompt Capacity Bounds the Forcing Floor（prompt 容量与 forcing floor 的边界）

#### 当前内容的中文释义

本节定义模型在攻击类下能达到的输出集合 `R_k(M)`，以及从控制目标分布抽样时目标落入该集合的概率 `α_k`。由于长度为 `k` 的离散 prompt 最多有 `|V|^k` 个，greedy decoding 又把每个 prompt 映射到一个输出，所以可达输出最多 `|V|^k` 个。若控制分布的 min-entropy 是 `H∞`，则 `α_k≤2^(k log2|V|-H∞)`。由此可以反解一个保证 floor 不超过容忍值的充分条件 `k*_thy`。

随后稿件把查询预算、prompt 长度和 fluency constraint 都换算成可达集合大小，主张它们可以统一到 bits 容量轴。

#### 中心思想

给出一个模型无关的最坏情况上界，并说明 prompt 搜索空间相对目标分布太大时，理论不再提供低误报保证。

#### E3 修改

- 数学命题可以保留，但术语必须纠正：它是 forcing rate 的 **upper bound**，不是 forcing 必然为正的 lower bound。可以继续把观测的 C 成功率叫 forcing floor，因为它是 raw rate 中不可归因于微调成员身份的基线，但不能说命题本身“证明了一个正的 floor”。
- 当指数上界超过 1 时，正确含义是 bound 变成 vacuous，而不是理论预测 `α_k` 会很高。
- `k*_thy` 是充分条件；E3 显示经验 `k*` 在 1% 阈值下仍不可分辨。两者必须分开。
- “field-type gradient”目前由上界启发，但上界不能预测实际排序。E3 中 email/SSN 的 `H`、tokenization 和匹配质量也不同，应写成待检验机制。
- query-budget 与 prompt-capacity 的“同一货币”依赖可达集合的粗略计数，适合作为理论视角，不宜写成已经实证校准的精确兑换率。
- E3 的 H4 应在本节末明确：名义容量上界有效，不代表实际优化器以恒定 `β` 实现这份容量。

### 2.5 Necessity of the Control（为什么控制组不可少）

#### 当前内容的中文释义

本节指出容量上界不能告诉我们具体模型的可达集合有多大，因此仅从训练目标上的成功无法拆分“由训练造成的可达性”和“与训练无关的可达性”。要识别微调归因，要么事先严格限制可达集合，要么用 non-member 控制目标实测后一项。

#### 中心思想

把“应当加控制组”提升为识别问题：没有控制，raw rate 缺少反事实基线。

#### E3 修改

- 保留为主要理论贡献。
- 避免把 `H∞≤k log2|V|` 写成现实模型一定能覆盖整个 D；证明陈述的是存在性/非识别，不是实际 GPT-2 行为。
- 用 E3 的同一模型容量曲线作为实际例证：`k` 增加时 C 大幅上升，说明 nuisance component 不能当成固定常数。

---

## 3. Calibrated Extraction Auditing（校准后的抽取审计）

### 3.1 The Estimand（真正想估计的量）

#### 当前内容的中文释义

对目标 `t`，`Y_t(1)` 表示模型在包含它的语料上训练后攻击是否成功，`Y_t(0)` 表示在其他条件相同、只排除该目标时攻击是否成功。二者平均差 `τ` 是“把该记录加入微调语料对可诱导性的平均影响”。逐目标重训太贵，因此稿件用 D 的成功率减去匹配 C 的成功率近似这个反事实差。

#### 中心思想

论文测量的不是“模型能不能输出字符串”，而是“微调中包含该字符串让输出概率增加了多少”。

#### E3 修改

- 定义保留，但必须把 `EMR(D)-EMR(C)` 称为 estimator，而非在没有条件时直接等于因果效应。
- E17 显示 email 的字符长度、token 长度、`H(t)` 的 SMD 约为 0.503、0.613、0.513，超过预定 0.1 阈值。email 的 D/C 差异目前只能描述，不能作因果解释。
- SSN 匹配通过，可作为更可信的字段层分析；最终主结果最好报告 pooled 与字段分层，并解释 pooled 受 email imbalance 影响。
- 先按字段实际微调暴露把 D 重标；E3 现有 50 个 D 目标中 2 个 SSN 没有进入训练文本。

### 3.2 The Same Number Is a Distinguisher's Advantage（同一差值也是区分器优势）

#### 当前内容的中文释义

若规则是“攻击成功就猜目标属于微调数据”，则 D 成功率是 TPR，C 成功率是 FPR，二者之差就是这个特定二元判定规则的 advantage。若训练机制满足 `(ε,δ)`-DP，任何区分器的 TPR/FPR 必须落在 DP 允许区域内，因此这对率理论上可给出 `ε` 的经验下界。

#### 中心思想

给 D/C 差值一个安全学解释：它不仅是两组均值之差，也是一个 membership test 的区分能力。

#### E3 修改

- 保留恒等式 `TPR-FPR`，但明确它对应 exact-match 这一项预先固定的二元规则。
- 因果解释还需要 exchangeability/no-interference 等假设，密码学恒等式本身不需要；两者不能无条件写成同一结论。
- `ε` 关系保留为理论 corollary。当前模型不是 DP 训练，样本也不足以提供有意义的经验 privacy certificate，不应在摘要和结果中称已经获得实证 `ε`。
- 删除依赖 NLL 阈值扫描的最大化 `ε` 结果；若未来恢复，应独立预注册 score、threshold selection 和置信区间。

### 3.3 Identification and the 2×2 Design（识别假设与 2×2 设计）

#### 当前内容的中文释义

稿件列出三项假设：D/C 在影响 forcibility 的变量上可交换；训练一个记录不改变其他记录的可诱导性；微调不会降低被排除记录的可诱导性。为处理微调对模型整体行为的改变，稿件提出同时比较 fine-tuned model 与 base checkpoint，形成 record membership × model training 的 2×2 设计，并用两个 estimator 做 sandwich/falsification。

#### 中心思想

控制记录只能处理目标侧差异，控制模型用于检查微调是否整体改变模型的可强迫程度。

#### E3 修改

- 把本节从“已执行的方法”改成“完整识别设计与当前实现程度”。E2/base-model arm 尚未运行，不能说本论文已经得到 sandwich interval。
- 报告 E17 匹配诊断，而不是只说 A1 可由构造保证。
- 重新审查 proposition 的条件与 bracket 方向；当前实验只支持 record-control estimator。
- SaTML 主文可以保留 2×2 作为未来完整协议，但必须在表格中明确 E1/E3 实际覆盖哪些 cell。

### 3.4 Capacity Calibration（容量校准）

#### 当前内容的中文释义

稿件定义 `α_k` 为控制分布在容量 `k` 下的成功率；定义每个控制目标首次成功的最小容量 `k_min(t)`；再把 `median H(t)/k_min(t)` 定义为模型 forcing capacity `β`，解释为每个 prompt token 实际提供的 steering bits。给定容忍 floor `α`，稿件用 `k*(α)=max{k:α_k≤α}` 选择操作点，并进一步定义 `Mem(t)=max(0,H(t)-β k_min(t))`。

#### 中心思想

试图把完整容量曲线压缩成一个可迁移常数和一个可直接选取的审计点。

#### E3 修改

- `α_k` 与容量曲线保留，并成为 E3 的核心。
- `k*` 必须根据 `α_k` 的置信区间上界选择，而不是点估计。E3 在 1% 阈值下没有任何已确认的 `k≥1`。
- 删除“`β` 是 reusable model constant”的结论。E3 的 `γ` 区间完全排除简单比例模型要求的 1。
- `H/k_min` 可放 appendix 作为描述性比率，不能作为 bits/token 的物理信道速率或跨字段安全保证。
- 删除或降级 `Mem(t)`；它直接依赖失配的 `β` 关系。
- 首次命中并不严格单调：E3 中有目标在较小 `k` 命中、较大 `k` 又失败。`k_min` 必须明确是有限 seed、有限网格、随机优化器下的观测量，并处理区间删失。
- H4 的结果应在这里直接出现：它不是旁支统计，而是决定本节核心公式是否成立的模型检验。

### 3.5 Recovering Adversarial Compression（与 ACR 的关系）

#### 当前内容的中文释义

ACR 用“找到一个比目标更短的 prompt”判断压缩/记忆。稿件称这相当于假设 prompt token 与 target token 携带同等信息，而本框架用控制目标估计 `β`，因此可以把 ACR 当作一个特殊情形。

#### 中心思想

说明本文相对于最接近的 anti-forcing 指标的增量。

#### E3 修改

- 保留概念比较，但删除“本框架已经测量出可替代 ACR 的统一 `β`”。
- E13 head-to-head 没有运行，所以不能声称经验上 subsume ACR。
- 可以把 E3 H4 写成对这一简化的警告：长度比或单一 bits/token 比率可能不能跨目标成立。

### 3.6 Reporting TPR at a Fixed Forcing Floor（固定 forcing floor 下报告 TPR）

#### 当前内容的中文释义

稿件认为 binary exact match 丢掉了优化器置信度，因此用最终目标 NLL 作为连续 score，构造 D/C ROC、AUC、`TPR@α`，并在不同阈值上最大化经验 `ε`。

#### 中心思想

把 extraction audit 改写为标准的 score-based hypothesis test。

#### E3 修改

- 当前 NLL/AUC 已从权威分析撤回，因此本小节不能以现有数据作为结果依据。
- 删除 AUC、ROC、`TPR@α` 和 threshold-maximized `ε` 的已实现声称，以及“chance-level AUC 就说明不可识别”的说法。
- 用 exact-match 的 `EMR(D)`、`EMR(C)`、差值和人员聚类置信区间作为本轮主指标。
- 如果论文仍想保留 TPR@fixed floor，需作为未来方法或重新预注册的新分析，不能从同一优化目标 NLL 直接事后选择最好阈值。

### 3.7 The Audit Protocol（审计协议）

#### 当前内容的中文释义

Algorithm 1 要求生成并匹配 C、检查 exchangeability、扫描容量并拟合 `β`、运行 record×model 四格、估计两个差值、报告 AUC/TPR，并把剩余控制作为 honeytoken。

#### 中心思想

把论文的概念变成审计者可执行的步骤。

#### E3 修改

建议重写为当前证据真正支持的协议：

1. 明确 target unit、D 的实际微调暴露与 C 的来源。
2. 在字段、字符长度、token 长度和预先规定的可比变量上匹配，并报告 overlap/SMD；失败的层不作因果归因。
3. 预先固定 `k` 网格、攻击预算、seed 聚合、exact-match 规则和容忍 floor `ε_floor`。
4. 对 D/C 运行 byte-identical 攻击，报告每个 `k` 的两条率曲线与人员聚类区间。
5. 只在控制率的置信上界不超过 `ε_floor` 时宣称操作点；没有这样的 `k` 就报告“unresolved”。
6. 报告 D−C 及区间，不把“区间包含 0”解释为等效。
7. 把 control-model、连续 score 和 honeytoken deployment 列为尚待验证的扩展。

删除 Algorithm 1 中当前没有完成的 `fit β`、四格全运行、AUC/TPR 已报告和部署防御等步骤。

---

## 4. Probes on the Capacity Axis（容量轴上的探针）

### 当前内容的中文释义

本节把 fixed prompts、PII-Scope、PII-Compass、context-free GCG、identifier-anchored GCG、fluency-regularized GCG、soft prompt 和 random restart 排在一条“表达能力/自由容量”轴上。核心比较是把 conditioning 与 free capacity 分开：anchored GCG 保留姓名/字段标签，context-free GCG 只有自由 token。soft prompt 被视为无界端点，random restart 被称为与 GCG 计算量匹配的 null。

### 中心思想

不同抽取方法不仅攻击强度不同，也给优化器不同的自由度；因此 raw success 的差异可能反映探针能力而非模型记忆。

### E3 后应如何修改

- 明确 E3 只对 context-free GCG 的 `k` 做完整扫描；不能写“每个 probe 都按完整 Algorithm 1 校准”。
- Table 3 可保留为概念 taxonomy，但“free capacity”的排序需承认不同方法的优化空间、conditioning、目标形式和预算并非一个精确标尺。
- random restart 不得称 compute-matched；真正的 E7 尚未运行。
- soft prompt 的 D/C 都 100% 是描述性端点，不能说“theory demands α→1”，因为理论命题只有上界。
- fixed prompt、PII-Scope 和 PII-Compass 的 0% 只能说明它们在这批小型自微调模型和当前配置下没有成功，不能概括这些方法本身无效。
- anchored 与 context-free 的目标长度/上下文差异必须核查，避免把 conditioning、target definition 与容量同时改变。
- fluency-regularized GCG 可作为 E1 描述结果，但 defense arms-race 尚未完成。

---

## 5. Related Work（相关工作）

### 5.1 Memorization and Extraction（记忆与抽取）

#### 当前内容的中文释义

回顾语言模型记忆、训练数据抽取、PII、去重与 `(n,p)` discoverability，指出过去工作主要报告 raw extraction rate，而本文增加 prompt capacity 轴。

#### E3 修改

- 保留，但把“过去工作都只报告 raw rate”的绝对化句子逐篇核验。
- 明确 E3 研究的是 confirmation setting，而部分 cited work 是 discovery setting，指标不可直接替换。
- 将 E3 的贡献表述为“同一优化器的经验 capacity-response”，不写成普遍的模型规模规律。

### 5.2 The Control That Was Lost（丢失的控制组）

#### 当前内容的中文释义

说明 canary exposure、DP auditing 与现代 membership inference 都依赖 member/non-member 对照，而 prompt-based elicitation 增加了一个过去没有校准的搜索自由度。

#### E3 修改

- 这是最强的 positioning，可保留。
- 加入匹配失败的教训：有控制组还不够，控制分布的可交换性必须通过平衡诊断验证。
- `ε` 联系写成理论兼容性，不写成当前实验已经给出有意义的 privacy certificate。

### 5.3 Adversarial Prompt Optimization（对抗式 prompt 优化）

#### 当前内容的中文释义

回顾 AutoPrompt、GCG、ARCA、流畅/隐蔽 jailbreak 和 model inversion，指出已有研究表明 chosen-output forcing 是可能的，本文尝试测量它。

#### E3 修改

- 用 E3 H1 作为“测量 forcing 如何随容量变化”的主要证据。
- 不声称更强优化器必然提高观测 floor；更大攻击类的理想可达集不缩小，但有限预算随机优化器的实测成功未必逐点单调。

### 5.4 Adversarial Compression（对抗压缩）

#### 当前内容的中文释义

把 ACR 视为最接近的 anti-forcing 方法，比较长度比假设、控制目标测量和操作点输出。

#### E3 修改

- 删除“framework adds frequency dose-response”等没有完成的经验贡献。
- 明确 ACR head-to-head 是未完成缺口。
- E3 H4 可成为有价值的负结果：简单线性/比例信息预算不足以描述当前目标的首次命中。

### 5.5 The 2024–25 PII-Attack Line（近期 PII 攻击）

#### 当前内容的中文释义

介绍 PII-Scope 与 PII-Compass，指出它们提供攻击与 raw rates，没有 never-trained arm 或容量扫描。

#### E3 修改

- “Neither reports…” 等新颖性判断需要 citation audit 后再保留。
- 旧 E1 对两者的 0% 不是完整 benchmark 结论；写清模型、数据和配置范围。

### 5.6 Defenses（相关防御）

#### 当前内容的中文释义

回顾 perplexity filtering，并提出 capacity limiting 与 honeytoken 是不同的防御方向。

#### E3 修改

- 相关工作可以保留，但把本文防御统一称为 proposals。
- 不把 E1 fluency probe 的单轮结果写成完整 adaptive defense evaluation。

---

## 6. Experimental Setup（实验设置）

### 6.1 Controlled Synthetic Corpus（受控合成语料）

#### 当前内容的中文释义

稿件称使用固定 seed 的 Faker 生成虚构人物，包含姓名、SSN、email、电话、地址、生日、信用卡、职业和公司，并嵌入七类模板，再与公共语料混合。C 来自不相交 seed stream，不加入微调 corpus；同样攻击 D/C。正文称本轮只报告 SSN/email 与固定 seed，其他频率、格式、非模板和 control-model arm 已由 harness 实现。

#### 中心思想

用可控合成数据提供已知的微调 membership，并使 D/C 尽可能可比。

#### E3 修改

- 实现实际有 9 个模板，正文的 7 个必须修正。
- 披露 C 是 E17 从未加入微调的候选中有放回匹配出来的不同目标；不是与 D 相同的字符串。
- 报告匹配变量及完整平衡表。SSN 通过、email 失败，不能隐藏在 appendix 一句话中。
- 说明48/50个D字段实际出现在训练文本；两个SSN缺失，已连同两个C-SSN作字段数量平衡的事后排除；只有一个C是原始E17配对，另一个是事后近邻。
- “harness implements” 与“experiment completed”分开。频率、格式、control-model 等尚未产出可用于论文的结果。
- “never trained”统一改为“not included in the fine-tuning corpus”。

### 6.2 Models（模型）

#### 当前内容的中文释义

稿件称对 GPT-2 124M/355M 和 Pythia 1.4B/2.8B 全参数微调三轮，并跟踪 PII loss；不同模型使用不同攻击预算，因此不作规模趋势比较。

#### 中心思想

E1 跨四模型展示 forcing 不是单一 checkpoint 的偶然现象。

#### E3 修改

- Pythia 实际使用 LoRA，不能称四个模型都 end-to-end fine-tuned。
- 恢复的 PII evaluation loss 为 `2.6761→2.2048→2.0889`，不是 near zero；删除“loss confirms memorization”结论。
- E3 的完整容量扫描只有 GPT-2 124M，一个 fine-tuned checkpoint；三个 seed 是攻击 seed。单独开一段写 E3 设置。
- 不把 E1 不同模型、不同攻击预算的率用于规模比较。
- checkpoint、训练配置、代码 commit、数据 manifest 和 full-launch 需要在匿名 artifact 中一一绑定。

### 6.3 Metrics and Statistics（指标与统计）

#### 当前内容的中文释义

稿件计划报告 D/C exact match、差值、AUC、经验 `ε`；区间用人员聚类 bootstrap，显著性用 paired McNemar，比例的 privacy bound 用 Clopper–Pearson。另用 unrelated random-record match 检查 substring 偶然碰撞。

#### 中心思想

统一成功规则，并对按人物聚类的目标给出不确定性。

#### E3 修改

- 主指标改为每个 `k` 的 D/C exact-match rate、差值及人员聚类 bootstrap CI。
- 删除 NLL/AUC/ROC 和经验 `ε` 结果。
- 清楚解释 H1–H4 的检验和 Holm 校正。H2 没有预先定义有效联合检验，其 `p=1` 是占位，不应当作数据算出的全局 p 值。
- H1 报 Spearman 趋势；它不证明每一对相邻 `k` 都单调。
- H2 报 zero-hit 点的保守上界和“未分辨”，不要把 0 次观察写成真实 floor=0。
- H3 报 effect size 与 CI；CI 包含 0 不是 D/C 等效。
- H4 报 censored model、删失区间、bootstrap 过程和 `γ=1` 判据。
- 统一 Table 4 所用 Newcombe interval 与 Methods 中 bootstrap 的口径。
- random-record match 若没有可追溯计数与区间就删除，不能只写“near zero”。

---

## 7. Results（结果）

### 7.1 The Forcing Floor Is Large but the Raw Rate Cannot See It（forcing 存在，而 raw rate 无法拆分它）

#### 当前内容的中文释义

这一节报告旧 E1：固定 prompt 为 0；`k=20` context-free GCG 在四个模型的 C 上也能成功；GPT-2 124M 的 D/C 都是 52%。稿件据此说 raw 52% 的 calibrated signal 为 0，并用 ROC/AUC 说明 D/C 不可区分。它还声称训练 loss 接近 0、soft prompt 对 D 100%，所以内容已被证明记住。

#### 中心思想

展示高 raw extraction rate 可以几乎完全由 forcing 基线解释。

#### E3 修改

- 把该节明确标为 E1 的早期现象结果：四模型、单训练 seed、固定 `k=20`、预算不同。
- 删除“The content is memorized”段。loss 不接近 0，soft prompt 对 C 也达到 100%，不能证明训练记忆。
- Table 4 删除 AUC 列；统一样本单位、区间方法和字段构成。
- 旧文说 forcing 为 33%–52% per model，但 Pythia-2.8B 的 C 是 0/12，这句话本身不准确。
- 删除 Figure 2 ROC 图和 chance-level ROC 讨论。
- “52%-52%=0”只能是点估计；区间宽，不能写成证明没有记忆。
- “model provably never saw”统一改为“control target absent from the fine-tuning corpus”。

### 7.2 Forcing Rises With Probe Expressivity（forcing 随探针表达能力上升）

#### 当前内容的中文释义

现稿用八种探针的 pooled 表格和柱状图展示：非优化 probe 为 0，gradient probe 的 C 为 39%–62%，soft prompt 为 100%，而 D−C 整体较小。它把这解释为 probe 越有表达能力，增加的成功越像 forcing。

#### 中心思想

把 forcing 从一个异常点扩展成“攻击自由度越大，控制命中通常越高”的谱系。

#### E3 修改

- 本节应拆成两部分：E1 probe-family spectrum 作为描述性背景；E3 within-probe `k` sweep 作为确认性主结果。
- E3 主图建议左面板画 `EMR(D)` 与 `EMR(C)` 的 14 点曲线和人员聚类 95% CI，右面板画 `D−C` 与 0 线。
- H1 在本节完整报告：`ρ=0.988965`，95% CI `[0.977915,0.994490]`，原始 `p=0.0001`，条件性 Holm `p=0.0004`；解释为总体排序趋势。
- H2 紧接 H1：`k=1,2,3` 观测 0 命中，但上界 10.33%，所以 1% 操作点未确认。
- 不再把旧 Table 5 的不同探针预算看成严格单一轴；random restart 不是 compute-matched。
- Table 5 的 69 是人物数；如果每人两个字段，person-field target 应为 138。修正 caption 和 denominator。

### 7.3 建议改为 Capacity Calibration Fails to Reduce to One Constant（容量校准不能压缩成一个通用常数）

#### 当前内容的中文释义

当前 7.3 是“The Continuous Score Is Consistent With Chance”，用 AUC 0.45–0.57 和 Figure 4 的理论曲线/单点论证连续 score 无法区分 D/C。

#### 中心思想

原意是说换阈值也没有找到 membership signal。

#### E3 修改

- 整节删除 NLL/AUC/ROC 内容。
- 用 H4 替代：定义 `log(k_min)=intercept+γ log(H)+error` 的每一项；解释 `γ=1` 才对应 `k_min≈H/β`；报告 `γ=3.484486 [2.811469,4.209360]`，所以简单比例模型不符合当前控制数据。
- Figure 4 删除“uniform SSN 理论 bound + 四模型 pooled 39% 单点”的混合画法。理论 bound 与 pooled SSN+email 经验点不是同一总体。
- H3 可放在本节或单独一小节：字段暴露更正后`k=20`的D/C差值为`0.00 pp [-8.96,+9.25]`；表述为未检测到差异，不是等效。
- H5 只放 appendix：峰值位置不稳定，不能支持一个“最优 k”。

### Results 结束时应该给出的诚实结论

- **支持**：在 GPT-2 124M 当前扫描中，forcing floor 随 `k` 强烈上升。
- **未分辨**：是否存在满足 1% floor 的正容量操作点。
- **更正后仍未分辨**：`k=20` 的微调成员相关差异；字段数量平衡的事后分析为`0.00 pp [-8.96,+9.25]`。
- **不支持**：`k_min` 与目标 self-information 之间的简单通用比例关系。
- **探索性/不稳定**：D−C 曲线的内部最优 `k`。

---

## 8. Defenses（防御）

### 当前内容的中文释义

稿件提出三类防御。第一，限制 prompt 长度或流畅度来缩小可达集合。第二，把未微调的合成控制记录部署成 honeytokens；若模型输出它们，则把事件解释为 forcing。第三，用 perplexity filter 拒绝非流畅优化 prompt，但稿件认为 fluency-regularized attacker 可以绕过。

### 中心思想

把造成审计混淆的 forcing 反过来用于检测，并让部署输入限制与审计容量使用同一语言。

### E3 后应如何修改

- 整节标题可改成“Defensive implications and proposals”。E12 没有运行，三项都不是经完整评估的防御。
- capacity bound 给的是最坏情况上界；E3 没有验证限制到某个 `k` 会在真实服务上得到预期 security/utility tradeoff。
- honeytoken proposition 依赖 decoy 与真实目标不可区分、攻击目标抽样和 `α_k` 可迁移等条件。控制字符串没有进入本次微调，不等于基础模型绝不可能知道它；“provably not recall”应限定为“not recall from this fine-tuning corpus”。
- 当前 E3 的 email 匹配失败说明 decoy indistinguishability 不能视为自动成立。
- perplexity filter 只有初步 E1 fluency probe，不能称完成 arms-race evaluation。
- 若篇幅紧张，SaTML 主文保留一段 security implication，把完整 proposition 和未验证设计移到 appendix。

---

## 9. Discussion and Limitations（讨论与局限）

### 当前内容的中文释义

稿件建议审计者总是同时报告 D raw rate 与 C forcing floor，选择容量而不是沿用 `k=20`，并优先报告差值、AUC 和 `ε`。它声称校准使不同模型和 probe 可比较，最后承认只有受控语料、四个小模型和单 seed，但认为 forcing、非识别和容量论证不依赖规模。

### 中心思想

把方法结果转化成审计实践，并界定哪些结论可以外推。

### E3 后应如何修改

- 实践建议改成：预先规定容忍 floor；测量完整控制曲线；使用上置信界选择容量；没有被分辨的点就报告没有可用操作点。
- 删除 AUC、经验 `ε`、通用 `β` 和“across-model comparable”结果声称。
- 加入以下限制：一个 E3 模型/一个训练 checkpoint；攻击 seed 不是训练复制；25 人/组；1% floor 功效不足；email 匹配失败；48/50字段实际暴露及事后字段数量平衡更正；逐目标E17配对丢失；有限网格和first-hit非单调；若干运行provenance仍为conditional；合成PII与真实世界分布不同；无法排除base-model pretraining exposure。
- 区分三个层级：理论命题的适用范围、E1 的多模型描述证据、E3 的单模型容量曲线。
- 不把“CI 包含 0”写成 audit 证明安全；它只说明当前研究没有分辨出差异。
- 明确下一步最重要的实验是字段重标、email 重匹配/扩样、独立训练 seed、base-model arm 和真正 compute-matched control。

---

## 10. Conclusion（结论）

### 当前内容的中文释义

现稿结论称优化 prompt 获得的容量足以迫使模型输出未训练记录，因此训练组 raw rate 不能区分 forcing 与 recall；GPT-2 的 52% raw rate 经校准后正好为 0。它进一步称控制差值可以给出经验 `ε`，控制还可直接成为 honeytoken，最终口号是“rate without a floor is a statement about the attack, not the model”。

### 中心思想

审计结果必须带上攻击在 non-member 上的基线，否则数字主要描述攻击能力，而非微调记忆。

### E3 后应如何修改

- 保留最后一句的思想，但避免绝对化；一个 rate 同时反映模型、攻击和目标分布。
- 用 E3 H1 替代 52%−52%=0 作为主要结论。
- 写清 1% 操作点没有确认，简单 `β` 比例模型被数据否定。
- 不声称当前实验给出 empirical `ε` 或验证 honeytoken defense。
- 不把 H3 的不显著结果写成“没有记忆”。
- 推荐结论：负控制是解释 optimization-based extraction 的必要组成；容量必须实测；当前数据表明 forcing 对 `k` 极敏感，同时警告不能靠一个通用 entropy/token 常数完成校准。

---

## Ethical Considerations（伦理考虑）

### 当前内容的中文释义

稿件说明数据完全由 Faker 生成，只测试自行微调的开放权重模型；主要双重用途风险不是制造更强攻击，而是可能让读者低估真实记忆问题。稿件承诺发布校准协议和 honeytoken 防御。

### E3/SaTML 修改

- 保留合成数据、不攻击生产 API 的说明。
- 加入攻击代码和 target-forcing 方法可能被滥用的讨论。
- 不声称 honeytoken 已验证；写成计划发布的防御性原型。
- 解释“控制成功”不能被误读为真实个人 PII 泄漏，“D/C 未分辨”也不能被误读为模型安全。
- SaTML 允许该节不计 body 页数，建议保留并加强。

---

## Open Science（开放科学）

### 当前内容的中文释义

稿件承诺匿名发布 corpus generator、control matching、checkpoints、完整 per-attempt log、capacity/`ε` 代码和 Algorithm 1，并称所有图表都由同一日志自动生成、没有手工抄数。

### E3/SaTML 修改

- SaTML 要求该节在 references 前，且匿名 artifact 必须在 2026-10-02 前冻结。
- 只承诺真正存在且可复现的材料；删除未完成的 empirical `ε` 和尚未实现的完整 Algorithm 1。
- 在冻结前解决字段暴露标签、email matching、checkpoint/full-launch 绑定、`dirty=null` manifests 和失败作业 provenance。
- “no number is transcribed by hand”与 Table 4 手工 Newcombe interval 目前矛盾，必须统一生成路径。
- artifact 中分别保存 preregistration、raw shards、合并 ledger、排除规则、分析代码、环境和图表生成记录。

---

## 新增：LLM Usage Considerations（LLM 使用说明）

SaTML 2027 要求使用 LLM 的稿件在 Open Science 之后、references 之前加入这一节。本项目使用 Codex 协助代码/数据审计、结果解释和稿件编辑，因此不能只写“用于语法润色”。至少应披露：

- Codex 参与了哪些代码检查、统计分析审计、图表/文本生成；
- 作者如何逐项对照 raw data、运行 ledger 和源代码独立验证；
- 哪些假设、统计方法和最终判断由作者决定；
- LLM 输出可能产生的遗漏、错误归因与复现限制；
- 计算环境和查询使用如何记录。

---

## Appendix（附录）

### A. Notation（符号表）

当前附录集中定义 `V`、`A_k`、`R_k`、D/C、`α_k`、`k*`、`β`、`Mem(t)`、`τ`、advantage、`ε` 等。

E3 后应删除或降级 `β` 与 `Mem(t)` 的正式地位；区分理论 `k*_thy`、基于点估计的经验 `k*` 与基于置信上界的可接受容量。补充 `γ`、删失的 `k_min` 和人员聚类单位。

### B. Data Generation（数据生成）

当前附录描述 Faker 字段、D/C seed stream、按字段/长度/token/entropy 匹配、七个模板和格式扰动。

应改为实际 9 模板；解释 E17 的匹配候选、距离、是否有放回、overlap 和 SMD；附完整 balance table；披露 email 失败与 48/50 字段暴露。不要把尚未运行的 format/non-template arms 写成本文实验。

### C. Training and Optimization Configuration（训练与优化配置）

当前附录给出统一 AdamW 全参数训练和 `k=20` GCG，并称 random restart 严格按 forward-pass 匹配。

应按模型分别写 GPT-2 full fine-tuning 与 Pythia LoRA；增加 E3 的完整 `k` 网格、三个攻击 seed、每格预算、候选数和 early stopping；删除 random restart “exactly matched”陈述。把软件版本、GPU、checkpoint hash 和 manifest 放入 artifact。

### D. Linguistic Features（语言特征）

当前附录列出 24 个 lexical/structural/syntactic/model-based 特征，并称 harness 用于 predictor analysis，但正文没有相应完成结果。

若这些特征未进入本稿任何完成分析，应删除这一节；若保留，则明确只是 artifact capability，不能占用有限主线或暗示已有 predictor 结论。

### References（参考文献）

参考文献本身不需要翻译，但 SaTML 定稿前必须单独做 citation audit，尤其核对 PII-Scope、PII-Compass、ACR、ARCA、DP auditing 和 forcing 相关句子是否由引用原文支持。当前 related-work 中多处“first”“neither”“all”等绝对表述是高风险审稿点。

---

## 当前图表逐项处理建议

| 图表 | 当前作用 | E3/SaTML 处理 |
|---|---|---|
| Figure 1 Overview | D/C 校准流程 | 保留并简化；删除 empirical `ε` 与已部署 honeytoken 暗示 |
| Table 1 Settings | discovery/confirmation/MIA 区分 | 保留，明确本文只覆盖 confirmation |
| Table 2 Formal roadmap | 标记对象是否“here” | 重做；当前把 `ε`、TPR、sandwich 等未交付项打勾 |
| Algorithm 1 | 完整审计协议 | 按置信上界、匹配门和实际实现重写 |
| Table 3 Probes | 探针 taxonomy | 保留为概念表，去掉精确单轴暗示 |
| Table 4 Per-model audit | E1 四模型 `k=20` | 可保留为次要结果；删 AUC，修单位/CI/单 seed 标签 |
| Figure 2 ROC/privacy | AUC 与 DP region | 删除；当前 NLL/AUC 已撤回 |
| Table 5 Probe spectrum | E1 八探针 | 放次要结果或 appendix；修 69 人/138 targets 与预算不匹配 |
| Figure 3 Probe spectrum | 表达能力柱状图 | 可缩小或进 appendix；不能替代 E3 同方法容量曲线 |
| Figure 4 Capacity bound | 理论 SSN 曲线+pooled 单点 | 替换为 E3 D/C 完整曲线与 D−C；理论曲线另作 inset 并分清总体 |
| Table 6 Notation | 符号表 | 移 appendix，删/降级失效的 `β`、`Mem(t)` |
| 新 Figure E3 | 14 点容量响应 | 主文核心图：D/C 曲线、CI、差值面板 |
| 新 Table E3 | H1–H5 验收 | 主文只放 H1/H2/H3/H4；H5 和逐 seed 进 appendix |
| 新 Balance table | D/C 匹配诊断 | 主文至少给字段结论，完整表进 appendix |

---

## SaTML 12 页版本的推荐结构

SaTML Research Paper 正文上限为 12 页、IEEEtran 双栏。当前 USENIX 稿不能直接改模板后压缩，应重新安排论证：

| SaTML section | 目标 | 建议正文预算 |
|---|---|---:|
| 1 Introduction | 问题、核心结果、三项贡献 | 1.25–1.5 页 |
| 2 Problem and Threat Model | confirmation setting、D/C 示例、定义 | 1.0 页 |
| 3 Why Controls Are Necessary | capacity upper bound、non-identifiability、advantage | 1.75–2.0 页 |
| 4 Calibrated Audit Design | 匹配、容量扫描、置信上界协议 | 1.25–1.5 页 |
| 5 Experimental Setup | E1/E3 数据、模型、指标、统计 | 1.25 页 |
| 6 Results | E1 forcing 存在；E3 H1/H2/H3/H4 | 2.75–3.0 页 |
| 7 Implications and Limitations | 防御仅作提案、适用边界 | 1.0 页 |
| 8 Related Work | 精炼 positioning | 0.75 页 |
| 9 Conclusion | 证据支持的结论 | 0.25 页 |

Ethical Considerations、Open Science 和 LLM Usage Considerations 按 SaTML 规则放在 references 前，并按不计页数的规则排版。完整 proofs、probe taxonomy、逐字段/逐 seed/逐目标结果、H5、balance table、实现细节和未完成扩展放 appendix；但 H1/H2/H4 的效应量和限制必须留在正文。

## 开始改写前的顺序

1. 将已完成的字段暴露更正结果写入H3/H5与主图，并披露它是事后、字段数量平衡且非完整配对。
2. 决定 email：重新匹配/扩样，或明确降级为描述性结果。
3. 冻结 SaTML 的题目、摘要、作者、单位和 topics；摘要注册截止 2026-09-22 23:59 AoE。
4. 建立新的 `satml2027_paper.tex`，使用 IEEEtran，保留 USENIX 版本作为历史稿。
5. 先重写 thesis、Abstract、Introduction 和 Results，再反向收缩 Method/Theory，避免保留结果已经否定的 `β` 主线。
6. 生成匿名 artifact 并在 2026-10-02 前冻结；论文提交截止 2026-09-29 23:59 AoE。

## 最终审稿判断

这篇稿件有一个适合 SaTML 的清晰安全与可信性问题：**一个隐私审计工具什么时候会把攻击能力误报成模型记忆？** E3 增强了最有价值的部分——同一攻击内部的容量响应——也迫使论文放弃“一个 `β` 常数就能校准所有目标”的过度简化。按照这一事实重写后，论文会比当前版本更窄，但论证更可信：它给出负控制为何必要、forcing 如何随容量变化、目前为何不能确认 1% 操作点，以及为什么实际校准必须保留完整曲线与不确定性。
