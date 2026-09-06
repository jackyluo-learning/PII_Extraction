"""Render report and tables strictly from the audited results ledger."""
from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[5];S=ROOT/'.ai/research/studies/capacity_axis_20260902';O=S/'reanalysis';A=ROOT/'artifacts/capacity_axis_20260902'
L=json.loads((S/'results.json').read_text());R=L['reanalysis']['estimates'];H=R['hypotheses'];P=L['reanalysis']['post_recovery_audit'];D=R['diagnostics']
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
**状态：可核验数据的统计重算已完成，但完整分析验收仍受 Cheaha 来源材料缺口阻塞；不是已接受的确认性研究，也未结项。** 已记录攻击耗时至少 {fulltime:.2f} h，超过 24 A100-h 预算；完整分配算力和失败成本尚未知。

## “Cheaha 来源材料缺口阻塞”具体指什么

这里的“阻塞”是**正式确认性验收与研究结项的阻塞**，不是统计程序无法运行，也不是 42 个主扫描分片或 4,200 行攻击结果缺失。现有逐行结果足以重算曲线、区间和假设统计量；缺少的是证明这些结果确实来自预定模型、预定匹配、预定环境和完整调度过程的历史来源链。

{table(['缺少的 Cheaha 材料','阻塞的验收门','对当前重算的影响','解除阻塞所需证据'],[
['实际执行 checkpoint 的内容指纹及训练—攻击关联','模型身份与五项 pin','不改变已存 parquet 的算术结果；但无法证明主扫描攻击的是计划中的那一个模型','历史 checkpoint 文件或可信 SHA256，以及能把它与各主分片关联的记录'],
[f"完整 launch 配置、环境锁和 {P['main_code_dirty_counts']['None']} 个 dirty=unknown 分片的清洁证据",'配置、环境与代码清洁性','已记录字段可以复核；未记录的运行差异仍无法排除','原始完整配置、依赖锁/镜像标识、git 状态或等价不可变记录'],
['Cheaha 三个攻击种子的 E17 matching 记录','D/C 可比性与成员性解释','实际被攻击样本的边际 SMD 可算；但不能验证每个主运行最初如何配对','seeds 42、1337、2024 的原始 E17 配对表及其哈希'],
['Slurm 终态、分配 walltime/GPU 和失败或抢占任务记录','预算、失败处理与运行完整性','不进入已完成行的统计值；总 GPU-h、失败成本和所有任务终态仍未知','sacct/squeue 导出、作业日志与失败/重试清单']])}

因此当前状态应读成：**条件性数值重算完成；确认性验收被来源证据阻塞；研究尚未结项。** 即使暂时找不到上述材料，当前数值仍可作为“给定这些已保存攻击行”的条件性结果，但不能升级成无保留的确认性结论。

## Ledger Audit

{table(['审计项','结论','边界'],[
['完整性','42/42 k×seed；84/84 两组单元；168/168 字段单元；4,200 行','每个目标全部 42 个测量齐全，无重复或关键缺失'],
['标签/判定','逐行用运行版本 exact_match 重算一致；与找回注册表一致','验证记录内部一致性与标签，不等于重新运行模型'],
['运行状态','新增49条基于原始文件的记录：42主扫描＋7 Colab pilot/cost/repro','3条旧pilot保留并排除，避免同名路径误指Cheaha；没有伪造调度退出状态'],
['五项 pins','42份manifest；代码commit和环境hash一致；36份dirty=false，6份unknown','缺Cheaha执行checkpoint哈希、完整launch配置/环境；unknown未改成false'],
['数据','四份找回Colab文件的完整SHA256与历史短哈希一致','不是每个Cheaha分片的独立数据/模型快照'],
['复现','独立核对Colab original/repro：每组50目标，均0次flip，判定通过','original为dirty=true且代码版本不同；不升级为clean Cheaha复现'],
['排除','Colab pilot/cost/repro不进主分析，旧同名引用被替代且保留','没有删掉未知cleanliness的6个主分片挑选有利子集；整体仅条件性'],
['种子','42、1337、2024，全格齐全，达到协议3种子下限','同一批人的重复攻击；不是3次独立训练或150名独立对象'],
['匹配','找到Colab seed42的600条E17配对，可重算两种SMD','Cheaha三种子原始E17仍缺；不能静默用Colab冒充'],
['算力','按每组原始wallclock_s核算攻击耗时','Slurm终态/分配时间/失败列表缺失，SSH认证未通过']])}

