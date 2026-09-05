"""Dump the E3 sweep's raw attempt table, unaggregated and unmodified.

Three files:
  results/e3_raw_attempts.csv.gz  every attempt, every column, 4200 rows
  results/e3_hit_matrix.csv       per target x capacity, hits out of 3 seeds
  results/e3_nll_matrix.csv       per target x capacity, mean final_target_nll

The hit and NLL matrices are pivots of the first file, not new measurements.
"""
import glob
import pandas as pd

files = sorted(glob.glob("results/attempts/e3a__*.parquet"))
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
print(f"{len(df)} rows from {len(files)} shards")
print(f"columns: {list(df.columns)}\n")

df.to_csv("results/e3_raw_attempts.csv.gz", index=False, compression="gzip")

df["tid"] = df.target_membership + "|" + df.field + "|" + df.person_id
hit = (df.assign(h=df.exact_match.fillna(False).astype(int))
         .pivot_table(index="tid", columns="capacity_k", values="h", aggfunc="sum"))
meta = df.groupby("tid").agg(H_bits=("target_H_bits", "first"),
                             len_tokens=("target_len_tokens", "first"),
                             train_frequency=("train_frequency", "first"))
hit.join(meta).to_csv("results/e3_hit_matrix.csv")

nll = df.pivot_table(index="tid", columns="capacity_k",
                     values="final_target_nll", aggfunc="mean")
nll.join(meta).to_csv("results/e3_nll_matrix.csv")

print("wrote:")
for p in ("results/e3_raw_attempts.csv.gz", "results/e3_hit_matrix.csv",
          "results/e3_nll_matrix.csv"):
    import os
    print(f"  {p}  {os.path.getsize(p)/1024:.0f} KB")
print(f"\ntrain_frequency tiers in the trained arm: "
      f"{dict(sorted(df[df.target_membership=='trained'].groupby('train_frequency').person_id.nunique().items()))}")
