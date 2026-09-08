"""Build a Chinese briefing from the authoritative, already computed E3 ledger.

Run briefing_figures.py first. This is a document export, not a statistical rerun.
The original analysis, preregistration and run ledger are never modified here.
"""
from pathlib import Path
import csv
import hashlib
import html
import json
import os
import re

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[3]
DATA = STUDY / 'reanalysis'
FIG = ROOT / 'artifacts/capacity_axis_20260902/figures/briefing'
OUT = ROOT / 'output/pdf'
OUT.mkdir(parents=True, exist_ok=True)
PDF = OUT / 'E3_实验结果汇报.pdf'
MD = STUDY / 'briefing.md'
ledger = json.loads((STUDY / 'results.json').read_text())
E = ledger['reanalysis']['estimates']
H = E['hypotheses']
curves = {s: {int(r['k']): r for r in rows} for s, rows in E['curves'].items()}
ks = list(curves['pooled'])


def read_csv(name):
    with (DATA / name).open() as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_sources():
    """Cross-check every displayed rate/count cell and the 42 source hashes."""
    ids = set(E['analysis_run_ids'])
    runs = [r for r in ledger['runs'] if r['run_id'] in ids]
    assert len(runs) == len(ids) == 42
    raw_paths = []
    for r in runs:
        assert r['run_status'] == 'completed' and not r.get('excluded', False)
        for a in r['artifacts']:
            if a['path'].endswith('.parquet'):
                p = ROOT / a['path']
                assert sha(p) == a['sha256'], p
                raw_paths.append(str(p.relative_to(ROOT)))
    assert len(raw_paths) == 42
    for r in read_csv('extraction_rates_and_counts_full.csv'):
        ref = curves[r['scope']][int(r['k'])][r['arm']]
        for key, dest in [('exact_match_rate', 'estimate'), ('ci_lower', None), ('ci_upper', None)]:
            value = ref[dest] if dest else ref['ci'][0 if key == 'ci_lower' else 1]
            assert abs(float(r[key]) - value) < 1e-12
        assert int(r['exact_match_successes']) == ref['successes']
    cells = read_csv('target_success_by_k_full.csv')
    assert len(cells) == 1400 and len({(r['target_id'], r['k']) for r in cells}) == 1400
    for field in ['ssn', 'email']:
        for arm in ['trained', 'control']:
            for k in ks:
                subset = [r for r in cells if r['field'] == field and r['arm'] == arm and int(r['k']) == k]
                assert len(subset) == 25
                assert sum(int(r['successes_out_of_3']) for r in subset) == curves[field][k][arm]['successes']
    for r in read_csv('extraction_counts_by_field_full.csv'):
        ref = curves[r['field']][int(r['k'])][r['arm']]
        assert int(r['successful_attempts']) == ref['successes']
    return raw_paths


raw_paths = check_sources()
pdfmetrics.registerFont(TTFont('CN', '/Library/Fonts/Arial Unicode.ttf'))
pdfmetrics.registerFont(TTFont('CNB', '/System/Library/Fonts/STHeiti Medium.ttc'))
pdfmetrics.registerFontFamily('CN', normal='CN', bold='CNB', italic='CN', boldItalic='CNB')
W, HH = landscape(A4)
NAVY = '#18324B'
TEAL = '#167C80'
BLUE = '#2767A8'
ORANGE = '#D8792A'
GRAY = '#536578'
LIGHT = '#EAF4F4'
c = canvas.Canvas(str(PDF), pagesize=(W, HH), pageCompression=1)
c.setTitle('E3 实验结果汇报：D/C完整曲线、匹配诊断与H1-H5')
c.setAuthor('PII Extraction Research')
c.setSubject('基于已保存主扫描数据的条件性结果；中文图解汇报')
markdown = ['# E3 实验结果汇报\n\nD/C 完整曲线、字段与靶标图、匹配诊断及 H1-H5\n\n整理日期：2026-09-07。数据版本：当前证据台账中的纠错重分析。\n']
page_no = 0
layout_records = []


def plain(t):
    return html.unescape(re.sub('<[^>]+>', '', t)).replace('\n', ' ')


def md_text(t):
    return html.unescape(t.replace('<b>', '**').replace('</b>', '**').replace('<br/>', '\n'))


