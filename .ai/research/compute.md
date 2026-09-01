# 计算环境

_实测于 2026-08-31。本机部分是探测出来的；两个远端环境是从 `slurm/` 作业脚本 + 用户确认得到的。_

## 三个环境及其分工

| 环境 | 角色 | 适合什么 |
|---|---|---|
| **Colab Pro / Pro+** | **主力**（用户当前优先） | 训练、短攻击、单个 E 实验 |
| **UAB Cheaha (SLURM)** | 长扫描 | E3 容量扫描、E7 预算匹配等需要 `afterok` 依赖链的多任务 |
| 本机 MacBook (M3 Max) | 写作与分析 | `make_tables.py` / `dump_all_results.py`（CPU，秒级）、git、论文 |

**分流的理由**：Colab 会话会被抢占且文件系统不持久。E3 是 13 个 k × 模型 × seed 的网格，
在 Colab 上几乎必然被中途打断；而 Cheaha 的 SLURM 有作业数组与 `afterok` 依赖，天生适合。
短任务（E2 基座臂、E5 用现有数据、所有纯分析）放 Colab 更快。

## Colab Pro / Pro+（主力）

- **加速器**：随可用性变化 —— A100 40GB / L4 / T4 16GB。**每次会话不保证同一型号。**
- **约束**：会话可被抢占；文件系统不持久
- **持久化**：**挂载 Google Drive**。`results/`、`models/`、`data/` 都落在 Drive 上
- **成本**：订阅费 + compute units。使用本身按 unit 计，非按美元直接计价

**代码库已经原生支持 Colab**：`config.py` 的 `_PROFILES` 里就有 `colab_free`（15 GB / batch 8）
和 `colab_pro`（40 GB / batch 32），且默认值就是 `colab_free`。

> **必须设 `PII_DEVICE_PROFILE=auto`。** 因为分到的 GPU 型号每次不同，`_auto_hw()` 会按实测
> 显存选档（≥70 GB → 80G 档，≥38 → 40G 档，≥20 → 24G 档，否则最小档）。写死 `colab_pro`
> 而实际拿到 T4，会 OOM。

> **每个 task 完成即把 `results.json` 与 attempts parquet 写回 Drive。** 会话被收回时未落盘的
> 证据就永久丢失，而算力已经花掉了。这一条在方法论里是硬性门禁。

> **每次 run 必须把实际 GPU 型号记进 `results.json`。** 否则 accelerator-hours 在 A100 与 T4
> 之间不可比，跨 run 的成本聚合就是错的。

## UAB Cheaha（SLURM，长扫描）

从 `slurm/*.slurm` 的 `#SBATCH` 声明读出：

| 分区 | GPU | 墙时上限 | 备注 |
|---|---|---|---|
| `amperenodes` | **A100 80GB** | 11:45:00 | 主力 GPU 队列 |
| `amperenodes-medium` | A100 80GB | 48:00:00 | 大模型（Pythia 1.4B/2.8B）走这条 |
| `pascalnodes` | **P100 16GB** | 12:00:00 | **约慢 3 倍**；小模型可用它 backfill |
| `express` | 无 GPU | 00:30:00 | 汇总/出表任务 |

每个 GPU 作业：`--gres=gpu:1 --cpus-per-task=8 --mem=64G`。

- **调度器**：Slurm。提交器接受 `PARTITION` / `GRES` / `ACCOUNT` 环境变量；`ACCOUNT` 默认空
  （不传 `--account`）。若集群要求 allocation 字符串，在此补上。
- **成本**：学术集群，**使用本身免费**。真正的约束是**排队时间与墙时**，不是钱。
- **作业切分策略**：`submit_per_model.sh` 已经把 scope 按模型右尺寸化，好让作业能 backfill
  进空闲槽（小模型同时投 `amperenodes,pascalnodes`）。这个策略要保留。

## 本机（写作与分析）

```
Apple M3 Max · 36 GB 统一内存 · macOS arm64 · Python 3.14.2
无 torch · 无 uv · 无 Slurm 客户端 · 无 .venv
磁盘 926 GB，已用 93%，剩余 68 GB
```

只用来跑 `make_tables.py` / `dump_all_results.py`（纯 pandas/numpy，秒级）和写论文。
**不要在这上面跑训练或攻击**——没有 CUDA，且 68 GB 余量放不下 checkpoint。

> 注意：`make_tables.py` 需要 `pandas` / `numpy` / `scipy` / `statsmodels`，本机目前都没装。
> 要在本机分析，先建一个只装分析依赖的轻量环境。

## 成本记账

两个远端环境**在使用点上都不收美元**，所以：

| 字段 | 约定 |
|---|---|
| `est_cost_usd` in `results.json` | 记 **0**（学术集群 / 已付订阅），真正的成本记在下一行 |
| **accelerator-hours** | **主记账单位**。= 墙时 × GPU 数 |
| GPU 型号 | 每 run 必记（`a100_80` / `a100_40` / `l4` / `t4` / `p100`），否则小时数不可比 |
| Colab compute units | 若 Colab 侧能读到，一并记；否则以 accelerator-hours 为准 |

### `confirm_above` 阈值（**临时值**）

**4 accelerator-hours** —— 超过这个量的启动需要显式批准。

这是**占位符，不是结论**。现在还没有任何一次 run 的实测成本，所以你我都不知道一次 GCG
攻击到底要多久。**这个值在协议阶段（protocol）用试点（pilot）实测的单 run 成本来确认。**
在那之前它只是一个防止手滑烧掉一天队列的粗糙护栏。

## 存储布局

| 位置 | 内容 |
|---|---|
| Drive（Colab）/ 项目目录（Cheaha） | `data/`（语料 + registry）、`models/<name>/`（微调 checkpoint + `train_meta.json`）、`results/attempts/*.parquet`、`results/tables/` |
| `.hf_cache/`（项目内） | 预取的基座模型权重；`setup_env.sh` 会填 |
| 仓库（git） | 代码、`.ai/research/`、`results/tables/*.txt` 可选提交；**`data/` `models/` `results/` 已在 `.gitignore` 中** |

## 环境与依赖 —— 一个未解决的重现性缺口

当前做法：`slurm/setup_env.sh` 执行 `python -m venv .venv` + `pip install -r requirements.txt`。
而 `requirements.txt` 用的是**下界约束**：

```
torch>=2.0.0
datasets>=2.14.0
faker>=18.0.0
...
```

**这不满足重现性契约。** `torch>=2.0.0` 在今天和三个月后解析出的是不同版本，同一份代码
在同一个 seed 上可能给出不同数字，而 `results.json` 里没有任何字段能记录这个差异——
第五个 pin（环境）实际上是缺失的。

**推荐迁移到 uv**：`pyproject.toml` 声明依赖 + 提交 `uv.lock` + 项目根的 `.venv/`。
Colab 和 Cheaha 都能用 uv。

> 但**这是一件独立的杂务，不作为 setup 的副作用执行**。迁移会动到所有作业脚本和
> Colab notebook，需要单独验证一遍端到端能跑通。要做的话，作为一个独立任务开始。
> 在迁移完成之前，`results.json` 的环境 pin 只能记 `pip freeze` 的快照哈希，
> 并在分析时把「环境未锁定」列为效度威胁。

## 待确认

- [ ] Cheaha 是否需要 `--account=<allocation>`（提交器支持，默认不传）
- [ ] Colab 侧 compute units 的余额与消耗速率（若要做预算门禁）
- [ ] `confirm_above` 的最终值 —— **协议阶段用 pilot 实测确认**