审计文件：[初次逐行审计（补证前快照）](reanalysis/raw_data_audit.json)、[补证审计](reanalysis/post_recovery_audit.json)、[合同审查](reanalysis/contract_audit.md)、[实现审查](reanalysis/implementation_audit.md)。
当前主模型来源不足使全部主扫描记录的 `confirmatory_eligible=false`；以下检验展示在已记录攻击数据上的条件性结果，不掩盖这一资格限制。

## 预注册假设与条件性结果（Preregistered hypotheses and conditional results）

“Preregistered”修饰的是**实验前固定的假设、估计量、判据和分析计划**，不是实验跑完以后产生的数据。原始实验数据是各次攻击的逐行 parquet 和 manifest；`results.json` 是把原始文件路径、哈希、运行资格与派生统计量连起来的证据台账，也不是原始数据本身。旧标题“Preregistered Results”容易被理解成“结果被预先登记”，因此改为本标题。

{table(['对象','含义','本研究中的位置'],[
['预注册','看结果前固定：问什么、H1–H5是什么、用什么指标和判据','design.md、protocol.md，以及 plan.json 中运行前登记的 prediction；plan 的 status/description 会随后更新'],
['原始实验数据','模型攻击后实际观察到的逐行输出及伴随运行记录','Cheaha attempts parquet 与 manifests'],
['证据台账','保留原始文件哈希、运行资格、排除理由和由原始数据重算的统计量','results.json'],
['本节结果','把预先指定的判据应用到事后观察数据；来源门未齐时只能条件性解释','以下 H1–H5 与详细结果']])}

### 实验前假设、判据、结果与推论

符号约定：D 为参与微调的目标组，C 为未参与微调的控制组；k 为可自由优化的提示 token 数；αₖ 为 C 的精确命中率（forcing floor）；τrec(k) 为 D 与 C 的命中率之差。H(t) 是参考模型给目标序列的自信息量，单位 bits；k_min 是本次规定的三个种子中任一攻击首次命中该目标时的最小网格容量。

{table(['假设与地位','实验前假设','预定判据','本次观察结果','是否满足','结果含义与后续待检验推论'],[
['H1（确认性）','H0：αₖ 与 k 无关/曲线平；H1：αₖ 随 k 单调不降','k=1…64 上 Spearman ρ 的人员 bootstrap 95% CI 完全大于0',f"ρ={H['H1']['rho']:.6f}，95% CI {ci(H['H1']['ci'],6)}，Holm p={R['holm']['H1']['p_holm']:.6f}",'满足预定“总体上升趋势”判据；条件性支持 H1','当前模型、攻击器和目标内，容量增加伴随更高 forcing floor；不推出相邻点严格单调或跨模型因果规律'],
['H2（拟作确认性，联合检验未定义）','存在 k≥1，使未训练控制目标的命中概率 αₖ≤1%；设计修订又要求同一点保留可检测的组间信号','αₖ 的95%上界≤容忍度，且 τ=D−C 的95% CI 排除0；原始1%形式和设计规定的可分辨容忍度范围均报告',f"1%下零命中 Wilson 上界={100*H['H2']['zero_count_wilson_upper']:.2f}%；字面联合规则仅在100%容忍度由负向τ的k=64满足；正向τ联合点为空",'1%形式未分辨；字面联合规则出现负向单点；正向可用性未获支持，但缺联合全局检验，不能正式反驳存在性','候选推论是“低 floor 与正向成员信号可能存在张力”；后续必须把 τ 下界>0、统一区间法和全局检验写进新预注册'],
['H3（确认性）','H0：τrec(20)=0；双侧备择：τrec(20)≠0','k=20 的人员 bootstrap 95% CI 排除0',f"τ={diff(H['H3']['tau'],H['H3']['ci'])}，原始p={H['H3']['p_raw']:.6f}，Holm p={R['holm']['H3']['p_holm']:.6f}",'未满足拒绝 H0 的判据；结果不等于两组等效','下一实验应事先给出最小实际效应/等效界 δ，直接做等效性或界限检验'],
['H4（确认性）','比例 forcing 模型 k_min∝H 成立，即 log-log 斜率 γ=1','控制组删失 log-log 回归中 γ 的95% CI 若排除1，则反驳比例模型',f"γ={H['H4']['gamma']:.6f}，95% CI {ci(H['H4']['gamma_ci'],6)}，Holm p={R['holm']['H4']['p_holm']:.6f}",'不满足；在声明的 Weibull 工作模型下 H4 被反驳','通用常数 β 不可由本实验迁移使用；应预注册非线性或字段分层模型再检验'],
['H5（探索性、低功效）','H0：τrec(k) 单调或平；备择：在1与64之间有内部峰','argmax位置95%区间排除两个端点；二次项 b<0 作为次要证据',f"并列观测最大值={H['H5']['observed_maximizers']}；位置包络={ci(H['H5']['argmax_envelope_ci'],0)}；b={H['H5']['quadratic_logk_coefficient']:.5f}，95% CI {ci(H['H5']['quadratic_ci'],5)}",'位置条件满足字面要求，但曲率未排除0；总体仍不确定','k=4…48 只是下一次高功效扫描的候选区间，不能称为已定位峰值']])}

