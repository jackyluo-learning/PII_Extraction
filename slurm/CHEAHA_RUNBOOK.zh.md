# Cheaha 操作手册 —— 研究 `capacity_axis_20260902`

_写给第一次用集群的人。英文版见 [`CHEAHA_RUNBOOK.md`](./CHEAHA_RUNBOOK.md)。_

**主机名已确认**：`cheaha.rc.uab.edu`（2026-09-03 实测解析并完成 SSH 握手）。仍待确认的是**作业是否需要 `--account=` 分配串**。其余内容都对着本仓库的脚本核过。

---

## 0 · 先建立心智模型

集群不是一台更大的笔记本，它是**两台不同的机器**：

| | 登录节点 | 计算节点 |
|---|---|---|
| 怎么到 | `ssh` | `sbatch` / `srun`，**永远不直接进** |
| 有网 | **有** | **常常没有** |
| 有 GPU | **没有** | 有 |
| 谁在共用 | 此刻所有人 | 只有你的作业 |
| 该在这里做什么 | `git`、`pip install`、编辑、`squeue` | 训练、攻击——任何要算的东西 |

**唯一的铁律：不要在登录节点算东西。** `ssh` 进去直接 `python train.py` 是最典型的新手动作——慢、没 GPU，而且会拖垮大家用来提交作业的那台机器。管理员看得见。

---

## 1 · 登录

```bash
ssh jluo@cheaha.rc.uab.edu
```

**新账号第一次登录建议先走浏览器界面（Open OnDemand）**，带文件浏览器和终端，地址在 Quick Start 链接里。它能一次确认两件事：凭据对不对、home 目录有没有初始化好。

### 如果 SSH 输完密码就 `Connection closed`

这**不是**网络或地址问题——握手已经成功了。密码错的话会回 `Permission denied` 并重新提示；**认证之后直接断开**是另一类问题。先诊断：

```bash
ssh -vvv jluo@cheaha.rc.uab.edu 2>&1 | tail -40
```

| 尾部输出 | 结论 |
|---|---|
| `Authentications that can continue: publickey,keyboard-interactive` 后断开 | 需要第二因素（Duo） |
| 认证成功后紧接着 `Connection closed` | 账号 / shell 未配好——先走网页门户初始化 |
| 反复 `Permission denied` | 密码不对，试校园 BlazerID 密码（开通邮件里并没有给独立密码） |

校外可能还需要 VPN。走不通就找 **support@listserv.uab.edu**（附上 `ssh -vvv` 的尾部输出），或**周一/周四 上午 10–12 点的 Zoom 办公时间**——第一次配环境，后者最快。

---

## 2 · 文件放哪 —— **第一个真正的坑**

你的账号有三个位置，**它们不能互换**：

| 路径 | 容量 | 生命周期 | 用来放 |
|---|---|---|---|
| `/home/jluo` | 与 `$USER_DATA` 共享 5 TB | 永久 | dotfiles、小配置 |
| **`/data/user/jluo`** | 5 TB | **永久** | **本仓库、语料、checkpoint、parquet 证据** |
| `/scratch/jluo` | 100 TB | **30 天未访问即删除** | 只放大块的临时中间文件 |

> **这个研究绝对不能放 `/scratch`。** 扫描跑完之后，parquet 分片会一直躺着不动，而你在写分析——「30 天未访问」正好是删除规则命中的情形。证据没了你也不会收到通知，直到你去看的那一刻。投稿是 2026-09-29，这个时间差是真实存在的。

```bash
cd /data/user/jluo
git clone https://github.com/jackyluo-learning/PII_Extraction.git
cd PII_Extraction
git checkout exp/e2-e5          # 八个 phase-0 闸门在这个分支上，不在 main
git log --oneline -3            # 应该看到 2517860 / 4739e24 / 77b6739
```

---

## 3 · 装环境 —— 在**登录节点**上

这一步需要联网，而计算节点通常没网。仓库把它单独拆出来就是这个原因。

```bash
cd /data/user/jluo/PII_Extraction
module load Python/3.11.5-GCCcore-13.2.0     # 确认过：Cheaha 上有这个模块
python3 --version                            # 应为 3.11.5
bash slurm/setup_env.sh
```

