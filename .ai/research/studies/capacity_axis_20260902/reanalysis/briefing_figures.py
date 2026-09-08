"""Render Chinese briefing figures from the accepted, already computed estimates.

No inferential statistics are recomputed here. Run from any working directory.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/capacity-briefing-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import PercentFormatter
import numpy as np

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[3]
DATA = STUDY / "reanalysis"
OUT = ROOT / "artifacts/capacity_axis_20260902/figures/briefing"
OUT.mkdir(parents=True, exist_ok=True)
RESULTS = STUDY / "results.json"
EST = json.loads(RESULTS.read_text())["reanalysis"]["estimates"]
GRID = [0, 1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 32, 48, 64]
POS = GRID[1:]
D, C, TEAL, INK, MUTED = "#2466A6", "#CE7721", "#178F8A", "#233246", "#607184"
FONT = "/Library/Fonts/Arial Unicode.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams.update({
    "font.family": font_manager.FontProperties(fname=FONT).get_name(),
    "font.size": 11, "axes.titlesize": 13, "axes.labelsize": 11,
    "xtick.labelsize": 10, "ytick.labelsize": 10,
    "axes.edgecolor": "#9BA9B6", "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "savefig.facecolor": "white",
    "axes.unicode_minus": False,
})
GENERATED = []


def read_csv(name):
    with (DATA / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def save(fig, name):
    for suffix in ("png", "pdf"):
        path = OUT / f"{name}.{suffix}"
        fig.savefig(path, dpi=220, facecolor="white")
        GENERATED.append(str(path.relative_to(ROOT)))
    plt.close(fig)


def foot(fig, text, y=0.015, size=10):
    fig.text(0.5, y, text, ha="center", va="bottom", fontsize=size, color=MUTED)


def axes_grid(ax, grid, include_zero=False):
    ax.set_xticks(range(len(grid)), [str(k) for k in grid])
    ax.set_xlim(-0.45, len(grid) - 0.55)
    ax.grid(axis="y", color="#E5EAF0", linewidth=0.8)
    ax.set_axisbelow(True)
    if include_zero:
        ax.axvspan(-0.45, 0.5, color="#EEF1F4", zorder=0)
        ax.axvline(0.5, color="#919DA9", linestyle=(0, (3, 3)), lw=1)


def interval(ax, x, y, ci, color, **kwargs):
    y = np.asarray(y, dtype=float)
    ci = np.asarray(ci, dtype=float)
    return ax.errorbar(x, y, yerr=np.maximum(0, np.array([y-ci[:, 0], ci[:, 1]-y])),
                       fmt="o", color=color, capsize=3, markersize=4,
                       elinewidth=1.2, **kwargs)


def workflow():
    fig, ax = plt.subplots(figsize=(11, 3))
    fig.subplots_adjust(left=0.015, right=0.985, top=0.87, bottom=0.07)
    ax.set(xlim=(0, 1), ylim=(0, 1)); ax.axis("off")
    fig.suptitle("D/C 的实验流程：同一个模型，比较训练过与未训练过的目标", fontsize=16, y=0.97)

    def box(x, y, w, h, text, color):
        ax.add_patch(FancyBboxPatch((x-w/2,y-h/2),w,h,
                     boxstyle="round,pad=0.008,rounding_size=0.018",
                     facecolor=color, edgecolor="#CCD6E0", lw=1))
        ax.text(x,y,text,ha="center",va="center",fontsize=11.5,linespacing=1.35)

    def arrow(start, end, color=MUTED):
        ax.add_patch(FancyArrowPatch(start,end,arrowstyle="-|>",
                     mutation_scale=13,color=color,lw=1.5))

    box(.09,.68,.155,.25,"训练语料\n含 D 目标", "#E7F0FA")
    box(.28,.68,.13,.25,"微调一次\n更新模型权重", "#EDF2F7")
    box(.47,.68,.155,.25,"冻结同一模型\n权重固定", "#EDF2F7")
    box(.68,.80,.16,.20,"攻击 D 目标", "#E7F0FA")
    box(.68,.43,.16,.20,"攻击 C 目标", "#FFF1DF")
    box(.89,.80,.17,.20,"D 的成功率", "#E7F0FA")
    box(.89,.43,.17,.20,"C 的成功率 α", "#FFF1DF")
    box(.47,.22,.155,.20,"C 目标\n不进入微调", "#FFF1DF")
    arrow((.176,.68),(.207,.68)); arrow((.353,.68),(.385,.68))
    arrow((.555,.72),(.592,.80)); arrow((.555,.62),(.592,.46))
    arrow((.555,.24),(.63,.32),C)
    arrow((.766,.80),(.799,.80),D); arrow((.766,.43),(.799,.43),C)
    ax.text(.89,.11,"差值 τ = D 成功率 − α",ha="center",fontsize=11.5,fontweight="bold")
    ax.text(.07,.18,"两组采用相同的攻击方法、k 和预算。\n攻击优化提示；不更新模型权重。", fontsize=10.8, color=MUTED, va="center")
    save(fig,"workflow")


def rates_full():
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.3), sharey=True)
    fig.subplots_adjust(left=.065,right=.985,bottom=.23,top=.75,wspace=.11)
    fig.suptitle("完整抽取率：D 与 C 都随 k 增大而更容易成功",fontsize=16,y=.97)
    for ax, field, title in zip(axes,["pooled","ssn","email"],
                               ["两字段合并","SSN · 探索性 (exploratory)","email · 探索性 (exploratory)"]):
        rows=EST["curves"][field]
        assert [r["k"] for r in rows] == GRID
        axes_grid(ax, GRID, True)
        for arm,color,offset,label in [("trained",D,-.09,"D：训练过"),("control",C,.09,"C：未训练过")]:
            vals=np.array([r[arm]["estimate"] for r in rows]); ci=[r[arm]["ci"] for r in rows]
            # The k=0 anchor is separate from the optimized positive-capacity sweep.
            ax.plot(np.arange(1,14)+offset,vals[1:],color=color,lw=1.7)
            interval(ax,np.arange(14)+offset,vals,ci,color,label=label,zorder=3)
        ax.set_title(title,fontsize=11.5,pad=8)
        ax.set_xlabel("k（优化提示的 token 数）",fontsize=10)
        ax.set_ylim(-.035,1.05);ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.tick_params(axis="x",labelsize=8.7)
    axes[0].set_ylabel("完整目标的精确生成成功率")
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc="upper center",bbox_to_anchor=(.5,.905),ncol=2,frameon=False,fontsize=11)
    foot(fig,"横轴按实验网格等距排列，数值间距不等；灰区 k=0 为无优化基线。竖线为逐点 95% 区间。",.063,10)
    foot(fig,"每组 25 人、两字段共 50 个目标、3 个攻击 seed；合并每 k 为 150 次，单字段为 75 次。",.015,10)
    save(fig,"rates_full")


def counts_full():
    rows=read_csv("extraction_counts_by_field_full.csv")
    index={(r["arm"],r["field"],int(r["k"])):r for r in rows}
    group=[("trained","ssn","D · SSN"),("control","ssn","C · SSN"),
           ("trained","email","D · email"),("control","email","C · email")]
    a=np.array([[int(index[arm,field,k]["successful_attempts"]) for k in GRID] for arm,field,_ in group])
    fig,ax=plt.subplots(figsize=(11,3.3))
    fig.subplots_adjust(left=.12,right=.985,bottom=.27,top=.76)
    fig.suptitle("按字段拆分的完整抽取计数",fontsize=16,y=.96)
    ax.imshow(a,cmap="Blues",vmin=0,vmax=75,aspect="auto")
    ax.set_xticks(range(14),GRID);ax.set_yticks(range(4),[g[2] for g in group])
    for i in range(4):
        for j in range(14):
            ax.text(j,i,f"{a[i,j]}/75",ha="center",va="center",fontsize=10.3,
                    color="white" if a[i,j]>=45 else INK)
    ax.set_xticks(np.arange(-.5,14,1),minor=True);ax.set_yticks(np.arange(-.5,4,1),minor=True)
    ax.grid(which="minor",color="white",lw=1.3);ax.tick_params(which="minor",bottom=False,left=False)
    ax.axvline(.5,color=INK,lw=2.3);ax.set_xlabel("k（按实验网格等距排列；k=0 为独立基线）")
    foot(fig,"每格 = 成功攻击次数 / 75 次；75 = 25 个目标 × 3 个攻击 seed。同一目标可计入多次成功。",.035,11)
    save(fig,"counts_full")


def targets(field):
    rows=[r for r in read_csv("target_success_by_k_full.csv") if r["field"]==field]
    cmap=ListedColormap(["#F0F4F5","#B1DAD2","#418F9A","#174B70"])
    norm=BoundaryNorm([-.5,.5,1.5,2.5,3.5],4)
    fig,axes=plt.subplots(1,2,figsize=(11,5.3))
    fig.subplots_adjust(left=.075,right=.985,bottom=.18,top=.81,wspace=.20)
    fig.suptitle(f"{field.upper() if field=='ssn' else 'email'}：全部 50 个目标在每个 k 下的成功次数",fontsize=15,y=.975)
    for ax,arm,label in zip(axes,["trained","control"],["D · 25 个训练目标","C · 25 个未训练目标"]):
        subset=[r for r in rows if r["arm"]==arm]
        per_target={}
        for row in subset:per_target.setdefault(row["target_id"],[]).append(row)
        def key(t):
            rs=per_target[t]
            hits=[int(r["k"]) for r in rs if int(r["successes_out_of_3"])>0]
            return (min(hits) if hits else float("inf"),-sum(int(r["successes_out_of_3"]) for r in rs),t)
        ids=sorted(per_target,key=key)
        assert len(ids)==25
        a=np.array([[int(next(r for r in per_target[t] if int(r["k"])==k)["successes_out_of_3"]) for k in GRID] for t in ids])
        assert a.shape==(25,14)
        ax.imshow(a,cmap=cmap,norm=norm,aspect="auto",interpolation="nearest")
        ax.set_xticks(range(14),GRID);ax.set_yticks(range(25),ids)
        ax.tick_params(axis="y",labelsize=9.1,length=0,pad=3);ax.tick_params(axis="x",labelsize=9)
        for i in range(25):
            for j in range(14):
                ax.text(j,i,str(a[i,j]),ha="center",va="center",fontsize=9.1,
                        color="white" if a[i,j]>=2 else INK)
        ax.set_title(label,fontsize=12,pad=6)
        ax.set_xticks(np.arange(-.5,14,1),minor=True);ax.set_yticks(np.arange(-.5,25,1),minor=True)
        ax.grid(which="minor",color="white",lw=.45);ax.tick_params(which="minor",bottom=False,left=False)
        ax.axvline(.5,color=INK,lw=1.9)
    # A compact discrete legend makes the counts readable without a colorbar.
    legend_handles=[plt.Line2D([0],[0],marker="s",markersize=10,color="none",markerfacecolor=cmap(i),
                              markeredgecolor="#9EAFBB",label=f"{i}/3 次成功") for i in range(4)]
    fig.legend(handles=legend_handles,loc="upper center",bbox_to_anchor=(.5,.936),ncol=4,frameon=False,fontsize=10.5)
    fig.text(.5,.103,"k（按实验网格等距排列；竖线左侧是 k=0）",ha="center",fontsize=10)
    foot(fig,"匿名编号；每格是同一目标在 3 个攻击 seed 中的成功次数。按首次命中、总成功次数、编号排序。",.052,10)
    foot(fig,"保留每个 k 的实际成败：较小 k 成功，不代表较大 k 必然成功。目标逐格描述属于探索性结果。",.012,10)
    save(fig,f"targets_{field}")


def balance():
    rows=read_csv("actual_balance.csv")
    label={"char_len":"字符长度","target_len_tokens":"token 长度","target_H_bits":"目标信息量 H(t)"}
    fig,ax=plt.subplots(figsize=(7,3.5))
    fig.subplots_adjust(left=.28,right=.96,bottom=.24,top=.77)
    fig.suptitle("D/C 匹配平衡：SSN 点估计接近，email 仍有差异",fontsize=13,y=.97)
    ax.axvspan(-.1,.1,color="#DDEFE8",label="参考范围：−0.1 至 +0.1")
    ax.axvline(0,color=MUTED,lw=.9)
    labels=[]
    for i,r in enumerate(rows):
        smd=float(r["smd"]);lo,hi=json.loads(r["ci"]);color=D if r["field"]=="ssn" else C
        ax.errorbar(smd,i,xerr=[[smd-lo],[hi-smd]],fmt="o",color=color,capsize=3,markersize=5)
        labels.append(f"{r['field'].upper() if r['field']=='ssn' else 'email'} · {label[r['covariate']]}")
    ax.set_yticks(range(6),labels);ax.invert_yaxis();ax.set_xlim(-.85,1.35)
    ax.set_xlabel("标准化均值差 SMD（D − C；0 表示均值相同）",fontsize=10)
    ax.grid(axis="x",color="#E5EAF0");ax.set_axisbelow(True)
    fig.text(.5,.845,"点为 SMD，横线为 95% 区间；绿色带是平衡诊断参考，不是显著性检验。",ha="center",fontsize=9.7,color=MUTED)
    foot(fig,"实际攻击目标，每组每字段 25 个；正值表示 D 的该特征均值更大。此图不属于 H1–H5 检验。",.025,9.7)
    save(fig,"balance")


def h1_floor():
    rows=EST["curves"]["pooled"][1:]
    fig,ax=plt.subplots(figsize=(7,3.4))
    fig.subplots_adjust(left=.105,right=.98,bottom=.23,top=.80)
    fig.suptitle("H1：提示容量增大时，未训练目标也更容易被生成",fontsize=13,y=.97)
    axes_grid(ax,POS)
    shades=["#D2DCE7","#AFC0D2","#869DB8"]
    for color,seed in zip(shades,[42,1337,2024]):
        seedrows={r["k"]:r for r in EST["seed_rates"] if r["seed"]==seed and r["arm"]=="control"}
        ax.plot(range(13),[seedrows[k]["rate"] for k in POS],".-",color=color,lw=1,markersize=3,label=f"seed {seed}")
    vals=[r["control"]["estimate"] for r in rows]
    ax.plot(range(13),vals,color=C,lw=2)
    interval(ax,range(13),vals,[r["control"]["ci"] for r in rows],C,label="C 合并估计与 95% 区间",zorder=4)
    ax.set_ylim(-.025,1.045);ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylabel("控制组成功率 α");ax.set_xlabel("k（正容量；按实验网格等距排列）")
    ax.legend(fontsize=8.2,loc="upper left",frameon=False,ncol=2)
    foot(fig,"3 个 seed 是对同一批目标的重复攻击；不代表 3 次独立微调。区间为逐点 95% 区间。",.025,9.8)
    save(fig,"h1_floor")


def h2_floor():
    rows=[r for r in EST["curves"]["pooled"] if r["k"] in [1,2,3,4]]
    fig,ax=plt.subplots(figsize=(7,3.4))
    fig.subplots_adjust(left=.105,right=.81,bottom=.28,top=.78)
    fig.suptitle("H2：零次成功，仍不足以确认控制组上限 ≤ 1%",fontsize=13,y=.97)
    for val,color in [(1,"#AC5350"),(5,"#9B8745"),(9,"#538D76")]:
        ax.axhline(val,color=color,lw=1,ls="--")
        ax.text(3.45,val,f"允许上限 {val}%",fontsize=9,color=color,va="center",clip_on=False)
    vals=np.array([r["control"]["estimate"] for r in rows])*100
    ci=np.array([r["control"]["ci"] for r in rows])*100
    interval(ax,[0,1,2],vals[:3],ci[:3],D,zorder=4)
    interval(ax,[3],vals[3:],ci[3:],C,zorder=4)
    for x in range(3):ax.text(x,10.6,"上界 10.33%",ha="center",fontsize=9,color=D)
    ax.text(3,3.6,"上界 3.33%",ha="center",fontsize=9,color=C)
    ax.set_xticks(range(4),["1\nWilson","2\nWilson","3\nWilson","4\n人员重采样"])
    ax.set_xlim(-.45,3.4);ax.set_ylim(-.5,12);ax.set_ylabel("C 成功率与 95% 区间（%）")
    ax.set_xlabel("k 与区间方法",fontsize=10);ax.grid(axis="y",color="#E5EAF0");ax.set_axisbelow(True)
    fig.text(.5,.835,"k=1–3：0/150 次成功；k=4：2/150 次成功（1.33%）。",ha="center",fontsize=10.5)
    foot(fig,"Wilson 使用假定的有效样本量；k=4 使用人员聚类 bootstrap。方法切换使区间宽度不可直接比较。",.071,9.5)
    foot(fig,"因此，不能根据 k=4 的区间更窄就认定它比零命中点更安全。",.016,10)
    save(fig,"h2_floor")


def h3_difference():
    rows=[next(r for r in EST["curves"][f] if r["k"]==20) for f in ["pooled","ssn","email"]]
    fig,ax=plt.subplots(figsize=(7,3.4))
    fig.subplots_adjust(left=.24,right=.75,bottom=.23,top=.77)
    fig.suptitle("H3：k=20 时，D − C 的区间包含 0",fontsize=13,y=.97)
    ax.axvline(0,color=MUTED,lw=1.2,ls="--")
    labels=["两字段合并\nH3 主分析","SSN\n探索性","email\n探索性"]
    for i,r in enumerate(rows):
        tau=r["tau"]*100;lo,hi=np.array(r["tau_ci"])*100;color=TEAL if i==0 else D
        ax.errorbar(tau,i,xerr=[[tau-lo],[hi-tau]],fmt="o",color=color,capsize=4,markersize=6)
        ax.text(1.035,i,f"{tau:+.2f}\n[{lo:+.2f}, {hi:+.2f}]",fontsize=9.5,va="center",transform=ax.get_yaxis_transform())
    ax.set_yticks(range(3),labels);ax.set_ylim(2.5,-.5);ax.set_xlim(-20,23)
    ax.text(1.035,-.48,"差值与 95% 区间",fontsize=9.5,va="bottom",transform=ax.get_yaxis_transform(),color=MUTED)
    ax.set_xlabel("D 成功率 − C 成功率 τ（百分点）")
    ax.grid(axis="x",color="#E5EAF0");ax.set_axisbelow(True)
    fig.text(.5,.84,"合并：D = 82.00%，C = 80.67%，差值 = +1.33 个百分点。",ha="center",fontsize=10.5)
    foot(fig,"区间包含 0：尚不能确认 D 的成功率更高；也不能据此认定两组等价或模型没有记忆。",.025,9.8)
    save(fig,"h3_difference")


def h4_gamma():
    h=EST["hypotheses"]["H4"];g=h["gamma"];lo,hi=h["gamma_ci"]
    fig,ax=plt.subplots(figsize=(7,3))
    fig.subplots_adjust(left=.10,right=.96,bottom=.30,top=.70)
    fig.suptitle("H4：当前拟合不支持 k_min 与 H 成正比",fontsize=13,y=.97)
    ax.axvline(1,color=C,ls="--",lw=1.8)
    ax.errorbar(g,0,xerr=[[g-lo],[hi-g]],fmt="o",color=D,markersize=7,capsize=5,lw=2)
    ax.text(1,.46,"比例假设\nγ = 1",ha="center",va="center",color=C,fontsize=11,bbox=dict(facecolor="white",edgecolor="none",pad=2))
    ax.text(g,.48,f"拟合 γ = {g:.3f}\n95% 区间 [{lo:.3f}, {hi:.3f}]",ha="center",fontsize=11,va="center",color=D)
    ax.set_xlim(0,4.7);ax.set_ylim(-.3,.82);ax.set_yticks([])
    ax.set_xlabel("γ：log(k_min) 对 log(H) 的斜率")
    ax.spines["left"].set_visible(False);ax.grid(axis="x",color="#E5EAF0");ax.set_axisbelow(True)
    foot(fig,"成正比要求 γ = 1；当前区间整体大于 1，表示拟合关系比正比增长更快。",.09,10)
    foot(fig,"结论限定于控制组 50 个目标及预设 Weibull 区间删失模型；横线为人员 bootstrap 95% 区间。",.022,9.5)
    save(fig,"h4_gamma")


def h5_peak():
    rows=EST["curves"]["pooled"][1:]
    vals=np.array([r["tau"] for r in rows])*100
    ci=np.array([r["tau_ci"] for r in rows])*100
    fig,ax=plt.subplots(figsize=(7,3.4))
    fig.subplots_adjust(left=.11,right=.985,bottom=.28,top=.71)
    fig.suptitle("H5（探索性）：观察到的峰值不足以确定最佳 k",fontsize=13,y=.975)
    axes_grid(ax,POS)
    ax.axhline(0,color=MUTED,ls="--",lw=1)
    ax.plot(range(13),vals,color=D,lw=1.6)
    interval(ax,range(13),vals,ci,D,zorder=3)
    peaks=EST["hypotheses"]["H5"]["observed_maximizers"]
    for k in peaks:
        x=POS.index(k);ax.scatter([x],[vals[x]],s=55,marker="D",color=C,zorder=5)
        ax.text(x,vals[x]-2.8,f"k={k}",ha="center",fontsize=9.5,color=C)
    # Separate k-location envelope above the plotting area, never on the tau scale.
    left,right=EST["hypotheses"]["H5"]["argmax_envelope_ci"]
    x0,x1=POS.index(int(left)),POS.index(int(right))
    trans=ax.get_xaxis_transform()
    ax.plot([x0,x0,x1,x1],[1.06,1.12,1.12,1.06],transform=trans,color=TEAL,lw=1.6,clip_on=False)
    ax.text((x0+x1)/2,1.14,"峰位置的 95% bootstrap 包络：k ∈ [4, 48]",transform=trans,
            ha="center",va="bottom",fontsize=9.4,color=TEAL)
    ax.set_ylim(min(-20,np.floor(ci[:,0].min()/5)*5),15);ax.set_ylabel("D − C 差值 τ（百分点）")
    ax.set_xlabel("k（正容量；按实验网格等距排列）")
    foot(fig,"橙色菱形：k=4 和 12 并列最高，均为 +2.67 个百分点；竖线：τ 的逐点 95% 区间。",.075,9.6)
    foot(fig,"绿色括号描述峰可能出现的 k 位置，和纵轴差值的区间含义不同；不能确认稳定的内部峰。",.018,9.6)
    save(fig,"h5_peak")


def validate_sources():
    issues=[]
    rates=read_csv("extraction_rates_and_counts_full.csv")
    for r in rates:
        est=next(v for v in EST["curves"][r["scope"]] if v["k"]==int(r["k"]))[r["arm"]]
        for key,ck in [("estimate","exact_match_rate"),("successes","exact_match_successes"),("n_attempts","n_attempts")]:
            if abs(float(est[key])-float(r[ck]))>1e-10:issues.append(f"rate disagreement: {r['scope']} {r['k']} {r['arm']} {key}")
        for key,value in zip(["ci_lower","ci_upper"],est["ci"]):
            if abs(float(r[key])-value)>1e-10:issues.append(f"interval disagreement: {r['scope']} {r['k']} {r['arm']} {key}")
    targets_rows=read_csv("target_success_by_k_full.csv")
    counts=read_csv("extraction_counts_by_field_full.csv")
    for r in counts:
        subset=[t for t in targets_rows if (t["arm"],t["field"],t["k"])==(r["arm"],r["field"],r["k"])]
        assert len(subset)==25 and all(int(t["n_seeds"])==3 for t in subset)
        if sum(int(t["successes_out_of_3"]) for t in subset)!=int(r["successful_attempts"]):issues.append(f"target sum disagreement: {r}")
        if int(r["attempts"])!=75:issues.append(f"unexpected denominator: {r}")
    if issues:raise ValueError(issues)
    return issues


if __name__=="__main__":
    issues=validate_sources()
    workflow();rates_full();counts_full();targets("ssn");targets("email")
    balance();h1_floor();h2_floor();h3_difference();h4_gamma();h5_peak()
    manifest={
        "source":str(RESULTS.relative_to(ROOT)),
        "source_pointer":"reanalysis.estimates",
        "results_sha256":hashlib.sha256(RESULTS.read_bytes()).hexdigest(),
        "files":GENERATED,"data_disagreements":issues,
        "notes":["Existing intervals only; no bootstrap rerun.",
                 "Positive k displayed at equally spaced grid positions, not a linear numeric axis.",
                 "Zero-capacity anchor isolated; no line from k=0 into the sweep.",
                 "Per-target counts retain observed nonmonotonic outcomes.",
                 "H2 interval method changes between k=1–3 and k=4.",
                 "H5 peak-location envelope shown separately from tau confidence intervals."]}
    (OUT/"figure_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"figure_count":len(GENERATED)//2,"output_directory":str(OUT),"data_disagreements":issues},ensure_ascii=False))