def paragraph(t, x, top, width, size=11.6, leading=None, color=NAVY, record=True):
    style = ParagraphStyle('body', fontName='CN', fontSize=size, leading=leading or size*1.48,
                           textColor=colors.HexColor(color), wordWrap='CJK', splitLongWords=True)
    p = Paragraph(t, style)
    _, height = p.wrap(width, 1000)
    if top + height > HH - 39:
        raise ValueError(f'Page {page_no}: paragraph overflows: {plain(t)[:65]} ({top+height:.1f})')
    p.drawOn(c, x, HH-top-height)
    layout_records.append({'page': page_no, 'kind': 'paragraph', 'bottom': top+height, 'text': plain(t)[:70]})
    if record:
        markdown.append(md_text(t) + '\n')
    return top + height


def start(title, takeaway, group):
    global page_no
    if page_no:
        c.showPage()
    page_no += 1
    c.setFillColor(colors.HexColor(TEAL)); c.rect(35, HH-43, 28, 4, fill=1, stroke=0)
    c.setFont('CN', 9.2); c.setFillColor(colors.HexColor(GRAY))
    c.drawString(73, HH-43, f'E3 研究汇报  /  {group}')
    c.setFont('CNB', 22); c.setFillColor(colors.HexColor(NAVY))
    c.drawString(35, HH-78, title)
    c.setFillColor(colors.HexColor(LIGHT)); c.roundRect(35, HH-118, W-70, 29, 5, fill=1, stroke=0)
    paragraph(takeaway, 46, 94, W-92, size=11.5, leading=17, record=False)
    c.setStrokeColor(colors.HexColor('#DCE4EA')); c.line(35, 31, W-35, 31)
    c.setFont('CN', 8.3); c.setFillColor(colors.HexColor(GRAY))
    c.drawString(35, 18, 'E3 / GPT-2 124M / 已保存数据的条件性结果 / 2026-09-07')
    c.drawRightString(W-35, 18, f'{page_no:02d}')
    c.bookmarkPage(f'p{page_no}'); c.addOutlineEntry(title, f'p{page_no}', level=0)
    markdown.append(f'\n## {title}\n\n**{takeaway}**\n')


def figure(name, x, top, width, maxheight, caption=None):
    p = FIG / name
    iw, ih = Image.open(p).size
    height = width * ih / iw
    if height > maxheight:
        width *= maxheight / height
        height = maxheight
    c.drawImage(str(p), x, HH-top-height, width=width, height=height, mask='auto')
    markdown.append(f'![{caption or name}]({os.path.relpath(p, MD.parent)})\n')
    layout_records.append({'page': page_no, 'kind': 'figure', 'bottom': top+height, 'file': name})
    return top + height


def table(headers, rows, x, top, widths, size=10.1, row_height=None):
    style = ParagraphStyle('cell', fontName='CN', fontSize=size, leading=size*1.34,
                           textColor=colors.HexColor(NAVY), wordWrap='CJK')
    data = [[Paragraph(str(v), style) for v in row] for row in [headers] + rows]
    t = Table(data, colWidths=widths, rowHeights=row_height)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7EFF5')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F8FA')]),
        ('VALIGN',(0,0),(-1,-1),'TOP'), ('LEFTPADDING',(0,0),(-1,-1),7),
        ('RIGHTPADDING',(0,0),(-1,-1),7), ('TOPPADDING',(0,0),(-1,-1),5),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),
        ('LINEBELOW',(0,0),(-1,0),0.6,colors.HexColor('#CBD8E1')),
    ]))
    _, height = t.wrap(sum(widths), 1000)
    if top+height > HH-39: raise ValueError(f'Page {page_no}: table overflows ({top+height:.1f})')
    t.drawOn(c, x, HH-top-height)
    markdown.append('| '+' | '.join(map(plain,headers))+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+
                    '\n'.join('| '+' | '.join(map(lambda z:plain(str(z)).replace('|','\\|'),row))+' |' for row in rows)+'\n')
    layout_records.append({'page': page_no, 'kind': 'table', 'bottom': top+height})
    return top+height


def note(t, top, x=35, width=None):
    return paragraph(t, x, top, width or W-70, size=9.5, leading=14, color=GRAY)


def pct(v): return f'{100*v:.2f}%'
def interval(v): return f'[{100*v[0]:.2f}, {100*v[1]:.2f}]'
def rate(v): return f"{pct(v['estimate'])} {interval(v['ci'])}"
def diff(r): return f"{100*r['tau']:+.2f} [{100*r['tau_ci'][0]:+.2f}, {100*r['tau_ci'][1]:+.2f}]"
def kvals(values): return '无' if not values else '、'.join(map(str, values))
body_left, body_right = 35, 528
leftw, rightw = 473, W-563

