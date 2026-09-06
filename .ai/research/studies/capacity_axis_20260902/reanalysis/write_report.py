"""Render report and tables strictly from the audited results ledger."""
from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[5];S=ROOT/'.ai/research/studies/capacity_axis_20260902';O=S/'reanalysis';A=ROOT/'artifacts/capacity_axis_20260902'
L=json.loads((S/'results.json').read_text());R=L['reanalysis']['estimates'];H=R['hypotheses'];P=L['reanalysis']['post_recovery_audit'];CHEAHA=P.get('cheaha_recovery',{});D=R['diagnostics']
T=L['reanalysis']['task_prediction_evidence']
def num(x,n=3):return '未得' if x is None else f'{x:.{n}f}'
def ci(x,n=3):return f'[{num(x[0],n)}, {num(x[1],n)}]'
def diff(v,b):return f'{100*v:+.2f} pp [{100*b[0]:+.2f}, {100*b[1]:+.2f}]'
def rate(v,b):return f'{100*v:.2f}% [{100*b[0]:.2f}, {100*b[1]:.2f}]'
def table(headers,rows):
 def cell(x):return ('—' if x is None else str(x)).replace('|','\\|').replace('\n','<br>')
 return '| '+' | '.join(cell(x) for x in headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(cell(x) for x in r)+' |' for r in rows)+'\n'