**必须写明版本号。** `module avail python` 里的默认项 `(D)` 是 **3.13.1**，直接 `module load Python` 会拿到它——3.13 在 torch / spacy / lifelines 这套科学栈上的 wheel 覆盖最没把握。3.11 是覆盖最稳的。系统自带的 `/usr/bin/python3` 是 **3.6.8**，torch 2.x 装不上，`setup_env.sh` 现在会直接拒绝而不是往下跑出一串看不懂的报错。

> **同一个模块在作业里也要加载。** SLURM 不继承你登录 shell 的 module 环境，而 `.venv/bin/python` 是指向模块目录的符号链接——不加载的话作业会死在一个断掉的解释器上。所有 `slurm/*.slurm` 都已经内置了这一步，默认就是 `Python/3.11.5-GCCcore-13.2.0`；换版本用 `export PII_MODULES="..."` 覆盖。

它会建 `.venv`、装 `requirements.txt`（含精确锁定的 `lifelines==0.30.0`）、把基座模型预取到项目内的 `.hf_cache`，并生成语料。

**如果 Python 是通过 module 提供的**，先把脚本顶部的 `module load python/3.11` 那行取消注释。`module avail python` 能列出集群上有哪些版本。

**跑完确认语料是干净的**——C4 停机和 Faker 不相交断言都在这一步触发，真有问题它会直接报错停下，但还是确认一下：

```bash
source .venv/bin/activate
python -c "import json; print(json.load(open('data/corpus_metadata.json'))['public_passages']['source_counts'])"
```

`c4` 必须不存在或为 `0`。如果 C4 有贡献，语料里可能混入了真实 PII —— **重新生成，不要往下走**。

---

## 4 · 重训 gpt2-124M —— 作为**作业**提交，不在登录节点跑

```bash
sbatch --partition=amperenodes --gres=gpu:1 --cpus-per-task=8 --mem=64G \
       --time=01:00:00 --job-name=pii-train \
       --wrap="cd /data/user/jluo/PII_Extraction && source .venv/bin/activate && \
               PII_DEVICE_PROFILE=auto python train.py --model gpt2"
```

`sbatch` 会打印一个 job id，后面所有查看和取消都用它。

---

## 5 · 提交扫描 —— 42 个分片作为一个 job array

**job array** 是一次提交变成很多个互相独立的任务。`exp_capacity.slurm` 本来就会从 `SLURM_ARRAY_TASK_ID` 解出 `(model, seed, k)`，所以整个扫描是一条命令。

本研究的网格——一个模型、三个 seed、十四个 `k`（含 `k=0` 锚点）：

```bash
cd /data/user/jluo/PII_Extraction
export PII_MODELS=gpt2
export PII_SEEDS="42 1337 2024"
export PII_KGRID="0 1 2 3 4 6 8 12 16 20 24 32 48 64"
export PII_GCG_ITERS=200
export PII_CAP_SWEEP_N=25
export PII_FIELDS=ssn,email
export PII_RUN_ID=e3a
source slurm/sweep_config.sh
echo "$NE3SHARDS 个分片"        # 必须打印 42
```

**提交要按 walltime 拆成两批。** `exp_capacity.slurm` 请求的是 `--time=11:45:00`，**正好是 `amperenodes` 的硬上限，零余量**；而大 `k` 的分片最贵，我的成本估计又是下界不是上界。所以把它们送去 `amperenodes-medium`（48 小时）：

```bash
# 任务号排列：先 model，再 seed，最后 k，即 id = (si * NK) + ki
# NK=14，k=32,48,64 位于 ki=11,12,13 —— 也就是每个 seed 区块的最后三个
sbatch --array=0-10,14-24,28-38   slurm/exp_capacity.slurm                              # 中小 k
sbatch --array=11-13,25-27,39-41  --partition=amperenodes-medium --time=24:00:00 \
                                  slurm/exp_capacity.slurm                              # k=32,48,64
```

如果集群要求分配串，两条都加 `--account=<你的>`，或者 `export ACCOUNT=<你的>`——仓库的提交脚本已经支持透传。

---

## 6 · 看着它跑

```bash
squeue -u jluo                       # 排队中和运行中的
squeue -u jluo -t RUNNING            # 只看运行中的
sacct -j <jobid> --format=JobID,State,Elapsed,MaxRSS,ExitCode    # 历史，含已结束的
seff <jobid>                         # 结束后看效率 —— 到底用上 GPU 了没
scancel <jobid>                      # 杀掉整个作业
scancel <jobid>_7                    # 只杀数组里的第 7 个任务
tail -f slurm/logs/pii-expcap-<jobid>_0.out
```