表中区分当前数据支持的结果含义与**后续待检验假设**；后者没有因出现在本报告里而变成预注册结论。H1/H4 的“确认性”表示原设计的假设地位；当前所有主扫描结论都仍受来源资格限制。

### 先读 k=0：sanity anchor

控制组 0/150；训练组 0/150；每组 25 人、三个种子。两组保守 Wilson 95% CI 均为 {ci(R['curves']['pooled'][0]['control']['ci'],4)}，组间 MOVER CI 为 {ci(R['curves']['pooled'][0]['tau_ci'],4)}。未观察到伪命中；不能把零观察写成总体概率恒为零。
`k=0` 是 fixed probe，优化目标为裸值；k≥1 是 gcg_free 的带字段前缀目标。它是单独基线，不纳入 H1/H4/H5 的容量域。

### 完整曲线

{curve_table}

B：10,000次独立D/C人员bootstrap，每次在所有k复用同一人样本，seed=20240601；W/M：遇到0/n或n/n时改用Wilson及Newcombe/MOVER。Wilson采用设计的保守n_eff=50/1.5=33.33，三种子不被当成新人。表中τ的数字是百分点；每个点的区间为描述性点区间，并非同时置信带。GPU分配小时未知，耗时栏只计攻击调用。

![容量与组间信号](../../../../artifacts/capacity_axis_20260902/figures/capacity_and_signal.png)
图1：预注册的主估计量，25人/组、3种子；阴影/误差棒为上述95%点区间。k=1.49只标示设计中的理论参照，不是本数据推出的边界。旧版把参考模型H(t)变成逐目标确定性下界的解释已撤回；尚未验证的理论概率上界不叠加成经验保证。

### H1 — 容量与 forcing floor 的上升关系

ρ={H['H1']['rho']:.6f}，95% CI {ci(H['H1']['ci'],6)}，n=25控制人、3种子；条件性Holm p={R['holm']['H1']['p_holm']:.6f}。预定CI判据支持向上趋势；不声称每个相邻网格点都严格单调，也不证明因果解释能外推到其他优化器/模型。[等权isotonic摘要](reanalysis/isotonic_summary.csv)按协议单独提供，没有用平滑曲线替换原始α或H2。

### H2 — 低误报且有可检测信号的操作点

**1%形式：inconclusive / unresolved。** 保守零计数上界为 {100*H['H2']['zero_count_wilson_upper']:.2f}%；重复攻击ICC=.5敏感性下为 {100*R['curves']['pooled'][1]['control']['repeat_icc_sensitivity_ci'][1]:.2f}%，两种约定均无法认证1%。在同一有效n约定且仍零命中的理想条件下，每组至少需 {H['H2']['minimum_people_per_arm_for_zero_wilson_upper_1pct']} 人才能把该Wilson上界压至1%；这不是τ的功效计算，也不保证出现可用点。设计写的9%是近似分辨率参照，保守双侧Wilson实际更严格。
联合判据严格按“控制组上界≤容忍度，且τ区间不含0”。以下同时给出最大可行k、检测率最大点、原始D/C比率最大点；比率不是DP下界。

{table(['容忍误报','floor-only k','联合可行k','最大联合k','检测率最优k','D/C比率最优k'],[[f"{100*x['tolerance']:g}%"+('（低于设计分辨率）' if x['below_preregistered_resolution'] else ''),str(x['floor_only_capacities']),str(x['joint_capacities']),x['largest_joint_capacity'],x['detection_optimum_k'],x['likelihood_ratio_optimum_k']] for x in H['H2']['mapping']])}