# 1. Set up the experiment, with a concrete D/C distinction.
start('实验怎样比较 D 与 C？', '先用含 D 的语料微调，再冻结同一个模型，分别尝试生成 D 和 C。', '实验流程')
figure('workflow.png',35,133,W-70,217,'D/C实验流程示意；不是实验数据图')
y=355
y=paragraph('<b>D：微调中出现过的目标；C：从本次微调语料中排除的目标。</b>例如 D 是 alice17@example.org，C 是 bruce24@example.org：都是邮箱，具体字符串不同；前者进入微调语料，后者没有。此例仅为说明，非实验原始记录。',35,y,W-70)
y=paragraph('<b>攻击时改变什么？</b>本次GCG攻击利用梯度搜索提示中可修改的token（文本片段），优化器知道要生成的目标。k是可修改位置的数量；模型权重保持冻结。命中C表示未参与本次微调的目标也可能被强制生成。',35,y+10,W-70)
note('本次主扫描：一个 GPT-2 124M 微调模型；每组25人，每人SSN（社会安全号码格式）和email两个合成字段，共50靶标/组。三个seed是三次不同随机初始化的攻击，不是三次独立训练。C的“未训练”只指本次微调。',y+66)

# 2. All rates, including the fixed anchor.
start('完整 D/C 抽取率：总体与两个字段', '随着 k 增大，两组抽取率都升高；判断成员差异还要比较 D 与 C 的距离。', '完整描述图 1 / 4')
figure('rates_full.png',35,134,W-70,300,'全14个k的D/C抽取率与95%点区间；字段拆分为探索性')
y=paragraph('<b>读图：</b>蓝色是D，橙色是C。α（forcing floor）就是C的抽取率；τ是D抽取率减C抽取率，单位为“百分点”。例如82.00%−80.67%=+1.33个百分点。',35,438,W-70)
note('每个总体点为150次攻击/组（25人×2字段×3seed）；每个字段点为75次攻击/组。误差线是95%点区间，表示估计的不确定性，不是95%的攻击结果落在其中；各点区间不构成整条曲线的同时保证。',y+9)
note('成功沿用实验的exact_match规则：规范化后，完整目标值出现在生成文本中；不要求整段输出只含目标。k=0是单独的固定提示基线，提示/优化目标形式与GCG不同。横轴等距排列，不代表k的数值差。',y+44)

# 3. All counts.
start('按字段拆开的完整抽取计数', '每格读作“75次攻击中成功了几次”；它不是成功人数。', '完整描述图 2 / 4')
figure('counts_full.png',35,139,W-70,250,'D/C × SSN/email × 全14个k的成功攻击次数；探索性描述')
r20=curves['pooled'][20]
y=paragraph('<b>实际例子：k=20。</b>SSN中D成功48/75次，C成功46/75次；email中两组均成功75/75次。合并后D为123/150，C为121/150，正好得到82.00%与80.67%。',35,405,W-70)
y=paragraph('<b>为什么不能称作75个样本？</b>同一个人、同一个字段被攻击了三次，这三次相关。同一人还有两个字段。因此统计区间按人员重采样，不能把重复攻击当成新增人员。',35,y+12,W-70)
note('本图保留全14个k、全部4个组别/字段组合，共56格；无插值、无筛选。整数计数本身不带误差线，抽取率的区间见上一页。唯一靶标的成功次数与重复稳定性见接下来的两页。',y+46)

# 4 and 5. All target rows, with equal sizing and consistent colors.
for field,label in [('ssn','SSN'),('email','email')]:
    start(f'逐靶标成功情况：{label} 完整版', '一行是一个匿名靶标，一列是一个 k；0、1、2、3 表示三个 seed 中的成功次数。', f'完整描述图 {3 if field=="ssn" else 4} / 4')
    figure(f'targets_{field}.png',35,131,W-70,359,f'{label}完整D/C靶标矩阵；每组25行、每行14个k；探索性描述')
    note('颜色越深表示三次尝试中成功越多；3表示本次三个seed全成功，并不保证未来必成功。D01和C01是不同组的匿名编号，不表示它们构成E17匹配对。',497)
    note('每个面板包含全部25个靶标；排序仅用于阅读。保留“成功后在更大k失败”的格子；未将首次成功之后全部补成成功。k=0仍为单独基线。',528)

