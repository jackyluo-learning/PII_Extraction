# 原始数据需求与审计

主扫描逐行原始记录可用于条件性重算；确认性来源链仍不完整。

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


## 仍需Cheaha补证

- Cheaha E17 matching records for seeds 42,1337,2024 (Colab seed42 recovered only)
- Cheaha executed checkpoint/content fingerprint; current Drive checkpoint is not proof of main model identity
- Original full environment lock and complete launch configuration
- Cleanliness evidence for 6 main shards with code.dirty=null
- Slurm job terminal states, walltime/GPU allocation, failed/preempted jobs; SSH authentication unavailable
