# 原始数据需求与审计

主扫描逐行原始记录可用于条件性重算；确认性来源链仍不完整。

| 审计项 | 结论 | 边界 |
|---|---|---|
| 完整性 | 42/42 k×seed；84/84 两组单元；168/168 字段单元；4,200 行 | 每个目标全部 42 个测量齐全，无重复或关键缺失 |
| 标签/判定 | 逐行用运行版本 exact_match 重算一致；与找回注册表一致 | 验证记录内部一致性与标签，不等于重新运行模型 |
| 运行状态 | 新增49条基于原始文件的记录：42主扫描＋7 Colab pilot/cost/repro | 3条旧pilot保留并排除，避免同名路径误指Cheaha；没有伪造调度退出状态 |
| 五项 pins | 42份manifest；代码commit、Python/Torch/Transformers/lifelines和pip-freeze hash一致；36份dirty=false，6份unknown | 缺执行checkpoint哈希、完整不可变launch记录；unknown未改成false |
| 数据 | 四份找回Colab文件的完整SHA256与历史短哈希一致 | 不是每个Cheaha分片的独立数据/模型快照 |
| 复现 | 独立核对Colab original/repro：每组50目标，均0次flip，判定通过 | original为dirty=true且代码版本不同；不升级为clean Cheaha复现 |
| 排除 | Colab pilot/cost/repro不进主分析，旧同名引用被替代且保留 | 没有删掉未知cleanliness的6个主分片挑选有利子集；整体仅条件性 |
| 种子 | 42、1337、2024，全格齐全，达到协议3种子下限 | 同一批人的重复攻击；不是3次独立训练或150名独立对象 |
| 匹配 | Cheaha 42/1337/2024 各600条E17均已恢复；三份字节相同，控制匹配有放回 | matching 来源已恢复，但字节相同的 seed 文件不提供独立 matching 变化；仍保留Colab SMD作为单独诊断 |
| 算力 | 主分片攻击耗时 26.251 h；sacct记录45个pii-expcap作业（43完成、1失败、1取消），已完成计费GPU-h下限 222.987 | 逐分片映射和失败/重试归属缺失，GPU-h是调度下限而非每行精确分摊 |


审计文件：[初次逐行审计（补证前快照）](reanalysis/raw_data_audit.json)、[Cheaha来源恢复审计](reanalysis/cheaha_recovery_audit.json)、[补证审计](reanalysis/post_recovery_audit.json)、[合同审查](reanalysis/contract_audit.md)、[实现审查](reanalysis/implementation_audit.md)。
虽然 Cheaha 的部分来源材料已恢复，历史 checkpoint 绑定、不可变 launch 记录、6 个 dirty=unknown 分片的清洁证据、逐分片调度归属和完整 started_at 仍不足，因此全部主扫描记录继续标为 `confirmatory_eligible=false`；以下检验展示在已记录攻击数据上的条件性结果，不掩盖这一资格限制。


## 仍需Cheaha补证

- 历史执行 checkpoint 内容指纹并与每个 Cheaha 分片绑定
- 超出 manifest PII_* 字段的不可变完整 launch 记录
- 6 个 code.dirty=null 主 manifest 的历史清洁证据
- 分片与 Slurm 作业的一对一映射及失败/重试归属
- 49 条导入运行记录的历史 started_at 时间戳