# 6. Complete numeric curve.
start('完整曲线数值表', '括号内是95%区间；差值为百分点。D、C两组与全部14个k均保留。', '可直接核对的数据')
rows=[]
for k in ks:
    r=curves['pooled'][k]
    method='边界法' if k<=3 else '人员重采样'
    rows.append([str(k),rate(r['trained']),rate(r['control']),diff(r),method,
                 f"{r['control']['attempt_elapsed_hours']:.3f} / {r['trained']['attempt_elapsed_hours']:.3f}"])
y=table(['k','D 抽取率；区间(%)','C 抽取率；区间(%)','D−C；区间(百分点)','区间方法','攻击小时 C / D'], rows,35,135,[29,159,159,176,93,155.89],size=9.4)
note('每行每组：25人、50靶标、150次攻击、3个seed。人员重采样：10,000次bootstrap；边界法：零命中时使用Wilson有效样本量区间，差值使用Newcombe/MOVER。有效样本量为50/1.5≈33.33，不乘三个seed。',y+11)
note('耗时是攻击调用时间，不等于GPU计费时间。全部主扫描攻击调用合计26.25小时；42个最终分片对应的调度计费下限为222.269 GPU小时。',y+44)

# 7. Explain matching, then show all six diagnostic rows.
start('D/C匹配平衡诊断', '不属于 H1-H5 的统计检验；它检查两组在训练经历之外是否足够相似。', '比较是否公平')
y=paragraph('<b>E17做什么？</b>从未训练目标池中，为D选择同一字段、长度和参考难度尽量接近的C。匹配不要求字符串相同；匹配记录也不保证最终入选的两组已经平衡。这里检查的是实际攻击目标。',35,136,W-70)
figure('balance.png',35,y+8,431,216,'实际攻击目标的六项SMD及95%bootstrap区间；阴影为±0.1诊断带')
bal=E['diagnostics']['actual_marginal_balance']
br=[]
names={'char_len':'字符数','target_len_tokens':'token数','target_H_bits':'H 信息量'}
for r in bal:
    br.append([r['field'],names[r['covariate']],f"{r['smd']:.3f}",f"[{r['ci'][0]:.3f}, {r['ci'][1]:.3f}]",'是' if abs(r['smd'])<.1 else '否'])
table(['字段','比较变量','SMD','95%区间','达标'],br,478,y+13,[53,66,51,118,40],size=9.4)
y=paragraph('<b>变量如何理解？</b>字符数是字符串有多少个字符；token数是分词器把它切成多少块；H是参考模型认为这个字符串有多“意外”的信息量（bits），越大表示参考模型赋予它的概率越低，不是直接测得的攻击难度。',35,419,W-70,size=11.2)
y=paragraph('<b>诊断结果：</b>SMD=(D均值−C均值)/合并标准差，越接近0越相似。SSN三项点估计均满足预定 |SMD|&lt;0.1；email三项均未满足，且D邮箱平均更长、token更多、H更大。0.1是平衡诊断线，不是p值。',35,y+9,W-70,size=11.2)
note('每字段25人/组。email不平衡限制H2/H3/H5的成员性解释；当前表不能算出它造成多少抽取率差异。H4只使用C，不依赖D/C匹配差值。',y+10)