主表使用本次重分析声明的混合法：边界零/全一单元用 Wilson，其他单元用人员 bootstrap。设计要求零计数 Wilson、组间 Newcombe/MOVER 和人员 bootstrap，但没有完全消除这些规则的适用范围歧义；不能把本次所有实现细节都追溯称作预注册。为检查方法切换是否驱动结果，下面增加**事后方法一致性敏感性（exploratory）**，对所有控制组 k 统一使用 Wilson；它是诊断，不替换主分析。

{table(['标签/容忍误报','声明的混合主法：floor-only k','统一 Wilson：target-only n_eff','统一 Wilson：repeated-ICC n_eff','正向联合点：floor用敏感性法，τ沿用主CI'],[[f"(exploratory) {100*tol:g}%",str(primarymap(tol)['floor_only_capacities']),str(sensmap(target_sens,tol)['floor_only_capacities']),str(sensmap(repeat_sens,tol)['floor_only_capacities']),f"{sensmap(target_sens,tol)['positive_tau_joint_capacities_using_primary_tau_ci']} / {sensmap(repeat_sens,tol)['positive_tau_joint_capacities_using_primary_tau_ci']}"] for tol in sens_tols])}

该诊断发现一个实质性方法伪影：主法下 k=4 的控制组上界为 {100*primary_k4['control']['ci'][1]:.2f}%，所以它在5%–10%行入选；统一 Wilson 后，同一 k 的上界分别为 {100*target_k4['control_wilson_ci'][1]:.2f}%（target-only n_eff={target_sens['n_eff']:.2f}）和 {100*repeat_k4['control_wilson_ci'][1]:.2f}%（repeated-ICC n_eff={repeat_sens['n_eff']:.2f}）。这解释了为何零命中的 k=1–3 反而可能比有命中的 k=4 更难“合格”。两种一致法都没有正向τ联合点；因此敏感性分析改变部分 floor-only 映射，但不改变 H2 的“不可判定”，更不能把它升级成“已反驳”。

原设计写的是“τ区间排除0”，没有要求方向为正；因此容忍度100%下的负向 k=64 会满足字面联合判据，却不能作为预期的正向成员信号工作点。这是判据含义的缺口，不能事后悄悄改成正向检验。没有得到满足正向检测条件的点。**未检出不等于不存在**，尤其不能由1%不可分辨的数据证明审计不可能。原设计没有定义联合全局p，本次以p=1保留H2家族位置，标为不可检验，拒绝重复旧版floor-only p替换。

### H3 — k=20 的成员组差异

D={rate(R['curves']['pooled'][9]['trained']['estimate'],R['curves']['pooled'][9]['trained']['ci'])}；C={rate(R['curves']['pooled'][9]['control']['estimate'],R['curves']['pooled'][9]['control']['ci'])}。τ={diff(H['H3']['tau'],H['H3']['ci'])}，每组25人/50目标/3种子；centered bootstrap p={H['H3']['p_raw']:.6f}，Holm p=1。判定：**inconclusive，不能主张无记忆或等效**。设计未给“足够窄”的实用阈值，不能事后设定。

{table(['字段','每组人/目标/种子','D及95%CI','C及95%CI','τ及95%CI（百分点）','C/D攻击小时；GPU未知'],[[f,'25 / '+str(next(x for x in R['curves'][f] if x['k']==20)['control']['n_targets'])+' / 3',rate((x:=next(x for x in R['curves'][f] if x['k']==20))['trained']['estimate'],x['trained']['ci']),rate(x['control']['estimate'],x['control']['ci']),diff(x['tau'],x['tau_ci']),f"{x['control']['attempt_elapsed_hours']:.3f}/{x['trained']['attempt_elapsed_hours']:.3f}"] for f in ['ssn','email']])}

email达到样本全命中仍有非零总体不确定性；其差值不再被写成确定的结构性零。SSN区间更宽，合并值不能替代字段级限制。

### H4 — k_min 与 H 的比例模型