def csvout(name,rows):
 if not rows:return
 with (O/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
mainrows=[]
for x in R['curves']['pooled']:
 mainrows.append([x['k'],f"25 / 50 / 150 / {x['n_seeds']}",rate(x['control']['estimate'],x['control']['ci']),rate(x['trained']['estimate'],x['trained']['ci']),diff(x['tau'],x['tau_ci']),'W/M' if 'MOVER' in x['tau_interval_method'] else 'B',f"{x['control']['attempt_elapsed_hours']:.3f} / {x['trained']['attempt_elapsed_hours']:.3f}"])
curve_table=table(['k','每组 人/目标/尝试/种子','**α：控制组（95% CI）**','训练组 EMR（95% CI）','τ=D−C（95% CI，百分点）','区间','攻击耗时 C/D（h）；GPU-h未知'],mainrows)
flat=[]
for field,rows in R['curves'].items():
 for x in rows:
  flat.append({'field':field,'k':x['k'],'n_persons_per_arm':25,'n_seeds':3,'n_targets_per_arm':x['control']['n_targets'],'n_attempts_per_arm':x['control']['n_attempts'],'alpha':x['control']['estimate'],'alpha_lower':x['control']['ci'][0],'alpha_upper':x['control']['ci'][1],'emr_D':x['trained']['estimate'],'emr_D_lower':x['trained']['ci'][0],'emr_D_upper':x['trained']['ci'][1],'tau':x['tau'],'tau_lower':x['tau_ci'][0],'tau_upper':x['tau_ci'][1],'interval_method':x['tau_interval_method'],'C_attack_elapsed_h':x['control']['attempt_elapsed_hours'],'D_attack_elapsed_h':x['trained']['attempt_elapsed_hours'],'allocated_GPU_h':'unknown'})
csvout('isotonic_summary.csv',H['H1']['isotonic_summary']);csvout('curve_table.csv',flat);csvout('seed_rates.csv',R['seed_rates']);csvout('actual_balance.csv',D['actual_marginal_balance']);csvout('colab_e17_balance.csv',D['recovered_colab_e17_balance']);csvout('auc_exploratory.csv',R['auc_exploratory'])
fulltime=sum(R['compute']['main_attempt_elapsed_hours'].values());excess=fulltime-24
sched=CHEAHA.get('scheduler',{})
sched_gpu_h=sched.get('completed_billing_gpu_hours_lower_bound')
dirty_unknown=P.get('main_code_dirty_counts',{}).get('None',0)
h2sens=H['H2']['consistent_interval_sensitivity']['conventions']
sens_by_name={x['name']:x for x in h2sens}
sens_tols=[.01,.05,.09,.10,.15,.20]
def sensmap(convention,tol):return next(x for x in convention['mapping'] if x['tolerance']==tol)
def primarymap(tol):return next(x for x in H['H2']['mapping'] if x['tolerance']==tol)
target_sens=sens_by_name['target_only_icc_0.5'];repeat_sens=sens_by_name['all_repeats_icc_0.5']
target_k4=next(x for x in target_sens['per_k'] if x['k']==4)
repeat_k4=next(x for x in repeat_sens['per_k'] if x['k']==4)
primary_k4=next(x for x in R['curves']['pooled'] if x['k']==4)
summary=rf'''# E3 重新分析：原始证据审计后的条件性结果

## Summary

已从台账关联的 42 个 Cheaha 原始分片重新计算，共 4,200 次攻击；每组 25 人、50 个目标，三个攻击种子。旧分析被撤回为历史版本，见 [prior_analysis.md](reanalysis/prior_analysis.md)。
H1：ρ={H['H1']['rho']:.4f}，95% CI {ci(H['H1']['ci'],4)}，支持记录数据中的上升趋势。H3：k=20 的差为 {diff(H['H3']['tau'],H['H3']['ci'])}，未排除零。
H2：1% 误报条件不可分辨；零命中的保守 Wilson 上界为 {100*H['H2']['zero_count_wilson_upper']:.2f}%，不再接受旧版的 [0,0] 区间或“不存在可用容量”结论。H4：γ={H['H4']['gamma']:.3f}，95% CI {ci(H['H4']['gamma_ci'])}，在声明的 Weibull 工作模型下排除比例关系。
**状态：Cheaha 来源材料已部分恢复；统计重算和完整描述图已完成，但最终分析验收仍未通过。** 来源侧仍有历史绑定缺口；设计侧还有email平衡门失败和H2全局检验合同未定义。这不是已接受的确认性研究，也未结项。主分片记录的攻击耗时为 {fulltime:.2f} h；sacct 还记录了 {sched.get('pii_expcap_jobs','未得')} 个主作业，已完成作业的计费 GPU-h 下限为 {sched_gpu_h if sched_gpu_h is not None else '未得'}，但仍缺逐分片映射、历史 checkpoint 绑定和完整运行时间戳。

## “Cheaha 来源材料缺口阻塞”具体指什么

这里的“阻塞”是**正式确认性验收与研究结项的阻塞**，不是统计程序无法运行，也不是 42 个主扫描分片或 4,200 行攻击结果缺失。Cheaha 的 E17、42 个 manifest、精确 pip freeze 和 sacct 汇总已经恢复；仍缺的是把每个结果绑定到当时执行的 checkpoint、不可变的完整 launch 记录、6 个 `code.dirty=null` 分片的历史清洁证据、逐分片的 Slurm 失败/重试归属，以及 49 条导入记录的历史 `started_at`。

{table(['材料状态','阻塞的验收门','对当前重算的影响','仍需的证据'],[
['执行 checkpoint 的内容指纹及训练—攻击关联仍缺','模型身份与五项 pin','不改变已存 parquet 的算术结果；无法证明主扫描攻击的是计划中的那个模型','历史 checkpoint 文件或可信 SHA256，以及与各主分片的绑定记录'],
[f"PII_* 配置已在 manifest 中恢复；完整不可变 launch 记录和 {dirty_unknown} 个 dirty=unknown 分片的历史清洁证据仍缺",'配置、环境与代码清洁性','精确环境已可复核；未记录的运行差异和历史工作树状态仍无法排除','完整 resolved launch 记录、不可变环境/镜像标识、历史 git 状态或等价记录'],
['E17 已恢复：42、1337、2024 各600行；三份字节相同，控制匹配观察到有放回','D/C 可比性与成员性解释','matching 证据已不再是缺口；三份相同意味着它们不是独立 seed matching 证据','若要证明 matching 随 seed 变化，需独立且不同的 E17 记录；当前结果仅证明已恢复这三份文件'],
['sacct 已恢复：pii-expcap 45个作业，43完成、1失败、1取消；逐分片映射和失败/重试归属仍缺','预算、失败处理与运行完整性','可报告调度汇总和 GPU-h 下限；无法把每个作业终态归给具体 manifest','原始作业日志、array/shard 映射和失败/重试清单'],
['49条导入运行记录缺历史 started_at','严格运行台账 schema','不改变已保存攻击行或统计量；但不能把导入记录当作完整的历史运行日志','Cheaha 作业 start 时间与每个 manifest 的可验证绑定']])}

因此当前状态应读成：**Cheaha 来源恢复完成了一部分；条件性数值重算与描述图完成；来源链验收仍被五项历史绑定缺口阻塞；加上email平衡门失败和H2合同缺口，研究尚未结项。** 当前数值可作为“给定这些已保存攻击行”的条件性结果，但不能升级成无保留的确认性结论。

## Ledger Audit

{table(['审计项','结论','边界'],[
['完整性','42/42 k×seed；84/84 两组单元；168/168 字段单元；4,200 行','每个目标全部 42 个测量齐全，无重复或关键缺失'],
['标签/判定','逐行用运行版本 exact_match 重算一致；与找回注册表一致','验证记录内部一致性与标签，不等于重新运行模型'],
['运行状态','新增49条基于原始文件的记录：42主扫描＋7 Colab pilot/cost/repro','3条旧pilot保留并排除，避免同名路径误指Cheaha；没有伪造调度退出状态'],
['五项 pins','42份manifest；代码commit、Python/Torch/Transformers/lifelines和pip-freeze hash一致；36份dirty=false，6份unknown','缺执行checkpoint哈希、完整不可变launch记录；unknown未改成false'],
['数据','四份找回Colab文件的完整SHA256与历史短哈希一致','不是每个Cheaha分片的独立数据/模型快照'],
['复现','独立核对Colab original/repro：每组50目标，均0次flip，判定通过','original为dirty=true且代码版本不同；不升级为clean Cheaha复现'],
['排除','Colab pilot/cost/repro不进主分析，旧同名引用被替代且保留','没有删掉未知cleanliness的6个主分片挑选有利子集；整体仅条件性'],
['种子','42、1337、2024，全格齐全，达到协议3种子下限','同一批人的重复攻击；不是3次独立训练或150名独立对象'],
['匹配','Cheaha 42/1337/2024 各600条E17均已恢复；三份字节相同，控制匹配有放回','matching 来源已恢复，但字节相同的 seed 文件不提供独立 matching 变化；仍保留Colab SMD作为单独诊断'],
['算力',f"主分片攻击耗时 {fulltime:.3f} h；sacct记录45个pii-expcap作业（43完成、1失败、1取消），已完成计费GPU-h下限 {sched_gpu_h if sched_gpu_h is not None else '未得'}",'逐分片映射和失败/重试归属缺失，GPU-h是调度下限而非每行精确分摊']])}

审计文件：[初次逐行审计（补证前快照）](reanalysis/raw_data_audit.json)、[Cheaha来源恢复审计](reanalysis/cheaha_recovery_audit.json)、[补证审计](reanalysis/post_recovery_audit.json)、[合同审查](reanalysis/contract_audit.md)、[实现审查](reanalysis/implementation_audit.md)。
虽然 Cheaha 的部分来源材料已恢复，历史 checkpoint 绑定、不可变 launch 记录、6 个 dirty=unknown 分片的清洁证据、逐分片调度归属和完整 started_at 仍不足，因此全部主扫描记录继续标为 `confirmatory_eligible=false`；以下检验展示在已记录攻击数据上的条件性结果，不掩盖这一资格限制。

## 预注册假设与条件性结果（Preregistered hypotheses and conditional results）

“Preregistered”修饰的是**实验前固定的假设、估计量、判据和分析计划**，不是实验跑完以后产生的数据。原始实验数据是各次攻击的逐行 parquet 和 manifest；`results.json` 是把原始文件路径、哈希、运行资格与派生统计量连起来的证据台账，也不是原始数据本身。旧标题“Preregistered Results”容易被理解成“结果被预先登记”，因此改为本标题。

{table(['对象','含义','本研究中的位置'],[
['预注册','看结果前固定：问什么、H1–H5是什么、用什么指标和判据','design.md、protocol.md，以及 plan.json 中运行前登记的 prediction；plan 的 status/description 会随后更新'],
['原始实验数据','模型攻击后实际观察到的逐行输出及伴随运行记录','Cheaha attempts parquet 与 manifests'],
['证据台账','保留原始文件哈希、运行资格、排除理由和由原始数据重算的统计量','results.json'],
['本节结果','把预先指定的判据应用到事后观察数据；来源门未齐时只能条件性解释','以下 H1–H5 与详细结果']])}

符号约定：D 为参与微调的目标组，C 为未参与微调的控制组；k 为可自由优化的提示 token 数；αₖ 为 C 的精确命中率（forcing floor）；τrec(k) 为 D 与 C 的命中率之差。H(t) 是参考模型给目标序列的自信息量，单位 bits；k_min 是本次规定的三个种子中任一攻击首次命中该目标时的最小网格容量。
以下 H1–H5 章节各自完整说明实验前假设、预定判据、观察结果、判定和由结果产生的后续待检验推论。H1–H4 属于原设计的确认性家族；H5 在实验前已经标为低功效探索性假设。当前所有结论仍受来源资格限制。

### 先读 k=0：sanity anchor

控制组 0/150；训练组 0/150；每组 25 人、三个种子。两组保守 Wilson 95% CI 均为 {ci(R['curves']['pooled'][0]['control']['ci'],4)}，组间 MOVER CI 为 {ci(R['curves']['pooled'][0]['tau_ci'],4)}。未观察到伪命中；不能把零观察写成总体概率恒为零。
`k=0` 是 fixed probe，优化目标为裸值；k≥1 是 gcg_free 的带字段前缀目标。它是单独基线，不纳入 H1/H4/H5 的容量域。

### 完整曲线

{curve_table}

B：10,000次独立D/C人员bootstrap，每次在所有k复用同一人样本，seed=20240601；W/M：遇到0/n或n/n时改用Wilson及Newcombe/MOVER。Wilson采用设计的保守n_eff=50/1.5=33.33，三种子不被当成新人。表中τ的数字是百分点；每个点的区间为描述性点区间，并非同时置信带。GPU分配小时未知，耗时栏只计攻击调用。

![容量与组间信号](../../../../artifacts/capacity_axis_20260902/figures/capacity_and_signal.png)
图1：预注册的主估计量，25人/组、3种子；阴影/误差棒为上述95%点区间。k=1.49只标示设计中的理论参照，不是本数据推出的边界。旧版把参考模型H(t)变成逐目标确定性下界的解释已撤回；尚未验证的理论概率上界不叠加成经验保证。

### 完整 D/C、字段与靶标描述图

![完整D/C抽取率](../../../../artifacts/capacity_axis_20260902/figures/extraction_rates_by_k_full.png)
补充图S1：完整14点容量网格上的D/C精确命中率。总体面板是预注册D/C曲线的完整显示；SSN和email面板是探索性字段拆分。每个总体点汇总25人、50个`(person, field)`靶标和3个固定攻击种子，共150条重复攻击；每个字段点为25人、25个靶标和75条重复攻击。误差棒是95%点区间：普通格使用10,000次人员聚类bootstrap，0/n或n/n边界格使用报告约定的Wilson有效样本量。灰底菱形列是`k=0` fixed-probe anchor，分隔线右侧才是`k≥1` GCG扫描；H1/H5不使用`k=0`。

![按字段拆开的完整抽取计数](../../../../artifacts/capacity_axis_20260902/figures/extraction_counts_by_field_full.png)
补充图S2（探索性、描述性）：按字段和组别拆开的精确命中attempt计数。每格分母固定为75（25人×3个固定攻击种子），格内整数没有置信区间，也不能当作75个独立样本。完整CSV另给每格至少1/3、至少2/3和3/3 seeds命中的唯一靶标数。`k=0` fixed anchor 与正容量扫描分开显示。

![不同靶标在不同k下的成功情况](../../../../artifacts/capacity_axis_20260902/figures/target_success_by_k_full.png)
补充图S3（探索性、描述性）：四个面板各含25个匿名靶标和全部14个`k`；每格颜色是该靶标在三个固定攻击seed中的成功次数0–3。靶标定义为`(arm, person_id, field)`，不使用会随probe表示改变的原始`target_string`；图中不显示姓名或目标值。每个面板按首次观察到任一seed成功的`k`、总成功次数和稳定匿名编号排序；这是事后可视化排序，不把后续失败补成成功，也不把首次命中解释为真正单调阈值。三个seed是同一批人员上的重复攻击，不是三次独立训练。

三张补充图都只使用`results.json`登记并逐文件校验SHA256的42个Cheaha主扫描分片，共4,200条记录；不混入Colab pilot、cost或repro结果。总体曲线的数值地位仍是“给定这些恢复行的条件性结果”，字段和靶标图不能产生确认性发现。对应完整表为[抽取率与计数](reanalysis/extraction_rates_and_counts_full.csv)、[字段计数](reanalysis/extraction_counts_by_field_full.csv)和[靶标×k成功矩阵](reanalysis/target_success_by_k_full.csv)。

### H1 — 容量与 forcing floor 的上升关系

**实验前假设。** H1 关注控制组的 forcing floor 是否随可优化提示容量上升。零假设 H0 是 αₖ 与 k 无关，即曲线总体为平；方向性备择假设是 αₖ 在 k=1…64 上单调不降。这个假设讨论的是控制组也能被攻击强行生成目标的概率，不是 D/C 成员差异。

**预定判据。** 在所有正容量网格上计算 k 与 αₖ 的 Spearman ρ，并以控制组人员为重采样单位构造95% bootstrap CI。只有该区间完全大于0，才支持上升趋势；H1 同时进入 H1–H4 的四项 Holm 校正家族。这个判据检验总体排序趋势，不足以证明每一对相邻容量都严格不降。

**观察结果。** ρ={H['H1']['rho']:.6f}，95% CI {ci(H['H1']['ci'],6)}，n=25名控制组人员、50个目标、3个固定攻击种子；原始p={H['H1']['p_raw']:.6f}，条件性Holm p={R['holm']['H1']['p_holm']:.6f}。[等权isotonic摘要](reanalysis/isotonic_summary.csv)按协议单独提供，没有用平滑值替换原始 αₖ。

**判定。** 区间完全大于0，满足预定的总体上升判据，因此在当前保存数据和当前来源限制下，H1 得到条件性支持。原始点估计中仍有局部回落，所以结论不是“每个相邻点都单调”。

**结果含义与新推论。** 在本次 GPT-2 124M、GCG 攻击器、SSN/email 目标和固定优化预算内，增加自由提示 token 与更高 forcing floor 稳定相关。下一项可检验推论是：这个上升关系是否能跨模型规模、攻击优化器和目标格式复现；它需要新的预注册实验，当前结果不提供跨设置的因果外推。

### H2 — 低误报且有可检测信号的操作点

**实验前假设。** 原始 H2 提出存在某个 k≥1，使控制组 forcing floor αₖ 不超过1%。设计在运行前进一步指出，低 floor 本身不能构成“可用”操作点：同一个 k 还必须保留可检测的 D/C 差异 τrec(k)。因此需要同时阅读原始1%形式和最终联合形式。

**预定判据及其合同缺口。** 原始1%形式要求 αₖ 的95% CI 上界≤1%。最终联合文字要求某个 k 同时满足“αₖ 上界≤审计者容忍度”和“τrec(k) 的95% CI 排除0”，并在设计认为可分辨的 α≥9% 范围报告。设计没有给联合假设定义全局p值，也没有要求 τ 的方向必须为正；后一个遗漏会使负向差异也满足字面规则。

**观察结果：原始1%形式。** k=1、2、3 都观察到零次控制组命中，但零观察不等于总体概率为零。保守有效样本约定下，零计数 Wilson 上界为 {100*H['H2']['zero_count_wilson_upper']:.2f}%；重复攻击 ICC=.5 敏感性下为 {100*R['curves']['pooled'][1]['control']['repeat_icc_sensitivity_ci'][1]:.2f}%。两者都高于1%，所以现有样本不能确认或排除1%条件。在同一有效样本约定并继续零命中的理想情形下，每组至少需 {H['H2']['minimum_people_per_arm_for_zero_wilson_upper_1pct']} 人才能把 Wilson 上界压至1%；这只是精度计算，不是 τ 的功效保证。

**观察结果：联合形式。** 下表同时给出 floor-only 资格和字面联合资格。容忍度≤90%时没有任何字面联合点；100%时 k=64 入选，但该点 τ 为负，因此不构成研究意图中的正向成员信号。检测率最优点和 D/C 比率最优点仅是同一字面规则下的描述，不是差分隐私下界。

{table(['容忍误报','floor-only k','联合可行k','最大联合k','检测率最优k','D/C比率最优k'],[[f"{100*x['tolerance']:g}%"+('（低于设计分辨率）' if x['below_preregistered_resolution'] else ''),str(x['floor_only_capacities']),str(x['joint_capacities']),x['largest_joint_capacity'],x['detection_optimum_k'],x['likelihood_ratio_optimum_k']] for x in H['H2']['mapping']])}

**为什么下面标为 exploratory。** `exploratory` 表示“事后探索性”：这一检查是在看到完整曲线以后增加的，没有资格用来确认或反驳原来的 H2。表中的1%、5%等数字只是允许的控制组误报容忍度，不是p值；例如“(exploratory) 1%”原意是“对1%容忍度做的事后敏感性检查”。为避免误读，本版把分析地位和容忍度拆成两列。

主表使用本次重分析声明的混合法：边界零/全一单元用 Wilson，其他单元用人员 bootstrap。设计要求零计数 Wilson、组间 Newcombe/MOVER 和人员 bootstrap，但没有完全消除这些规则的适用范围歧义。下面的事后方法一致性检查对所有控制组 k 统一使用 Wilson；它只诊断结论对区间方法的敏感度，不替换主分析。

{table(['分析地位','容忍误报','声明的混合主法：floor-only k','统一 Wilson：target-only n_eff','统一 Wilson：repeated-ICC n_eff','正向联合点：floor用敏感性法，τ沿用主CI'],[['(exploratory) 事后方法敏感性',f"{100*tol:g}%",str(primarymap(tol)['floor_only_capacities']),str(sensmap(target_sens,tol)['floor_only_capacities']),str(sensmap(repeat_sens,tol)['floor_only_capacities']),f"{sensmap(target_sens,tol)['positive_tau_joint_capacities_using_primary_tau_ci']} / {sensmap(repeat_sens,tol)['positive_tau_joint_capacities_using_primary_tau_ci']}"] for tol in sens_tols])}

该诊断发现一个实质性方法伪影：主法下 k=4 的控制组上界为 {100*primary_k4['control']['ci'][1]:.2f}%，所以它在5%–10%行入选；统一 Wilson 后，同一 k 的上界分别为 {100*target_k4['control_wilson_ci'][1]:.2f}%（target-only n_eff={target_sens['n_eff']:.2f}）和 {100*repeat_k4['control_wilson_ci'][1]:.2f}%（repeated-ICC n_eff={repeat_sens['n_eff']:.2f}）。这解释了为何零命中的 k=1–3 反而可能比有命中的 k=4 更难“合格”。两种一致法都没有正向τ联合点；因此敏感性分析改变部分 floor-only 映射，但不改变 H2 的“不可判定”，更不能把它升级成“已反驳”。

**判定。** 原始1%形式未分辨。字面联合规则只在100%容忍度由负向 k=64 满足，暴露了符号合同缺口；科学上需要的正向联合点没有得到支持。由于原设计没有定义联合全局p，本次以p=1保留 H2 的多重比较位置，不能把“没有观察到正向点”升级成正式反驳存在性。

**结果含义与新推论。** 当前曲线提示低 forcing floor 与正向成员信号可能存在张力，但这只是后续假设。新的确认性研究应事先规定 τ 的下界必须大于0、对所有 k 使用一致的区间规则，并定义整个网格上的全局检验；若仍以1%为目标，还需扩大控制组精度。

### H3 — k=20 的成员组差异

**实验前假设。** H3 检验固定容量 k=20 时，训练目标组和控制目标组是否存在成员相关的精确命中率差异。零假设是 τrec(20)=0；备择是双侧的 τrec(20)≠0，不预设方向。

**预定判据。** 使用同一批人员在三个固定攻击种子上的记录，以人员为重采样单位构造 τrec(20) 的95% bootstrap CI。只有区间排除0才拒绝零假设；H3 进入四项 Holm 校正家族。设计提到区间若“足够窄”可以形成有用界限，但没有提前给出何为足够窄，所以不能事后把未显著结果解释成等效。

**观察结果。** D={rate(R['curves']['pooled'][9]['trained']['estimate'],R['curves']['pooled'][9]['trained']['ci'])}；C={rate(R['curves']['pooled'][9]['control']['estimate'],R['curves']['pooled'][9]['control']['ci'])}。τ={diff(H['H3']['tau'],H['H3']['ci'])}，每组25名人员、50个目标、3个固定种子；centered bootstrap 原始p={H['H3']['p_raw']:.6f}，Holm p={R['holm']['H3']['p_holm']:.6f}。

{table(['字段','每组人/目标/种子','D及95%CI','C及95%CI','τ及95%CI（百分点）','C/D攻击小时；GPU未知'],[[f,'25 / '+str(next(x for x in R['curves'][f] if x['k']==20)['control']['n_targets'])+' / 3',rate((x:=next(x for x in R['curves'][f] if x['k']==20))['trained']['estimate'],x['trained']['ci']),rate(x['control']['estimate'],x['control']['ci']),diff(x['tau'],x['tau_ci']),f"{x['control']['attempt_elapsed_hours']:.3f}/{x['trained']['attempt_elapsed_hours']:.3f}"] for f in ['ssn','email']])}

email达到样本全命中仍有非零总体不确定性；其差值不再被写成确定的结构性零。SSN区间更宽，合并值不能替代字段级限制。

**判定。** 置信区间包含0，未满足拒绝 H0 的判据，H3 为不确定结果。它既不是“发现成员差异”，也不是“两组等效”或“模型没有记忆”的证据。

**结果含义与新推论。** 当前数据把总体差异约束在 -7.33 到 +10.00 个百分点，但设计没有实用等效界。后续应先规定最小有意义效应 δ，再进行有足够功效的等效性或界限检验；字段级结果还提示该设计应单独处理 SSN 和 email 的不同饱和行为。

### H4 — k_min 与 H 的比例模型

**实验前假设。** H4 检验 forcing 容量是否服从比例关系 k_min≈H/β。最终治理规则把它写成控制组的 log-log 模型：若比例关系成立，log k_min 对 log H(t) 的斜率 γ 应等于1。

**预定判据。** 以三个固定种子中任一攻击首次命中的最小网格容量定义 k_min，保留区间删失和右删失；在控制组拟合 log-log 模型，并按人员 bootstrap。若 γ 的95% CI 排除1，就反驳比例模型。H4 进入四项 Holm 校正家族。设计没有预先固定 Weibull 误差分布，因此该分布是明确披露的工作模型限制。

**观察结果。** 对控制组25名人员、50个目标进行10,000次人员重拟合，无最终失败。γ={H['H4']['gamma']:.6f}，95% CI {ci(H['H4']['gamma_ci'],6)}，原始p={H['H4']['p_raw']:.6f}，条件性Holm p={R['holm']['H4']['p_holm']:.6f}。截距={H['H4']['intercept_log_scale']:.3f}，95% CI {ci(H['H4']['intercept_ci'])}；exp(−截距)={H['H4']['beta_scale_exp_minus_intercept']:.3e}，区间 {ci(H['H4']['beta_scale_ci'],1)}。log-normal 事后模型诊断给出 γ={H['H4']['lognormal_distribution_sensitivity']['gamma']:.3f}，只作探索性敏感性检查。

**判定。** γ 的区间完全排除1，因此在声明的 Weibull 工作模型下 H4 被反驳。这个结果针对比例形式，不是对所有 forcing 模型的反证。

**结果含义与新推论。** 当 γ≠1 时，exp(−截距)不再是可迁移的常数 bits/token，不能作为通用 β 指导攻击容量。后续可检验推论是 k_min 与 H 的关系可能非线性或随字段改变；应在新预注册中比较非线性与字段分层模型，并增加字段内 H 变化，避免只由 SSN/email 两个簇识别斜率。

### 四项家族与判据

{table(['假设','原始p或保留值','Holm p','条件性解读'],[[h,num(R['holm'][h]['p_raw_or_reserved'],6),num(R['holm'][h]['p_holm'],6),{'H1':'趋势判据支持','H2':'联合检验未定义；p=1保留位置','H3':'不拒绝零；不是等效','H4':'拒绝γ=1'}[h]] for h in ['H1','H2','H3','H4']])}

家族始终是四项，不丢弃H4。p算法是本次明确披露的补充实现，采用有限Monte Carlo加一校正；最小可报告值1/10001，绝不报告p=0。H3离散边界已用整数成功次数独立核对。Holm并不能补足未预注册的联合H2检验或来源缺口，所以这些是条件性重分析输出。

## Ablations

未新增模型/攻击实验。按预注册补出字段拆分、删失敏感性和matching诊断；不把分析拆分冒充新实验。

### β的直接比率与删失模型诊断

{table(['字段','n人/目标/种子','保守median H/k；95%CI','乐观网格端点；95%CI','保守值/log₂V','GPU-h'],[[x['field'],f"{x['n_persons']}/{x['n_targets']}/{x['n_seeds']}",num(x['conservative_median'])+' '+ci(x['conservative_ci']),num(x['optimistic_median'])+' '+ci(x['optimistic_ci']),num(x['conservative_fraction_log2V']),'未知；同一主扫描'] for x in D['direct_beta_brackets']])}

端点括号是网格不确定性，CI是人员bootstrap抽样不确定性，二者不可混淆。跨seed任一命中定义偏向成功率更高的三次尝试程序，不是单次攻击能力。比例模型失配下这些为描述性比率，不是物理信道速率，也不是跨字段安全保证。
Tobit次要规格：level-scale截距={H['H4']['secondary_tobit']['intercept']:.3f}，CI {ci(H['H4']['secondary_tobit']['intercept_ci'])}；斜率={H['H4']['secondary_tobit']['slope_tokens_per_bit']:.3f} tokens/bit，CI {ci(H['H4']['secondary_tobit']['slope_ci'])}，n=25控制人，10,000次人员重抽样。Complete-case线性截距={D['complete_case_linear']['intercept']:.3f}，CI {ci(D['complete_case_linear']['intercept_ci'])}；斜率={D['complete_case_linear']['slope']:.3f}，CI {ci(D['complete_case_linear']['slope_ci'])}。后者仅作删失诊断，未替换AFT。
本样本右删失比例={H['H4']['right_censored_fraction']:.3f}，未触发高删失的Turnbull替代条件。控制组 {H['H4']['nonmonotone_targets']}/50 目标出现命中后在更大k失效，违背AFT吸收阈值假设。H的控制组方差：总={D['H_variance_control']['total']:.3f}，字段内={D['H_variance_control']['within_field']:.3f}，字段间={D['H_variance_control']['between_field']:.3f}；不能仅凭两字段不同就断言总方差都来自字段间。

### 各seed首次命中敏感性（exploratory）

{table(['标签','seed / 字段','n人','median首次命中k；95%CI','右删失目标','非单调目标'],[[x['label'],f"{x['seed']} / {x['field']}",x['n_persons'],num(x['median_first_hit_k'],1)+' '+ci(x['median_ci'],1),x['right_censored_targets'],x['nonmonotone_targets']] for x in D['per_seed_kmin']])}

单seed行均为探索性敏感性；主定义仍是固定三个seed中的首次任一命中，未按这里的数值择优切换。

### 平衡与原始E17

{table(['实际攻击字段','协变量','nD/nC','SMD；95%bootstrap CI','|SMD|<0.1'],[[x['field'],x['covariate'],f"{x['n_D']}/{x['n_C']}",num(x['smd'])+' '+ci(x['ci']),'是' if x['passes_abs_0_1'] else '否'] for x in D['actual_marginal_balance']])}

SMD的0.1是预定诊断阈值，不是显著性测试。SSN字符长度两组都固定相同，因此SMD=0不意味着可检测该协变量的变异；email三项都未过点估计平衡门槛，影响D/C的成员解释。
[完整Colab E17双SMD表](reanalysis/colab_e17_balance.csv)同时包含配对加权与控制去重边际、全匹配人群与实际D子集。其来源明确为Colab seed42。Cheaha 三个 seed 的 E17 文件已经恢复，但三份字节相同；它们证明了保存的 matching 输入结构（控制记录有放回），不提供独立的 seed matching 变化。来源摘要见 [Cheaha恢复审计](reanalysis/cheaha_recovery_audit.json)。

## Exploratory Findings

### H5 — τ_rec(k) 是否在网格内部达到峰值（探索性、低功效）

**实验前假设与地位。** H5 的零假设是 τ_rec(k) 在 k=1,…,64 上单调或平坦；备择是曲线先升后降，并在两个端点之间达到内部峰值。H5 在设计阶段因预计功效不足而明确放在确认性家族之外。“探索性”表示它可以生成下一次研究的假设，但当前结果不能作为确认性发现，也不参与 H1–H4 的 Holm 校正。

**预定探索性判据。** 在每个人员 bootstrap 重抽样中保留全部并列最大点，构造 argmax 位置的 95% 包络；包络需排除端点 {{1,64}}。二次模型 τ_rec(k)=a log k+b(log k)^2 中的 b<0 是辅助曲率证据。位置与曲率应合并解释，而不能只挑其中有利的一项。

**观察结果。** 观测曲线的并列最大点为 k={H['H5']['observed_maximizers']}；保留并列峰后的 95% 位置包络为 {ci(H['H5']['argmax_envelope_ci'],0)}，10,000 次重抽样中有 {H['H5']['tied_maximum_replicates']} 次出现并列最大值。二次项 b={H['H5']['quadratic_logk_coefficient']:.5f}，95% CI {ci(H['H5']['quadratic_ci'],5)}，探索性单侧 p={H['H5']['quadratic_one_sided_p']:.4f}；只保留第一个 argmax 的敏感性 CI 为 {ci(H['H5']['first_argmax_ci'],0)}。

**判定。** 位置包络排除了两个端点，满足位置条件的字面要求；曲率证据没有排除平坦关系，而且峰位置区间很宽。H5 因此判为探索性不确定，不能声称已经定位内部峰值，也不能声称曲线平坦。

**解释与新推论。** {ci(H['H5']['argmax_envelope_ci'],0)} 只能作为下一次扫描的候选区域。结果提出的后续假设是：在更高人员样本量和更密的中段网格下，τ_rec(k) 是否存在稳定的内部峰，并且峰值是否高于两侧一个预注册的最小实际差异。新实验还需预先定义平坦曲线的等效界。

### NLL/AUC（exploratory）

**NLL（negative log-likelihood，负对数似然）** 衡量模型在最终优化提示 $x^*$ 下给完整目标 token 序列 $t=(t_1,\ldots,t_T)$ 分配了多少概率：

$$
\mathrm{{NLL}}(t \mid x^*) = -\sum_{{i=1}}^{{T}} \ln p_\theta\!\left(t_i \mid x^*, t_1,\ldots,t_{{i-1}}\right).
$$

原始字段 `final_target_nll` 以 nats 为单位，是整个目标序列的总和，并未除以 token 数。NLL 越小，表示模型认为该目标在该提示下越可能；它提供了比“是否精确生成”更连续的信号。由于序列总 NLL 会受目标长度影响，跨字段或长度不同目标的比较可能混入长度效应，因此这里保留字段拆分，并把合并分析仅作为探索性结果。

**AUC（area under the receiver operating characteristic curve，ROC 曲线下面积）** 使用 $s=-\operatorname{{NLL}}$ 作为成员分数，并把 trained 目标记为 D、control 目标记为 C。本报告的样本 AUC 等价于：

$$
\mathrm{{AUC}} = \Pr\!\left(s_D > s_C\right) + \frac{{1}}{{2}}\Pr\!\left(s_D = s_C\right),
$$

即随机抽取一个 D 分数和一个 C 分数时，D 的 NLL 更低的排序概率，平局计一半。AUC=0.5 表示没有排序分离；AUC>0.5 表示 D 倾向于具有更低 NLL；AUC<0.5 表示方向相反；AUC=1 表示样本中所有 D/C 分数都按该方向正确排序。这里在每个字段和 k 内汇总三个固定攻击种子，并以人作为 bootstrap 重采样单位。AUC 是无阈值的排序统计量，不是“某目标属于训练集”的概率、某个固定阈值的分类准确率，也不能单独证明记忆或隐私泄露。

{table(['行标签','字段/k','n人每组/种子','AUC及95%人员bootstrap CI','GPU-h'],[[x['label'],f"{x['field']} / {x['k']}",'25 / 3',num(x['auc'])+' '+ci(x['ci']),'未知；重用主扫描'] for x in R['auc_exploratory'] if x['field']!='pooled' and x['k'] in [1,2,3,8,20,64]])}

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
7. 找回的Colab文件独立存放，绝不覆盖同名Cheaha文件；Cheaha三份E17和42份manifest也以独立恢复包记录。新补录身份哈希表示本次观察到的manifest字段，不伪装为历史完整配置hash；未知清洁状态、模型身份和逐分片账目继续未知。
8. 阅读完整曲线后增加全k一致Wilson区间及MOVER对照，明确标为事后方法敏感性。有效n基于假设ICC而非测得ICC；它揭示H2部分floor-only资格依赖区间切换，不改变H2不可判定。

## Predictions vs. Outcomes

这里比较的是 `plan.json` 中登记的**各任务预测**与实际证据，不是 H1–H5 的统计检验表。plan 是持续更新的执行账本；保留 prediction 原文不等于已经证明每条文字都在数据可见前写入，尤其不能用后写的 description 当原始证据。上一版有 11/24 行显示“未独立验收”，原因是报告生成器给所有未专门编写分支的任务套用了同一句默认文案，混在一起的其实有：原始行可直接复核、只有部分证据、执行门本次未重跑、以及真正缺材料阻塞。这是报告分类错误，不是 11 项原始实验数据都缺失。

本版把 20 个原子任务和 4 个阶段 checkpoint 分开，并使用四个互斥状态。`执行门未重跑`只表示本轮统计重分析没有再做 kill-test、显存模拟等工程试验；它不自动否定历史运行，也不影响已经保存的攻击行。`缺失证据阻塞`才表示现有材料不足以完成该验收门。

__PREDICTIONS__

## Threats to Validity

- A1/matching：实际email的三项SMD未过预设门槛；Cheaha三份E17已恢复且字节相同，仍没有独立seed matching变化证据。组间差值和AUC不应直接归因为训练成员性。
- 新增CODE_MAP #16–#21逐项记录本次发现及Validity标记；#21说明H2的部分floor-only资格依赖区间方法切换，一致Wilson敏感性不能升级为确认性结论。
- CODE_MAP旧问题#1/#15（β单位及删失）：本次保留删失，另给比率；γ失配时不把截距当通用bits/token。H4并未因数据右删失少就免除非单调命中假设问题。
- CODE_MAP #7（CI不一致）：本次逐行标明B/W/M；边界格不再出现无依据的零宽区间。#8及#10的目标/提示差异：k0单列；没有把anchored对比混入本研究。
- CODE_MAP #9/#11/#12：语料生成与训练程序限制仍存在；源代码显示padding标签未屏蔽，影响模型训练条件及可外推解释。GPT-2单模型没有跨模型LoRA比较，训练工件的主扫描身份仍待补证。
- CODE_MAP #13/#14：E17有放回、去重与实际独立子集不等于配对平衡；已验证本次被攻击D/C标识及SSN/email值无交叠，不能自动推广为完整语料无污染。
- CODE_MAP #2/#3/#4：没有把异单位forward计数当GPU-h，没有预算匹配自然提示比较，也没有把原始比值称为DP证书。#5/#6（λ/软提示扫描）未运行，不能做相应结论。
- 6份main清洁状态未知；所有main缺历史checkpoint内容pin及不可变的完整 launch 记录。精确 pip freeze 和当前文件 hash 有帮助，但不能制造 Cheaha 历史执行身份。
- 只有一个训练模型、25人/组、两个合成字段、200步GCG、三个攻击种子。人员bootstrap条件于这三种子，不估计跨重训练、跨硬件或新seed总体不确定性。
- 原分析已看过数据；新提出的p实现和探索性分析有研究者自由度。独立复算验证计算，不能消除这个设计层限制。

## Compute

控制组已记录攻击耗时 {R['compute']['main_attempt_elapsed_hours']['control']:.3f} h，训练组 {R['compute']['main_attempt_elapsed_hours']['trained']:.3f} h，合计 **{fulltime:.3f} h**。每份manifest记录1张A100；sacct的已完成主作业计费 GPU-h 下限为 **{sched_gpu_h if sched_gpu_h is not None else '未得'}**，已比批准24 A100-h高出至少 {sched_gpu_h-24 if sched_gpu_h is not None else '未得'} h（按该下限计）。
这不包括加载、匹配、日志、训练、Colab pilot及失败/中断。**不能报告总GPU-h=0，也不能报告预算内。** sacct 已提供作业级汇总，但失败/取消作业尚未一对一绑定到具体 manifest，不能把该下限当作每个结果的精确分摊；本次重分析为本机CPU计算，未新增GPU实验。

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
- Cheaha 来源材料已部分恢复，但没有完成逐分片历史绑定与失败/重试归属核验；研究仍未达到最终分析验收和结项条件。

复算入口：`reanalysis/recompute.py`；完整描述图入口：`reanalysis/render_descriptive_figures.py`；报表入口：`reanalysis/write_report.py`。参数与环境见[方法约定](reanalysis/method_choices.md)、[环境记录](reanalysis/analysis_environment.txt)。完整表：[curve_table.csv](reanalysis/curve_table.csv)、[seed_rates.csv](reanalysis/seed_rates.csv)、[抽取率与计数](reanalysis/extraction_rates_and_counts_full.csv)、[字段计数](reanalysis/extraction_counts_by_field_full.csv)、[靶标×k成功矩阵](reanalysis/target_success_by_k_full.csv)、[actual_balance.csv](reanalysis/actual_balance.csv)、[探索性AUC](reanalysis/auc_exploratory.csv)。
'''
plan=json.loads((O/'prior_plan.json').read_text())
prediction_audit={
 't0-1':{'status':'原始证据直接复核','observed':'恢复的数据注册信息显示修正后的频率层级抽样为3/7/15；旧 prefix 的反事实没有复演。','verdict':'修正后结果符合；反事实部分仅可追溯'},
 't0-2':{'status':'原始证据直接复核','observed':'k=0 分片有独立命名与 capacity_k=0 标签，原始行数与预期一致且未与 GCG 分片碰撞。','verdict':'支持'},
 't0-3':{'status':'执行门未重跑','observed':'本轮没有中途终止新任务来检查部分 parquet 的保留行为。','verdict':'本轮未复测'},
 't0-4':{'status':'原始证据直接复核','observed':'42 份主 manifest 的 target_subset_hash 一致。','verdict':'支持'},
 't0-5':{'status':'执行门未重跑','observed':'本轮没有模拟 16GB 显存配置。','verdict':'本轮未复测'},
 't0-6':{'status':'部分复核','observed':'元数据支持 C4 计数为0和 D/C 值不相交；来源记录同时包含 arXiv，且本轮未重放语料再生成断言。','verdict':'复合预测只部分满足；“Wikipedia alone”不成立'},
 't0-7':{'status':'执行门未重跑','observed':'本轮没有构造缺少 lifelines 的导入环境。','verdict':'本轮未复测'},
 't0-8':{'status':'部分复核','observed':'恢复的 Colab train_meta 显示 PII eval loss：'+' → '.join(f'{x:.4f}' for x in T['training']['pii_eval_losses'])+'；文件哈希已核验，Cheaha 模型身份仍未建立。','verdict':'下降部分满足；“near zero”未获支持，且原计划未定义该阈值'},
 't0-cp':{'status':'部分复核','observed':'多项数据门可复核，但三项工程门未重跑，且历史 clean-tree/完整 pin 证据不全。','verdict':'checkpoint 未整体满足'},
 't1-1':{'status':'原始证据直接复核','observed':f"k=0 两组均为0次命中；控制组95%上界仍为 {100*R['curves']['pooled'][0]['control']['ci'][1]:.2f}%。",'verdict':'观测支持 anchor 预测；不能由零命中断言总体概率为零'},
 't1-2':{'status':'部分复核','observed':'Colab 原始 pilot 的每次攻击均值：'+ '；'.join(f"k={x['k']}：{x['mean_attempt_seconds']:.2f}s" for x in T['cost_pilot'])+f"。按notebook的T=10公式，k64实测/线性预测={T['cost_comparison']['observed_over_linear']:.4f}，未过其{T['cost_comparison']['notebook_overhead_flag_threshold']:.2f}倍提示阈值；dirty pilot、不同早停步数限制解释。",'verdict':'大幅超线性成本预测未获支持；256候选数部分仍缺直接证据'},
 't1-3':{'status':'原始证据直接复核','observed':'D=25、C=25，D 含三种频率层级。','verdict':'支持'},
 't1-4':{'status':'原始证据直接复核','observed':'找回的 Colab original/repro 在两组逐目标均为0 flips；original 为 dirty=true，代码边界也不同。','verdict':'数值判据通过；不能替代 clean Cheaha 复现'},
 't1-cp':{'status':'部分复核','observed':'anchor、样本臂和 Colab flip 判据有证据；成本结论与来源身份仍有限制。','verdict':'四项 pilot 条件未能整体确认'},
 't2-1':{'status':'原始证据直接复核','observed':'seed 42 曲线总体上升，但存在局部回落；完整曲线见 seed_rates.csv。','verdict':'字面“逐点单调”预测不满足；H1 的总体趋势判据满足'},
 't2-2':{'status':'部分复核','observed':'seed 1337 的完整网格与相同总体形状可见，但计划没有定义“within its intervals”的逐 seed 通过规则。','verdict':'定性支持，不能形式验收'},
 't2-3':{'status':'部分复核','observed':'seed 2024 的完整网格与相同总体形状可见，但同样缺预定逐 seed 判据。','verdict':'定性支持，不能形式验收'},
 't2-2b':{'status':'原始证据直接复核','observed':'42 份主分片的 subset hash 与 N=200 一致。','verdict':'支持'},
 't2-cp':{'status':'缺失证据阻塞','observed':f"攻击矩阵完整且逐行可重算；E17、精确环境和sacct已恢复，但checkpoint绑定、完整不可变launch、6个dirty=unknown历史清洁证据及逐分片Slurm归属仍缺，已记录攻击耗时 {fulltime:.3f} h。",'verdict':'ledger 数值完整，阶段验收未通过'},
 't3-1':{'status':'部分复核','observed':'边界区间、固定家族与删失求解器在本次实现中有校验；原实现缺失门槛的证据见 implementation_audit.md，但本轮校验不能追溯证明所有原始单元测试的时序。','verdict':'已覆盖实现的当前校验通过；历史全门槛时序未验收'},
 't3-2':{'status':'部分复核','observed':'实际 email 边际 SMD 未过门槛；Cheaha seed42/1337/2024 的 E17 各600行已恢复且三份字节相同，控制匹配有放回。','verdict':'边际可失败的预测出现；matching来源已恢复，但三份相同不提供独立seed变化'},
 't3-3':{'status':'部分复核','observed':'H1 条件性支持；H4 被反驳；H2/H3 未决；H5 仍为探索性不确定。','verdict':'混合；原预测只部分吻合'},
 't3-4':{'status':'原始证据直接复核','observed':f"右删失比例={H['H4']['right_censored_fraction']:.3f}；H4 的 γ 排除1，使AFT截距不再对应通用bits/token的β。次要Tobit/OLS斜率比较见删失诊断。",'verdict':'β的预期大小方向无法按原定义有效判断；零右删失时“丢最难例”机制未出现'},
 't3-cp':{'status':'缺失证据阻塞','observed':'每个假设已有条件性判定或明确不可判定；Cheaha matching、环境锁和sacct汇总已恢复，但checkpoint历史绑定、6个dirty=unknown清洁证据、逐分片调度归属仍缺。','verdict':'字面预测满足；完整阶段验收仍未通过'},
}
tasks=[t for phase in plan['phases'] for t in phase['tasks']]
assert {t['id'] for t in tasks}==set(prediction_audit),({t['id'] for t in tasks}^set(prediction_audit))
status_order=['原始证据直接复核','部分复核','执行门未重跑','缺失证据阻塞']
status_meaning={
 '原始证据直接复核':'现有逐行结果、manifest或台账字段足以判断该预测的观察部分。',
 '部分复核':'有直接证据，但原句是复合条件、缺明确阈值或仍有一部分没有重放。',
 '执行门未重跑':'本轮没有重新执行工程/破坏性测试；不表示主攻击原始行缺失。',
 '缺失证据阻塞':'现有材料不足以通过该任务或 checkpoint 的正式验收。',
}
counts={s:sum(prediction_audit[t['id']]['status']==s for t in tasks) for s in status_order}
status_table=table(['状态','任务数','含义'],[[s,counts[s],status_meaning[s]] for s in status_order])
def prediction_table(selected):
 rows=[]
 for t in selected:
  a=prediction_audit[t['id']]
  rows.append([t['id'],t.get('prediction','未登记'),a['observed'],a['verdict'],a['status']])
 return table(['任务','登记的任务预测（原文）','本次直接证据/结果','预测判定','验收状态'],rows)
atomic=[t for t in tasks if not t['id'].endswith('-cp')]
checkpoints=[t for t in tasks if t['id'].endswith('-cp')]
prediction_text=status_table+'\n### 20个原子任务\n\n'+prediction_table(atomic)+'\n### 4个阶段 checkpoint\n\n'+prediction_table(checkpoints)
summary=summary.replace('__PREDICTIONS__',prediction_text)
(S/'analysis.md').write_text(summary)
audit_text='# 原始数据需求与审计\n\n主扫描逐行原始记录可用于条件性重算；确认性来源链仍不完整。\n\n'+summary.split('## Ledger Audit\n\n')[1].split('## 预注册假设与条件性结果')[0]+'\n## 仍需Cheaha补证\n\n'+'\n'.join('- '+x for x in P['remaining_missing'])+'\n'
(O/'data_audit.md').write_text(audit_text)
print('Wrote analysis.md, data_audit.md and ledger-derived CSV tables.')
print(curve_table.splitlines()[0]);print('\n'.join(curve_table.splitlines()[2:4]))