# 8. H1, self-contained hypothesis/results/implication.
start('H1：提示容量增加，C是否更容易被生成？', '当前数据支持总体上升趋势；局部点仍可能回落。', 'H1 / 趋势')
figure('h1_floor.png',35,144,473,237,'H1：控制组正容量曲线及三个攻击seed的变化；主线带95%点区间')
y=paragraph('<b>实验前假设</b><br/>零假设：C抽取率α与k无关，总体曲线为平。实验前预期：α随k单调不降。这里考察C，不是D−C。',528,140,rightw)
y=paragraph('<b>怎样判断</b><br/>用Spearman相关系数ρ衡量排序趋势，接近+1表示强上升。按人员重新抽样并重复计算，所得95%区间完全大于0才通过。这个判据不能证明逐点单调。',528,y+12,rightw)
hh=H['H1']
paragraph(f'<b>结果</b><br/>ρ={hh["rho"]:.4f}<br/>95%区间 [{hh["ci"][0]:.4f}, {hh["ci"][1]:.4f}]<br/>每组25人中的C组、50目标、3个攻击seed。',528,y+12,rightw)
y=paragraph('<b>是否符合预期？</b>符合总体上升判据。例如C在k=20为80.67%，到k=64为96.67%；但k=32到48由92.00%降至91.33%。因此不能说每增加一个k都更高，更不能把总体趋势当成每个靶标必然单调。',35,398,W-70)
y=paragraph('<b>对论文的意义与下一步：</b>未参与微调的目标也会随攻击容量增加而更常被命中，因此“抽取成功”本身不足以归因于训练记忆。跨模型、其他攻击器能否复现这一趋势，需要另做实验。',35,y+10,W-70)
note('原始p=0.000100；Holm调整p=0.000400。p衡量在零假设与计算模型成立时，出现当前或更极端统计结果的程度；它不是假设为真的概率。Holm用于控制H1-H4一起检验时的误报，四项并不因此成为同一个假设。',y+10)

# 9. H2 original floor question, including the interval-switch issue.
start('H2：有没有一个 k，让 C 成功率足够低？', '原始1%要求尚未分辨：观察到0次成功，也不能确认总体成功率不超过1%。', 'H2 / 先只看控制组')
figure('h2_floor.png',35,149,473,240,'低容量C成功率和95%区间；1%、5%、9%是允许上限，不是不同实验')
y=paragraph('<b>实验前假设</b><br/>存在某个k≥1，使控制组真实成功率α不超过1%。推广写法是α≤ε；ε表示允许的C成功率上限，例如1%、5%或9%。',528,139,rightw)
y=paragraph('<b>预定判据</b><br/>要求α的95%区间上界≤ε，不能只看观察成功率。在“命中即判断为训练成员”的规则下，C被误判的概率就是α。',528,y+12,rightw)
paragraph('<b>结果与判定</b><br/>k=1、2、3均为0/150次命中；但保守区间上界仍为10.33%，高于1%。因此未确认1%条件，也未证明它不可能成立。',528,y+12,rightw)
y=paragraph('<b>为什么图上k=4的上界反而较低？</b>它观察到2/150次成功（1.33%），主分析用人员bootstrap得到上界3.33%；零命中的k=1-3则换用保守Wilson区间，上界10.33%。这是区间方法切换的结果，不能解释成k=4比零命中的点更安全。',35,407,W-70)
y=paragraph('<b>对结果的影响：</b>k=4是否满足5%上限依赖区间方法。若也按同一Wilson约定计算，其上界为12.60%。所以“5%时有k=4”只能作为当前表的条件性候选，不能当作已验证的可靠操作点。',35,y+10,W-70)
note('设计预估约9%的分辨范围；按实际采用的保守区间，零命中上界为10.33%，两者不是同一个数。下一步需要预先统一区间方法和所需精度，再增加独立控制人员。',y+10)

# 10. H2 full tolerance map, replacing opaque headers with explicit conditions.
start('H2：低 C 成功率之外，D 是否明显更高？', '目前没有同时得到“C足够低”与“D明显高于C”支持的 k。', 'H2 / 再看成员区分')
mapping=H['H2']['mapping']
rows=[[pct(r['tolerance']),kvals(r['floor_only_capacities']),kvals(r['positive_tau_capacities'])] for r in mapping]
bottom=table(['允许的C上限 ε','仅要求C的95%上界≤ε：候选k','再要求D−C的95%下界>0：候选k'],rows,35,139,[87,259,149],size=10.1)
y=paragraph('<b>为什么加第二个条件？</b><br/>如果D和C都很少成功，虽然C低，攻击也不一定能区分训练成员。成员识别还需要D的成功率明显高于C。',553,141,W-588)
y=paragraph('<b>“明显高于”怎么读？</b><br/>对差值τ=D−C计算95%区间；整个区间在0右边（下界>0）才支持D更高。区间跨0则方向未分辨。',553,y+11,W-588)
y=paragraph('<b>与设计原文的关系</b><br/>原文只要求“差值区间不含0”，没有限定正向。按字面，在ε=100%时k=64也入选，但其D−C为−6.00个百分点，方向相反。表中第三列明确展示成员识别所需的正向条件。',553,y+11,W-588)
note('表中k是当前混合区间规则下的描述性映射；5%、9%、10%行出现k=4的原因见上一页。100%上限几乎放弃控制误报，k=64的负差值也不能作为正向成员信号。',max(bottom,y)+14)
note('最终判定：1%条件未分辨；没有得到支持的正向联合操作点。设计未规定跨所有k如何做一个整体检验（“全局检验”），故不能宣称已正式证明“任何k都不存在”。H2没有有效p值，旧表中1只是占位。',max(bottom,y)+47)

