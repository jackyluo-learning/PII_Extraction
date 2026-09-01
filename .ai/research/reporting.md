# 报告规范

_目标场次：**IEEE SaTML**。这是风格指南，不是手册。_

## 格式

- **IEEE 双栏。** 现有草稿是 USENIX 格式，需转换；仓库里 `IRI_paper.tex` 已是 IEEE 格式，
  模板可复用。
- 术语与草稿保持一致：**forcing floor**、`τ̂rec`、**EMR**、**capacity**、**probe**、
  `α_k`、`k⋆`、`β`。中文讨论时保留英文原形，不自造译名。

## 不确定性的呈现 —— 三条硬规矩

**① 永远不报裸均值。** 效应量 + 区间 + n，三者缺一不可。

```
✗  52.0
✓  52.0% [−26, 26], n=25
```

**② `EMR(D)` 绝不单独出现。** 必须与 `α_k`（forcing floor）成对。这是草稿 §3.6 自己定的
规矩：`(rate, floor)` 是最低可发表配对。一个没有 floor 的提取率，是关于攻击的陈述，
不是关于模型的。

**③ 完整报告含五项**：`EMR(D)` · `α_k` · `τ̂rec[CI]` · `AUC[CI]` · `ε̂`。

> 当前差距：Table 4 缺 `ε̂`（**代码里没有实现**），且 `TPR@α` 已经在 `table1_main` 里算出来
> 却没进表。前者要补约十行代码，后者是纯搬运。

## 区间方法 —— 统一约定

目前存在一处不一致：草稿 §6.3 写「person-clustered bootstrap」，Table 4 的 caption 写
「Newcombe (Wilson-score)」，而 `make_tables.py` **只实现了 bootstrap**。

**约定**：

- **默认 person-clustered bootstrap**（`_cluster_emr_ci` / `_cluster_diff_ci`，N=10000，
  重抽样单元是 `person_id`）
- **当某一臂计数为 0 导致 bootstrap 退化时改用 Newcombe**（例如 Pythia-2.8B 的 EMR(C)=0/12）
- **在表注中标明哪些行用了 Newcombe**，不要让一张表里混着两种方法而读者看不出来

## 探索性结果的标注

**必须在表格自身里标注**，不能只在正文说。约定：行尾上标 `ᵉ` + 表注一行说明。

> 按当前的种子硬下限 3，**run2 的全部结果都是探索性的**（单 seed）。任何引用它们的表格
> 都要带这个标记，直到补到 ≥3 seed。

## 图表约定

延用草稿已有的角色划分：

| 图 | 角色 |
|---|---|
| Fig 1 | 总览示意（D/C 双臂、校准、honeytoken） |
| Fig 2 | ROC 空间散点 + (ε,0)-DP 前沿曲线 |
| Fig 3 | 容量轴柱状（8 个 probe × 双臂） |
| Fig 4 | Prop. 1 的理论界 + 实测点 |

**所有表格由 `make_tables.py` 单一脚本生成。** 不手抄数字——草稿里 Newcombe 区间是手算的，
这正是两处不一致的来源。

## 成本报告

每个研究报 **accelerator-hours** 与 **run 数**，并说明 GPU 型号构成（Colab 每次会话分到的
加速器可能不同，不注明型号则小时数不可比）。

## 待确认

- [ ] SaTML 的投稿截止日期
- [ ] SaTML 的页数上限（决定理论下沉到附录的比例）