对控制组25人、50目标拟合log-log Weibull AFT，保留区间删失及右删失，三种子任一命中的最小k定义不变；10,000次按人重拟合，无最终失败。γ={H['H4']['gamma']:.6f}，95% CI {ci(H['H4']['gamma_ci'],6)}，条件性Holm p={R['holm']['H4']['p_holm']:.6f}。**声明的工作模型下 refuted：γ区间排除1。** 这不是对所有可能forcing模型的反证。
截距={H['H4']['intercept_log_scale']:.3f}，95% CI {ci(H['H4']['intercept_ci'])}。exp(−截距)为 {H['H4']['beta_scale_exp_minus_intercept']:.3e}，区间 {ci(H['H4']['beta_scale_ci'],1)}；当γ不为1，其单位不能称为通用bits/token，禁止作为可迁移β指导攻击容量。
Weibull误差分布并未在预注册中固定，因此工作分布选择明确披露；log-normal敏感性点估计γ={H['H4']['lognormal_distribution_sensitivity']['gamma']:.3f}，仅作探索性模型诊断，不以它替换主结果。

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
[完整Colab E17双SMD表](reanalysis/colab_e17_balance.csv)同时包含配对加权与控制去重边际、全匹配人群与实际D子集。其来源明确为Colab seed42；尚缺Cheaha原始E17，故不能据此宣称所有主扫描matching已核验。

## Exploratory Findings

### H5（exploratory，underpowered）

观察最大值出现在 {H['H5']['observed_maximizers']}；保留所有并列峰值后的95%位置包络为 {ci(H['H5']['argmax_envelope_ci'],0)}，{H['H5']['tied_maximum_replicates']}/10,000 重抽样存在并列最大值。log-k二次项={H['H5']['quadratic_logk_coefficient']:.5f}，95% CI {ci(H['H5']['quadratic_ci'],5)}，n=25人/组、3种子。探索性单侧曲率p={H['H5']['quadratic_one_sided_p']:.4f}（null-centered、未调整）；只保留第一个argmax的敏感性CI为 {ci(H['H5']['first_argmax_ci'],0)}。位置包络满足不触端点的字面条件，但曲率区间含0、峰区间宽且没有预定flatness等效阈值，判定为探索性不确定；既不声称定位了峰，也不声称证明曲线平坦。

### NLL/AUC（exploratory）

**NLL（negative log-likelihood，负对数似然）**衡量模型在最终优化提示 $x^*$ 下给完整目标 token 序列 $t=(t_1,\ldots,t_T)$ 分配了多少概率：

$$
\operatorname{{NLL}}(t\mid x^*)=-\sum_{{i=1}}^T \ln p_\theta(t_i\mid x^*,t_{{<i}}).
$$

原始字段 `final_target_nll` 以 nats 为单位，是整个目标序列的总和，并未除以 token 数。NLL 越小，表示模型认为该目标在该提示下越可能；它提供了比“是否精确生成”更连续的信号。由于序列总 NLL 会受目标长度影响，跨字段或长度不同目标的比较可能混入长度效应，因此这里保留字段拆分，并把合并分析仅作为探索性结果。

**AUC（area under the receiver operating characteristic curve，ROC 曲线下面积）**使用 $s=-\operatorname{{NLL}}$ 作为成员分数，并把 trained 目标记为 D、control 目标记为 C。本报告的样本 AUC 等价于：

$$
\Pr(s_D>s_C)+\tfrac12\Pr(s_D=s_C),
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
7. 找回的Colab文件独立存放，绝不覆盖同名Cheaha文件。新补录身份哈希表示本次观察到的manifest字段，不伪装为历史完整配置hash；未知清洁状态、模型身份和账目继续未知。
8. 阅读完整曲线后增加全k一致Wilson区间及MOVER对照，明确标为事后方法敏感性。有效n基于假设ICC而非测得ICC；它揭示H2部分floor-only资格依赖区间切换，不改变H2不可判定。

## Predictions vs. Outcomes

这里比较的是 `plan.json` 中登记的**各任务预测**与实际证据，不是 H1–H5 的统计检验表。plan 是持续更新的执行账本；保留 prediction 原文不等于已经证明每条文字都在数据可见前写入，尤其不能用后写的 description 当原始证据。上一版有 11/24 行显示“未独立验收”，原因是报告生成器给所有未专门编写分支的任务套用了同一句默认文案，混在一起的其实有：原始行可直接复核、只有部分证据、执行门本次未重跑、以及真正缺材料阻塞。这是报告分类错误，不是 11 项原始实验数据都缺失。

本版把 20 个原子任务和 4 个阶段 checkpoint 分开，并使用四个互斥状态。`执行门未重跑`只表示本轮统计重分析没有再做 kill-test、显存模拟等工程试验；它不自动否定历史运行，也不影响已经保存的攻击行。`缺失证据阻塞`才表示现有材料不足以完成该验收门。

