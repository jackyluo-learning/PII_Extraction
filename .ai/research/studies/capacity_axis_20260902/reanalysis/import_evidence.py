"""One-time recovery importer, followed by schema/provenance normalization.

Normal reanalysis starts from the committed ledger and does not rerun this importer.
Preserved to document the recovery procedure; completed imports are protected.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,collections,subprocess
import pandas as pd
root=Path.cwd();study=root/'.ai/research/studies/capacity_axis_20260902';out=study/'reanalysis';rec=root/'artifacts/capacity_axis_20260902/recovered_colab'
ledger=json.loads((study/'results.json').read_text());audit=json.loads((out/'raw_data_audit.json').read_text())
if ledger.get('reanalysis',{}).get('estimates'):
 raise SystemExit('Recovery already imported and analyzed. Use recompute.py; do not overwrite accepted provenance or estimates with the one-time importer.')
registry=json.loads((rec/'data/target_registry.json').read_text())
truth={e['person']['name']:e for e in registry}
allmain=pd.concat([pd.read_parquet(root/r['artifact']) for r in audit['shards']],ignore_index=True)
err=0
for row in allmain[allmain.capacity_k==0].itertuples(index=False):
 e=truth[row.person_id]
 err+=int(row.target_string!=e['person'][row.field] or ((row.target_membership=='control')!=e['is_negative_control']) or row.train_frequency!=e['frequency'])
assert err==0
repro=[]
original=pd.read_parquet(rec/'results/attempts/e3a__E3__gpt2_42_field-ssn-email_k20.parquet')
repeat=pd.read_parquet(rec/'results/attempts/e3a_repro__E3__gpt2_42_field-ssn-email_k20.parquet')
key=['target_membership','person_id','field'];joined=original.merge(repeat,on=key,suffixes=('_orig','_repro'),validate='one_to_one')
assert len(joined)==len(original)==len(repeat)==100
for arm,g in joined.groupby('target_membership',observed=True):
 n=len(g);flip=int((g.exact_match_orig!=g.exact_match_repro).sum());p=float(g.exact_match_orig.mean());repro.append({'arm':arm,'n_targets':n,'flips':flip,'flip_rate':flip/n,'criterion_bound':2*p*(1-p),'passed':flip/n<=2*p*(1-p)})
new=[]
for scope,paths,mbase in [('cheaha_main',sorted((root/'results/attempts').glob('e3a__*.parquet')),root/'results/manifests'),('colab_pilot',sorted((rec/'results/attempts').glob('*.parquet')),rec/'results/manifests')]:
 for p in paths:
  mpath=mbase/(p.stem+'.json');m=json.loads(mpath.read_text());d=pd.read_parquet(p);seed=int(m['shard']['seed']);k=int(m['shard']['capacity_k'])
  cfg={'shard':m['shard'],'PII_overrides':m.get('config',{}),'code_commit':m['code']['commit'],'environment_hash':m['env']['pip_freeze_sha256_16'],'source_scope':scope}
  cfg['shard']=dict(cfg['shard']);cfg['shard'].pop('seed',None)
  ch=hashlib.sha256(json.dumps(cfg,sort_keys=True,separators=(',',':')).encode()).hexdigest();rid=f'capacity_axis_20260902__{ch[:8]}__s{seed}'
  metrics={a:{'hits':int(g.exact_match.sum()),'attempts':len(g),'persons':g.person_id.nunique(),'targets':len(g[['person_id','field']].drop_duplicates()),'exact_match_rate':float(g.exact_match.mean()),'attempt_wallclock_s':float(g.wallclock_s.sum())} for a,g in d.groupby('target_membership',observed=True)}
  arts=[{'path':str(x.relative_to(root)),'sha256':hashlib.sha256(x.read_bytes()).hexdigest(),'bytes':x.stat().st_size,'role':role} for x,role in [(p,'raw_attempts'),(mpath,'launch_manifest')]]
  excluded=scope!='cheaha_main'
  new.append({'run_id':rid,'source_stem':p.stem,'source_scope':scope,'run_status':'completed','completion_basis':'full expected rows in recovered raw shard; scheduler terminal state not available','arm':'both','seed':seed,'config':cfg,'config_hash':ch,'config_hash_scope':'retrospective identity of observed manifest fields; not a launch-time complete resolved configuration','code_commit':m['code']['commit'],'code_dirty':m['code']['dirty'],'environment':m['env'],'accelerator':m['accelerator'],'dataset_version':'ledger fingerprint 7a059fc04ae21665; independently verified on recovered Colab corpus, not per-main-shard checkpoint','split_hash':m['target_subset_hash'],'model_checkpoint_sha256':None,'metrics':metrics,'metric_split':'fixed synthetic person-field audit set, D versus C','accelerator_hours':None,'est_cost_usd':0,'excluded':excluded,'exclusion_reason':'Pilot/cost/repro evidence kept for audit; outside single-environment Cheaha main sweep.' if excluded else None,'exclusion_preregistered':True if excluded else None,'confirmatory_eligible':False,'eligibility_reason':'Main checkpoint fingerprint and complete launch pins unavailable; code cleanliness additionally unknown.' if m['code']['dirty'] is None else ('Colab pilot/repro scope; not confirmatory.' if excluded else 'Main checkpoint fingerprint and complete launch pins unavailable; results conditional on recorded artifacts.'),'artifacts':arts})
# Normalize optional unknowns without inventing missing historical start times.
for r in new:
 r['config_hash_scope']='Retrospective canonical hash of observed manifest configuration, per-run seed excluded; historical full resolved launch config unavailable.'
 if r.get('code_dirty') is None:r.pop('code_dirty',None);r['code_dirty_state']='unknown (source manifest code.dirty=null)'
 else:r['code_dirty_state']='dirty' if r['code_dirty'] else 'clean as recorded'
 r['arm_metrics']=r['metrics'];r['metrics']={f'{a}_{k}':v for a,m in r['arm_metrics'].items() for k,v in m.items()};r['metrics']['alpha_k']=r['arm_metrics']['control']['exact_match_rate']
 r['evaluation_population']=r.pop('metric_split');r.pop('accelerator_hours',None);r['accelerator_hours_status']='unknown; scheduler allocation unavailable'
 if r.get('exclusion_preregistered') is None:r.pop('exclusion_preregistered',None)
 r['started_at_status']='unavailable in original manifest; current file times are not launch time'
 for a in r['artifacts']:a['evidence_kind']=a['role'];a['role']={'raw_attempts':'predictions','launch_manifest':'logs'}[a['role']]
old_ids={r['run_id'] for r in ledger['runs']}
for r in ledger['runs']:
 if r.get('source_scope') is None:
  r['excluded']=True;r['exclusion_reason']='Superseded by byte-addressed recovered Colab import; original path now names a different Cheaha artifact. Historical row retained.'
for r in new:
 if r['run_id'] not in old_ids:ledger['runs'].append(r)
post={'created_at':datetime.now(timezone.utc).isoformat(),'recovered_colab_files':len(json.loads((rec/'retrieval_manifest.json').read_text())),'registry_label_value_mismatches':err,'data_fingerprints_reverified':{f:hashlib.sha256((rec/'data'/f).read_bytes()).hexdigest() for f in ['target_registry.json','individuals.json','negative_controls.json','corpus/train.json']},'repro_check':{'passed':all(x['passed'] for x in repro),'comparisons':repro,'original_path':str((rec/'results/attempts/e3a__E3__gpt2_42_field-ssn-email_k20.parquet').relative_to(root)),'repeat_path':str((rec/'results/attempts/e3a_repro__E3__gpt2_42_field-ssn-email_k20.parquet').relative_to(root)),'scope':'Colab original code_dirty=true; repeat code_dirty=false; same recorded environment. Validates observed decisions, not clean launch or Cheaha checkpoint identity.'},'main_code_dirty_counts':dict(collections.Counter(str(r.get('code_dirty')) for r in new if r['source_scope']=='cheaha_main')),'remaining_missing':['Cheaha E17 matching records for seeds 42,1337,2024 (Colab seed42 recovered only)','Cheaha executed checkpoint/content fingerprint; current Drive checkpoint is not proof of main model identity','Original full environment lock and complete launch configuration','Cleanliness evidence for 6 main shards with code.dirty=null','Slurm job terminal states, walltime/GPU allocation, failed/preempted jobs; SSH authentication unavailable'],'new_imports':len(new),'imported_scope_counts':dict(collections.Counter(r['source_scope'] for r in new))}
ledger['reanalysis']={'status':'doing','raw_audit_path':str((out/'raw_data_audit.json').relative_to(root)),'post_recovery_audit':post,'inference_scope':'Conditional reanalysis of complete recorded main attempts. Not yet confirmatory or ready for closeout.','prior_analysis_superseded':True,'analysis_run_ids':[r['run_id'] for r in new if r['source_scope']=='cheaha_main']}
(study/'results.json').write_text(json.dumps(ledger,indent=2,ensure_ascii=False)+'\n');(out/'post_recovery_audit.json').write_text(json.dumps(post,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(post,indent=2,ensure_ascii=False))
