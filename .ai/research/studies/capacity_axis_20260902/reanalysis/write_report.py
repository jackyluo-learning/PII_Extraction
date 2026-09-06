"""Render report and tables strictly from the audited results ledger."""
from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[5];S=ROOT/'.ai/research/studies/capacity_axis_20260902';O=S/'reanalysis';A=ROOT/'artifacts/capacity_axis_20260902'
L=json.loads((S/'results.json').read_text());R=L['reanalysis']['estimates'];H=R['hypotheses'];P=L['reanalysis']['post_recovery_audit'];D=R['diagnostics']
def num(x,n=3):return '未得' if x is None else f'{x:.{n}f}'
def ci(x,n=3):return f'[{num(x[0],n)}, {num(x[1],n)}]'
def diff(v,b):return f'{100*v:+.2f} pp [{100*b[0]:+.2f}, {100*b[1]:+.2f}]'
def rate(v,b):return f'{100*v:.2f}% [{100*b[0]:.2f}, {100*b[1]:.2f}]'
def table(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join('—' if x is None else str(x) for x in r)+' |' for r in rows)+'\n'
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
summary=f'''# E3 重新分析：原始证据审计后的条件性结果

## Summary

已从台账关联的 42 个 Cheaha 原始分片重新计算，共 4,200 次攻击；每组 25 人、50 个目标，三个攻击种子。旧分析被撤回为历史版本，见 [prior_analysis.md](reanalysis/prior_analysis.md)。
H1：ρ={H['H1']['rho']:.4f}，95% CI {ci(H['H1']['ci'],4)}，支持记录数据中的上升趋势。H3：k=20 的差为 {diff(H['H3']['tau'],H['H3']['ci'])}，未排除零。
H2：1% 误报条件不可分辨；零命中的保守 Wilson 上界为 {100*H['H2']['zero_count_wilson_upper']:.2f}%，不再接受旧版的 [0,0] 区间或“不存在可用容量”结论。H4：γ={H['H4']['gamma']:.3f}，95% CI {ci(H['H4']['gamma_ci'])}，在声明的 Weibull 工作模型下排除比例关系。
**状态：可核验数据的统计重算已完成，但完整分析验收仍受 Cheaha 来源材料缺口阻塞；不是已接受的确认性研究，也未结项。** 已记录攻击耗时至少 {fulltime:.2f} h，超过 24 A100-h 预算；完整分配算力和失败成本尚未知。

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

## Preregistered Results

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

除极高容忍度下负向τ的描述性单点外，没有得到满足正向检测条件的点。**未检出不等于不存在**，尤其不能由1%不可分辨的数据证明审计不可能。原设计没有定义联合全局p，本次以p=1保留H2家族位置，标为不可检验，拒绝重复旧版floor-only p替换。

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

## Predictions vs. Outcomes

下列逐任务表区分本次能核验的结果和历史文字；不把已有description中的“done/held”当作原始证据。

__PREDICTIONS__

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
plan=json.loads((O/'prior_plan.json').read_text());prediction_rows=[]
for phase in plan['phases']:
 for t in phase['tasks']:
  tid=t['id']
  if tid in ['t1-1']:obs='原始anchor确认未命中；总体概率仍有区间';ver='符合观察预测'
  elif tid=='t1-4':obs='找回original与repro，逐目标0 flips；原始pilot dirty';ver='判定复现通过；来源限制'
  elif tid in ['t2-1','t2-2','t2-3']:obs='种子网格齐全；见seed_rates.csv和主曲线';ver='上升形状支持；不声称每相邻点单调'
  elif tid=='t2-2b':obs='逐行重建subset hash一致，N=200一致';ver='通过'
  elif tid=='t2-cp':obs='原始矩阵完整；GPU分配账目未齐，已记录攻击时间超预算';ver='未满足全部checkpoint条件'
  elif tid=='t3-2':obs='email实际攻击边际SMD不达标；Cheaha配对未齐';ver='平衡预测失败/待补证'
  elif tid=='t3-3':obs='H1趋势、H4比例被反驳；H2/H3未决，H5探索性';ver='混合；不接受旧完结结论'
  elif tid=='t3-4':obs='保留删失；右删失为零，未见预期的掉难例差异可直接解释';ver='比较需保留模型差异，不宣称预测成立'
  elif tid=='t3-1':obs='边界区间、固定家族、删失求解器经过本次校验';ver='本次实现验证通过'
  elif tid=='t3-cp':obs='新报告和数值已写；来源/匹配/总账仍待补齐';ver='尚未验收'
  elif tid=='t0-8':obs='找回Colab模型和train_meta；未重训，Cheaha模型身份待核验';ver='历史损失预测未据日志重新判定'
  else:obs='本次未重跑该执行/破坏性试验；保留历史预测';ver='未独立验收'
  prediction_rows.append([tid,t.get('prediction','未登记'),obs,ver])
summary=summary.replace('__PREDICTIONS__',table(['任务','原预测（原文）','本次可核验结果','判定'],prediction_rows))
(S/'analysis.md').write_text(summary)
audit_text='# 原始数据需求与审计\n\n主扫描逐行原始记录可用于条件性重算；确认性来源链仍不完整。\n\n'+summary.split('## Ledger Audit\n\n')[1].split('## Preregistered Results')[0]+'\n## 仍需Cheaha补证\n\n'+'\n'.join('- '+x for x in P['remaining_missing'])+'\n'
(O/'data_audit.md').write_text(audit_text)
print('Wrote analysis.md, data_audit.md and six CSV tables from results.json.')
print(curve_table.splitlines()[0]);print('\n'.join(curve_table.splitlines()[2:4]))