# 11. H3, one plot plus the full group/field comparison.
start('H3：在论文原有的 k=20，能分辨 D 与 C 吗？', 'D=82.00%，C=80.67%；差值+1.33个百分点，但不确定区间仍跨过0。', 'H3 / 固定主点')
figure('h3_difference.png',35,143,463,223,'k=20总体与字段D−C差值及95%区间；字段拆分为探索性')
y=paragraph('<b>实验前假设与意义</b><br/>固定k=20，检验总体差值是否为0（双侧）。这是论文已有主点的校准，检验扣除C的forcing floor后还剩多少差异；它不是寻找最优k。',528,140,rightw)
y=paragraph('<b>预定判据</b><br/>D−C的95%人员bootstrap区间排除0，才拒绝“总体差值为0”。本次区间为[−7.33,+10.00]个百分点，包含0。',528,y+10,rightw)
paragraph('<b>判定与新问题</b><br/>尚不能分辨成员差异，也不能证明两组等效或模型没有记忆。后续应先定义多大的差异才有实际意义，再安排足够人员检验。',528,y+10,rightw)
rows=[]
for f,label in [('pooled','总体'),('ssn','SSN（探索性）'),('email','email（探索性）')]:
    rr=curves[f][20]
    rows.append([label,f"25/{rr['control']['n_targets']}/3",rate(rr['trained']),rate(rr['control']),diff(rr)])
y=table(['范围','每组人/靶标/seed','D及95%区间(%)','C及95%区间(%)','D−C及95%区间(百分点)'],rows,35,389,[103,112,165,165,226.89],size=9.8)
note('同一主扫描；k=20攻击耗时C/D=0.782/0.766小时。原始p=0.825617，Holm p=1.000000。email全部观察命中仍有总体不确定性；字段差异不能被总体平均掩盖。',y+11)
note('三个seed的总体D/C分别为80%/78%、86%/86%、80%/78%（每个seed50次/组）。它们展示重复攻击波动，不增加独立人员数。',y+41)

# 12. H4 teaching page; every formula term has a definition.
start('H4：先把“成正比”说清楚', '假设是：目标信息量 H 翻倍，所需首次命中容量 k_min 也约翻倍。', 'H4 / 假设与公式')
y=paragraph('<b>实验前假设：k_min(t) ≈ H(t) / β。</b>H4只使用控制组C，希望用一个固定的β，把目标信息量转换成需要的提示容量。',35,138,W-70,size=13)
rows=[
 ['t','某一个具体目标字符串。'],
 ['H(t)','参考模型给目标t的自信息量，单位bits；目标越不被参考模型预期，H通常越大。'],
 ['k_min(t)','在本次正容量扫描中，三个固定攻击seed任一次首次成功时，最小的已观察k。'],
 ['β（beta）','比例模型中的换算常数，单位bits/token：每个自由提示token对应多少目标信息量。'],
]
y=table(['符号','含义'],rows,35,y+15,[116,655.89],size=11.1)
y=paragraph('<b>示意例子（不是实测数据）：</b>若β=10 bits/token，H=40 bits对应k_min≈4；H=80 bits对应k_min≈8。两者同时翻倍，这就是成正比。',35,y+16,W-70,size=12)
formula_top=y+16
y=paragraph('<b>为什么拟合里会出现斜率γ？</b>把比例公式两边取对数：<br/>log(k_min) ≈ log(H) − log(β)<br/>再允许数据自由决定斜率：log(k_min) = a + γ × log(H) + error。',35,formula_top,468,size=12)
right_bottom=paragraph('<b>新增符号的含义</b><br/>log：对数变换。<br/>a：直线截距。<br/>γ（gamma）：对数坐标上的斜率。<br/>error：H未解释的差异与攻击随机性。',530,formula_top,W-565,size=11.4)
note('比例关系要求γ=1，且此时a=−log(β)。如果γ不等于1，就不能再从截距a报告一个通用的bits/token换算常数。H是参考模型的描述量，不是经验证的确定性容量下界。',max(y,right_bottom)+13)

