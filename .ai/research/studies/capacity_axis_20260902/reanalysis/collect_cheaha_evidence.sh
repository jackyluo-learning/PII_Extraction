#!/usr/bin/env bash
# Run on Cheaha. Reads project evidence and scheduler records; launches no job.
set -euo pipefail
cd /data/user/jluo/PII_Extraction
bundle_dir=$(mktemp -d /tmp/e3-evidence.XXXXXX)
export E3_BUNDLE_DIR="$bundle_dir"
python3 - <<'PY'
from pathlib import Path
import os,json,hashlib,shutil,subprocess,tarfile
root=Path.cwd();out=Path(os.environ['E3_BUNDLE_DIR']);items=[]
for pattern in ['results/e17_matches_e3a_seed*.json','results/manifests/e3*.json','slurm/logs/*capacity*','slurm/logs/*e3*','requirements*.txt','*.lock','environment*.yml']:
 for p in root.glob(pattern):
  if p.is_file():
   dest=out/p.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for rel in ['data/target_registry.json','data/individuals.json','data/negative_controls.json','data/corpus_metadata.json','models/gpt2/train_meta.json','models/gpt2/config.json','models/gpt2/tokenizer_config.json','config.py','slurm/exp_capacity.slurm','slurm/sweep_config.sh','slurm/setup_env.sh']:
 p=root/rel
 if p.is_file():
  dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
for rel in ['data/corpus/train.json','data/target_registry.json','models/gpt2/model.safetensors','models/gpt2/tokenizer.json']:
 p=root/rel
 if not p.is_file():items.append({'path':rel,'missing':True});continue
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 items.append({'path':rel,'sha256_now':h.hexdigest(),'bytes':p.stat().st_size})
(out/'current_content_hashes.json').write_text(json.dumps(items,indent=2)+'\n')
commands={'git_identity_now.txt':['git','rev-parse','HEAD'],'git_status_now.txt':['git','status','--short'],'sacct.tsv':['sacct','-u',os.environ.get('USER','jluo'),'-S','2026-09-03','-E','2026-09-07','--parsable2','--format=JobIDRaw,JobName%80,State,ExitCode,Start,End,ElapsedRaw,AllocTRES%100']}
for name,cmd in commands.items():
 try:r=subprocess.run(cmd,capture_output=True,text=True,timeout=60);text=r.stdout+'\nSTDERR:\n'+r.stderr+'\nexit='+str(r.returncode)
 except Exception as exc:text=str(exc)
 (out/name).write_text(text)
py=root/'.venv/bin/python'
if py.exists():
 r=subprocess.run([str(py),'-m','pip','freeze'],capture_output=True,text=True,timeout=60);(out/'pip_freeze_now.txt').write_text(r.stdout);(out/'pip_freeze_status.txt').write_text(r.stderr+'\nexit='+str(r.returncode))
(out/'README.txt').write_text('Collected now; current hashes/status do not prove historical per-shard identity or repair code.dirty=null by themselves. No experiments launched. Slurm export is scoped to the study dates and current user.\n')
archive=out.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as tar:tar.add(out,arcname=out.name)
print(archive)
PY
