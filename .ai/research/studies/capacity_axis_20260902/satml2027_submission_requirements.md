# IEEE SaTML 2027 投稿要求与当前稿件影响

核对日期：2026-09-19
权威来源：[SaTML 2027 Call for Papers](https://satml.org/call-for-papers/)；[Submission Checklist](https://satml.org/call-for-papers/checklist/)

## 投稿定位

当前稿件最符合 **Research Paper**：它提出一个校准优化式记忆审计的方法，并用新的受控实验评估该方法。它不是以整理整个研究领域为主要目标的 SoK，也不是以提出宏观立场为主的 Position Paper。

SaTML 明确要求安全与可信机器学习问题贯穿全文。对本文而言，每一个理论、方法与实验小节都应回答同一个可信性问题：**优化式抽取审计何时会把攻击的 forcing 能力误判为训练记忆，以及负控制和容量校准如何避免这一错误隐私归因。**

## 2027 年关键日期

所有截止时间均为当天 23:59 AoE（UTC-12）。

| 事项 | 截止时间 |
|---|---|
| 强制摘要注册 | 2026-09-22 |
| 正文投稿 | 2026-09-29 |
| 匿名 artifact 最后更新并冻结 | 2026-10-02 |
| Early reject 通知 | 2026-11-04 |
| 互动讨论与修订 | 2026-11-25 至 2026-12-09 |
| 决定通知 | 2026-12-16 |
| Revision 稿截止 | 2027-01-21 |
| Camera-ready | 2027 年 2 月中旬，具体日期待定 |
| 会议 | 2027 年 5 月初 |

摘要注册时必须提交非空题目和摘要，并固定作者、单位和 topics；作者和单位之后原则上不能增删，甚至 camera-ready 也不行。所有作者必须在 HotCRP 中填写 ORCID、完成 Author Certification、申报冲突，并指定一名之后不能更换的 author-reviewer。

## 篇幅与模板

- Research Paper：最多 **12 页 body text**。
- References 与 appendices 不限页，但评审没有义务阅读 appendix；支撑核心结论的证据必须留在正文。
- 必须使用双栏 IEEE proceedings 格式：`\documentclass[conference]{IEEEtran}`、默认 10pt 和默认页面几何。
- 不得修改字体、页边距或行距来挤页，否则可能 desk reject。
- Open Science、LLM usage considerations、Ethical Considerations 不计入页数。

当前 `usenix_paper_v2.tex` 使用 USENIX 模板，不能直接投稿。应保留原文件，另建 SaTML 入口文件，例如 `satml2027_paper.tex`。当前 PDF 共 17 页，references 在第 14 页开始、appendix 位于后部；总页数不能直接与 12 页比较，必须先切换 IEEEtran，再按 body text 重新计数。

## 双盲与投稿政策

- 删除作者姓名与单位；自引用使用第三人称。
- 论文、链接和 artifact 必须匿名；不能写可能泄露身份的“我们的工具已经公开”等表述。
- 可以发布预印本，但不能刻意向潜在评审宣传作者身份。
- 不得与已经发表、接受或同时在投且有正式 proceedings 的工作实质重叠。若其他投稿仍在审，可以先注册摘要，但必须在 9 月 29 日前得到拒稿或撤稿结果。
- 若本文此前在其他 venue 收到过真实评审，即使之后撤稿，也必须把最近一次完整、未编辑且匿名化的 reviews 和处理说明放在所有 appendices 之后。内部或模拟 review 不属于这一要求。

## Open Science 与 artifact

- references 前必须有 `Open Science` section，说明发布哪些 artifact，或解释为何无法分享。
- 10 月 2 日前必须在完全匿名的仓库中提供 artifact；此后整个审稿期必须可访问且不得编辑。
- 接受后必须把 artifact 发布到 Zenodo；接受以 artifact 可用为条件，除非有有效理由。
- Chairs 和 reviewers 可以核对 artifact 是否支持论文 claims。

因此，E3 当前的字段级 D 暴露、email matching、checkpoint/full-launch、`dirty=null` manifests 和作业来源问题不能只作为内部整理事项。它们必须在匿名 artifact 冻结前修复，或在论文与 artifact 中准确披露。

## LLM 使用要求

本项目使用了 Codex 协助分析、审计与写作，因此必须在 Open Science 后、references 前增加独立的 **LLM usage considerations** section。至少应说明：

- LLM 用于哪些编辑、代码或分析工作；
- 所有输出如何由作者独立核验；
- LLM 是否参与研究方法或只用于编辑；
- 使用带来的复现限制；
- 实验为何需要这些模型与计算，使用了哪些硬件，如何控制查询量和环境开销。

官方给出的编辑用途表述是：`LLMs were used for editorial purposes in this manuscript, and all outputs were inspected by the authors to ensure accuracy and originality.` 最终 section 还需按实际使用范围补充，不能只复制这一句话。

## Ethical Considerations

该 section 在 SaTML 2027 是可选且不计页数，但本文研究 PII 抽取，建议保留并加强：

- 攻击与审计代码可能被滥用；
- 为什么使用合成 PII；
- 数据主体权利、真实数据和预训练污染的界限；
- artifact 的访问与匿名化方式；
- 结果如何避免被错误解读为对具体个人数据的泄漏证明。

## 评审过程

SaTML 2027 先进行 Initial Review，可因格式、匿名、scope 或明显低于质量门槛而 desk reject。通过后先分配两位 Round 1 评审；没有可接受路径的稿件会 early reject。其余稿件进入 Round 2，随后是匿名互动讨论与修订期。决定为 Accept、Revision 或 Reject。

接受稿原则上必须由至少一名作者按 full non-student rate 注册并在 Reykjavík 现场报告，否则不能进入 IEEE proceedings；例外必须事先得到 chairs 同意。

## 对当前改稿的直接要求

1. 立即冻结 Research Paper 类别、拟用题目、摘要、作者、单位和 topics，以满足 9 月 22 日摘要注册。
2. 新建 IEEEtran 入口文件，不覆盖 USENIX 稿。
3. 把 E3 的 H1、H2 边界、H4 反证和字段级纠正后的 H3 放入 12 页正文；完整曲线、逐 seed、逐字段/靶标图和来源审计进入 appendix。
4. 核心结论不能只放 appendix；正文必须报告效应量、区间、样本范围和资格限制。
5. 删除或改写 unsupported claims：NLL/AUC、compute-matched、near-zero loss、通用 `β`、已验证的 1% `k*`、经验 `ε` 和防御有效性。
6. 加强每节与可信 ML 的联系，避免把稿件写成一般的 prompt optimization 论文。
7. 匿名化并冻结可重现 artifact；解决 E3 当前来源与标签缺口。
8. 在 references 前按顺序放置 Ethical Considerations（建议保留）、Open Science、LLM usage considerations。

## 官方链接

- [SaTML 2027 首页](https://satml.org/)
- [Call for Papers](https://satml.org/call-for-papers/)
- [Submission Checklist](https://satml.org/call-for-papers/checklist/)
- [CFP 变更记录](https://satml.org/call-for-papers/changes/)
- [投稿系统](https://satml27.hotcrp.com/)
- [IEEE conference templates](https://www.ieee.org/conferences/publishing/templates.html)