状态是 `PENDING`、原因写 `Resources` 或 `Priority` 是**正常**的——你在排队。第一个分片跑完用 `seff` 看一下，就知道后面的 walltime 申请合不合理。

---

## 7 · 读闸门，再谈数据

**`α_0` 是 sanity 门。在读任何其他分片的数字之前先读它。**

```bash
source .venv/bin/activate
python - <<'PY'
import glob, json, pandas as pd, run_manifest
a0 = pd.concat([pd.read_parquet(p) for p in glob.glob("results/attempts/e3a__*_k0.parquet")])
c = a0[a0.target_membership == "control"]
print(f"alpha_0 = {c.exact_match.mean():.4f}  n={len(c)}   <-- 必须 ~0")

for p in sorted(glob.glob("results/manifests/e3a__*.json")):
    d = json.load(open(p))
    print(f"  k={str(d['shard']['capacity_k']):<3} arms={d['arm_sizes']} "
          f"tiers={d['tier_composition']} subset={d['target_subset_hash']}")
print(run_manifest.compare(sorted(glob.glob("results/manifests/e3a__*.json"))))
PY
```

三件事必须成立，**每一条都是停机而不是警告**：

* **`alpha_0` ≈ 0** —— 否则说明零容量下 `exact_match` 就会命中，上面每一个 `k` 都带着同一个偏移。
* **`tier_composition` 里有 `20`** —— 否则说明分层抽样的闸门没生效，训练臂缺了记忆最深的那一层。
* **`compare()` 返回 `ok: True`** —— 否则说明各分片攻击的不是同一批人，跨 `k` 的配对设计已经没了。**不要「只用一致的那些分片」**，那是看过数据之后再挑子集。

---

## 8 · 把证据取回来

很小，几 MB。**在你自己的笔记本上跑**，不是在 Cheaha 上：

```bash
rsync -av jluo@cheaha.rc.uab.edu:/data/user/jluo/PII_Extraction/results/attempts/ results/attempts/
rsync -av jluo@cheaha.rc.uab.edu:/data/user/jluo/PII_Extraction/results/manifests/ results/manifests/
```

checkpoint 和语料留在 Cheaha 上。

---

## 命令速查

| 想做什么 | 命令 |
|---|---|
| 提交一个脚本 | `sbatch script.slurm` |
| 提交一条命令 | `sbatch --wrap="..."` |
| 提交一个数组 | `sbatch --array=0-41 script.slurm` |
| 看我的作业 | `squeue -u jluo` |
| 看已结束的作业 | `sacct -j <id>` |
| 有没有真用上 GPU | `seff <id>` |
| 杀掉 | `scancel <id>` |
| 交互式 GPU shell（只用于调试） | `srun --partition=amperenodes --gres=gpu:1 --time=01:00:00 --pty bash` |
| 有哪些分区 | `sinfo -s` |

## 本研究用到的分区

| 分区 | GPU | walltime 上限 | 用途 |
|---|---|---|---|
| `amperenodes` | A100 80 GB | 11:45 | 多数分片 |
| `amperenodes-medium` | A100 80 GB | 48:00 | `k = 32, 48, 64` |
| `express` | 无 | 00:30 | 出表、聚合 |

---

## 装环境时最可能卡住的地方

| 症状 | 多半是 | 怎么办 |
|---|---|---|
| `python: command not found` | 集群用 module 管 Python | `module avail python`，然后取消 `setup_env.sh` 顶部 `module load` 的注释 |
| `pip install` 卡死或超时 | 在计算节点上跑了（没网） | 回登录节点跑 |
| torch 装成 CPU 版 | 默认 wheel | 按 `setup_env.sh` 注释里那行装 cu121 的 |
| 语料生成报 `PublicDataUnavailableError` | **C4 被触发了** | 这是**设计如此**。等 Wikipedia 可达再跑，或调小 `PII_N_PUBLIC` |
| 语料生成报 SSN/email 碰撞 | Faker 两个池子撞了 | 也是**设计如此**，改 `data_cfg.seed` 重来 |
| 磁盘写满 | 写到 `$HOME` 了 | 确认在 `/data/user/jluo` 下 |

前两条是环境问题；**后两条是断言在正常工作**，不要绕过去。