# 13. H4 actual result and limitations.
start('H4：数据是否支持这条比例关系？', 'γ的95%区间排除1；在当前工作模型下，简单比例关系不适合这些控制目标。', 'H4 / 结果与边界')
figure('h4_gamma.png',35,145,471,202,'H4斜率γ及95%人员bootstrap区间；比例模型要求γ=1')
y=paragraph('<b>斜率怎样算出来？</b><br/>对50个C目标，先记录每个目标的首次成功网格。例如在k=4失败、k=6首次成功，阈值工作模型将其记为(4,6]的区间信息。',528,138,rightw)
y=paragraph('用Weibull统计模型，寻找让这些区间观察最可能出现的参数（最大似然估计），得到γ。再按25名人员重抽样并重复拟合10,000次，得到95%区间。',528,y+12,rightw)
paragraph('<b>预定判据</b><br/>γ的95%区间排除1，反驳简单比例形式。这里检验γ是否为1，不是检验它是否为0。',528,y+12,rightw)
hh=H['H4']
y=paragraph(f'<b>结果：</b>γ={hh["gamma"]:.6f}，95%区间[{hh["gamma_ci"][0]:.6f}, {hh["gamma_ci"][1]:.6f}]；原始p=0.000100，Holm p=0.000400。区间整体高于1，未满足成正比的要求。',35,373,W-70,size=12)
y=paragraph('<b>这一判定有何限制？</b>控制组7/50个靶标在首次成功后，于某个更大的k又全部失败。也就是说，“失败→成功→失败”真实存在；首次命中不是确定的能力门槛，(4,6]只是阈值模型的解释。本次没有到64仍未命中的控制目标。',35,y+12,W-70)
y=paragraph('<b>对论文与下一步：</b>不能据此给出一个可迁移的通用β。需要进一步检查字段差异、攻击随机性和非线性关系；这些是新研究方向，不能把γ≈3.48当成已经建立的新普遍定律。',35,y+12,W-70)
note('“工作模型”是这次估计使用的统计近似，并非物理定律。本页沿用当前主分析的“三个seed首次任一命中”口径；Weibull工作分布及p算法为重分析中披露的实现约定，不能追溯称为事前固定。',y+9)

# 14. H5, with an explicit exploratory definition.
start('H5：D−C 的差值会在中间容量达到峰值吗？', 'k=4和12是当前并列最高点，但尚未定位一个稳定、可靠的最优容量。', 'H5 / 探索性')
figure('h5_peak.png',35,146,472,232,'H5探索性：D−C差值曲线及95%点区间，峰位置包络另行标示')
y=paragraph('<b>实验前假设</b><br/>预期差值τ随k先升后降，在1与64之间出现内部峰；对照是单调或平坦关系。H5研究D−C的峰，不是D或C自身成功率的峰。',528,138,rightw)
y=paragraph('<b>为什么叫探索性？</b><br/>实验前就判断当前人数不足以可靠识别峰形，因此H5只用于提出后续问题，不作为确认性发现，也不参加H1-H4的Holm校正。',528,y+12,rightw)
paragraph('<b>预定判断思路</b><br/>重复抽样看最高点落在哪里，其95%位置包络应避开两端；同时用弯曲方向检查是否确有“先升后降”。重分析保留所有并列最高点。',528,y+12,rightw)
hh=H['H5']
y=paragraph('<b>观察结果：</b>k=4、12并列+2.67个百分点，但各自差值区间均跨0。峰位置的95%包络为[4,48]，范围很宽；它表示最高点位置的不确定性，不表示此区间内所有k都好。',35,401,W-70)
y=paragraph(f'<b>是否符合假设？</b>位置条件在字面上通过。b是拟合曲线的弯曲系数，负值表示向下弯；本次b={hh["quadratic_logk_coefficient"]:.5f}，95%区间[{hh["quadratic_ci"][0]:.5f}, {hh["quadratic_ci"][1]:.5f}]含0，未支持明确的峰形。探索性单侧p={hh["quadratic_one_sided_p"]:.4f}，整体仍不确定。',35,y+10,W-70)
note('下一步：先规定峰值至少应高出两侧多少，再增加独立人员并加密候选容量。当前不能宣称k=4或12最优，也不能因证据不足就宣称曲线平坦。b仅是对log(k)拟合二次曲线的弯曲系数。',y+10)