__PREDICTIONS__

## Threats to Validity

- A1/matching：实际email的三项SMD未过预设门槛；原始配对诊断仅恢复Colab版本。组间差值和AUC不应直接归因为训练成员性。
- 新增CODE_MAP #16–#21逐项记录本次发现及Validity标记；#21说明H2的部分floor-only资格依赖区间方法切换，一致Wilson敏感性不能升级为确认性结论。
- CODE_MAP旧问题#1/#15（β单位及删失）：本次保留删失，另给比率；γ失配时不把截距当通用bits/token。H4并未因数据右删失少就免除非单调命中假设问题。
- CODE_MAP #7（CI不一致）：本次逐行标明B/W/M；边界格不再出现无依据的零宽区间。#8及#10的目标/提示差异：k0单列；没有把anchored对比混入本研究。
- CODE_MAP #9/#11/#12：语料生成与训练程序限制仍存在；源代码显示padding标签未屏蔽，影响模型训练条件及可外推解释。GPT-2单模型没有跨模型LoRA比较，训练工件的主扫描身份仍待补证。
- CODE_MAP #13/#14：E17有放回、去重与实际独立子集不等于配对平衡；已验证本次被攻击D/C标识及SSN/email值无交叠，不能自动推广为完整语料无污染。
- CODE_MAP #2/#3/#4：没有把异单位forward计数当GPU-h，没有预算匹配自然提示比较，也没有把原始比值称为DP证书。#5/#6（λ/软提示扫描）未运行，不能做相应结论。
- 6份main清洁状态未知；所有main缺历史checkpoint内容pin及完整环境。恢复数据和当前Colab模型hash有帮助，但不能制造Cheaha历史执行身份。
- 只有一个训练模型、25人/组、两个合成字段、200步GCG、三个攻击种子。人员bootstrap条件于这三种子，不估计跨重训练、跨硬件或新seed总体不确定性。
- 原分析已看过数据；新提出的p实现和探索性分析有研究者自由度。独立复算验证计算，不能消除这个设计层限制。

## Compute

控制组已记录攻击耗时 {R['compute']['main_attempt_elapsed_hours']['control']:.3f} h，训练组 {R['compute']['main_attempt_elapsed_hours']['trained']:.3f} h，合计 **{fulltime:.3f} h**。每份manifest为1张A100；若按所记录的独占单GPU执行，这是分配小时的下限，已比批准24 A100-h至少高 {excess:.3f} h（{100*excess/24:.1f}%）。
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
 't2-cp':{'status':'缺失证据阻塞','observed':f"攻击矩阵完整且逐行可重算；checkpoint/完整 pins、Slurm 终态和总 GPU-h 缺失，已记录攻击耗时 {fulltime:.3f} h 并超过预算。",'verdict':'ledger 数值完整，阶段验收未通过'},
 't3-1':{'status':'部分复核','observed':'边界区间、固定家族与删失求解器在本次实现中有校验；原实现缺失门槛的证据见 implementation_audit.md，但本轮校验不能追溯证明所有原始单元测试的时序。','verdict':'已覆盖实现的当前校验通过；历史全门槛时序未验收'},
 't3-2':{'status':'缺失证据阻塞','observed':'实际 email 边际 SMD 未过门槛；只恢复 Colab seed42 的 E17，缺 Cheaha 三种子配对表。','verdict':'边际可失败的预测出现；pair-wise 部分无法在主运行验收'},
 't3-3':{'status':'部分复核','observed':'H1 条件性支持；H4 被反驳；H2/H3 未决；H5 仍为探索性不确定。','verdict':'混合；原预测只部分吻合'},
 't3-4':{'status':'原始证据直接复核','observed':f"右删失比例={H['H4']['right_censored_fraction']:.3f}；H4 的 γ 排除1，使AFT截距不再对应通用bits/token的β。次要Tobit/OLS斜率比较见删失诊断。",'verdict':'β的预期大小方向无法按原定义有效判断；零右删失时“丢最难例”机制未出现'},
 't3-cp':{'status':'缺失证据阻塞','observed':'每个假设已有条件性判定或明确不可判定；来源、matching 与完整算力账仍未齐。','verdict':'字面预测满足；完整阶段验收仍未通过'},
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
print('Wrote analysis.md, data_audit.md and six CSV tables from results.json.')
print(curve_table.splitlines()[0]);print('\n'.join(curve_table.splitlines()[2:4]))