# 15. Concise reporting scope and references, not another one-line H1-H5 summary.
start('如何使用这份汇报', '本文件完整呈现所选结果；数值重算已完成，研究的正式验收仍未通过。', '解释范围与数据出处')
y=paragraph('<b>目前可以汇报什么？</b>已保存的42个Cheaha主分片覆盖完整14个k与3个攻击seed，共4,200次攻击；本文件中的曲线、字段计数与逐靶标矩阵逐格对应。D/C比较来自同一模型、同一攻击流程下的不同目标组。',35,141,369)
y=paragraph('<b>为什么仍称“条件性结果”？</b>现有攻击数据可以复算，但仍缺当时执行模型的指纹与各分片的完整启动绑定，6个分片的历史代码清洁性未知；部分失败/重试归属及Colab历史时间也未补齐。email匹配未过关，H2跨k整体检验也未预先定义。',35,y+14,369)
y=paragraph('<b>哪些结论不能从这里推出？</b>不能把攻击命中直接叫作训练记忆；不能把未显著叫作两组相同；不能把一次首次成功叫作确定门槛；也不能把探索性的候选k作为部署选择。结论范围限于本次模型、两种合成字段及攻击预算。',35,y+14,369)
paragraph('<b>成本口径</b><br/>C攻击调用13.022小时；D为13.229小时。主分片调度计费合计至少222.269 GPU小时，包含调用之外的占用；两种计时不能混为一谈。',35,y+14,369,size=11.1)
y=paragraph('<b>数据与文档索引</b><br/>以下路径均相对本研究目录；Markdown版提供可点击链接。所有图沿用纠错重分析数值，没有新增模型实验。',445,141,W-480)
source_items=[
 ('完整分析与限制','analysis.md'),
 ('实验前假设与执行方案','design.md；protocol.md'),
 ('权威数值','results.json → reanalysis.estimates'),
 ('全部曲线与区间','reanalysis/curve_table.csv'),
 ('完整抽取率与计数','reanalysis/extraction_rates_and_counts_full.csv'),
 ('字段计数与唯一靶标数','reanalysis/extraction_counts_by_field_full.csv'),
 ('完整匿名靶标矩阵','reanalysis/target_success_by_k_full.csv'),
 ('实际攻击目标平衡','reanalysis/actual_balance.csv'),
 ('首次命中与模型输入','reanalysis/kmin_recomputed.csv'),
 ('复算方法与独立核对','reanalysis/method_choices.md；reanalysis/statistics_review.md'),
]
table(['可核对内容','文件'],source_items,445,y+13,[108,W-588],size=9.3)
note('本汇报保留总体曲线、字段/靶标描述、匹配诊断及H1-H5。字段拆分和H5均明确标注探索性；未把原先删除的连续评分分析重新加入。',531)

c.save()
markdown.append('\n### 可点击的来源链接\n')
for rel in ['analysis.md','design.md','protocol.md','results.json',
            'reanalysis/curve_table.csv','reanalysis/extraction_rates_and_counts_full.csv',
            'reanalysis/extraction_counts_by_field_full.csv','reanalysis/target_success_by_k_full.csv',
            'reanalysis/actual_balance.csv','reanalysis/kmin_recomputed.csv',
            'reanalysis/method_choices.md','reanalysis/statistics_review.md']:
    markdown.append(f'- [{rel}]({rel})')
markdown.append('\n\n[下载PDF汇报]('+os.path.relpath(PDF,MD.parent)+')\n')
MD.write_text('\n'.join(markdown))
inputs=[STUDY/'analysis.md',STUDY/'design.md',STUDY/'protocol.md',STUDY/'results.json']
inputs += [DATA/name for name in ['curve_table.csv','extraction_rates_and_counts_full.csv',
            'extraction_counts_by_field_full.csv','target_success_by_k_full.csv','actual_balance.csv']]
manifest={'description':'Document extraction and illustration; no new hypothesis tests or model runs.',
          'authority':'results.json/reanalysis/estimates', 'pages':page_no,
          'source_main_shards_sha256_checked':len(raw_paths),
          'target_k_cells_checked':1400, 'total_attack_records_represented':4200,
          'inputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in inputs],
          'outputs':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [MD,PDF]],
          'layout':layout_records}
(DATA/'briefing_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'pdf':str(PDF),'markdown':str(MD),'pages':page_no,'source_shards_verified':42},ensure_ascii=False))
