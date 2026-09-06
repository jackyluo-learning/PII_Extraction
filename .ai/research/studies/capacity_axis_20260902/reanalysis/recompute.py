"""Fresh ledger-linked conditional E3 analysis. No GPU/model inference."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,sys,time,warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.isotonic import IsotonicRegression
from lifelines import WeibullAFTFitter,LogNormalAFTFitter
from censored_models import weibull_fit,normal_interval_fit

ROOT=Path(__file__).resolve().parents[5]
STUDY=ROOT/'.ai/research/studies/capacity_axis_20260902'
OUT=STUDY/'reanalysis'
ART=ROOT/'artifacts/capacity_axis_20260902'
BOOT_ART=ART/'bootstrap'
GRID=np.array([0,1,2,3,4,6,8,12,16,20,24,32,48,64]);POS=GRID[1:]
SEEDS=[42,1337,2024];B=10000;BOOT_SEED=20240601
LOGV=np.log2(50257)


def clean(v):
    if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,(np.integer,)):return int(v)
    if isinstance(v,(np.bool_,)):return bool(v)
    if isinstance(v,(float,np.floating)):return float(v) if np.isfinite(v) else None
    return v


def save(obj,path):path.write_text(json.dumps(clean(obj),indent=2,ensure_ascii=False,allow_nan=False)+'\n')


def interval(x):return np.percentile(x,[2.5,97.5],axis=0)


def wilson(p,n):
    z=stats.norm.ppf(.975);den=1+z*z/n
    center=(p+z*z/(2*n))/den;rad=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return np.array([0. if p==0 else max(0.,center-rad),1. if p==1 else min(1.,center+rad)])


def mover(d,c,nd,nc):
    dl,du=wilson(d,nd);cl,cu=wilson(c,nc)
    return [d-c-np.hypot(d-dl,cu-c),d-c+np.hypot(du-d,c-cl)]


def bootstrap_p(reps,point,null=0):
    # tolerance retains mathematically equal boundaries for discrete rates.
    return (np.count_nonzero(np.abs(reps-point)>=abs(point-null)-1e-12)+1)/(len(reps)+1)


def load():
    led=json.loads((STUDY/'results.json').read_text());ids=led['reanalysis']['analysis_run_ids']
    assert led['reanalysis']['post_recovery_audit']['repro_check']['passed'] is True
    rows={r['run_id']:r for r in led['runs']};dfs=[]
    for rid in ids:
        r=rows[rid];assert r['run_status']=='completed' and not r['excluded'] and r['source_scope']=='cheaha_main'
        assert r.get('code_dirty') is not True
        a=next(x for x in r['artifacts'] if x.get('evidence_kind')=='raw_attempts');p=ROOT/a['path']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256']
        dfs.append(pd.read_parquet(p))
    df=pd.concat(dfs,ignore_index=True)
    key=['seed','capacity_k','target_membership','person_id','field']
    assert len(df)==4200 and not df.duplicated(key).any() and not df.exact_match.isna().any()
    assert set(df.seed)==set(SEEDS) and set(df.capacity_k)==set(GRID)
    assert len(df.groupby(['seed','capacity_k','target_membership','field'],observed=True))==168
    assert (df.groupby(['target_membership','person_id','field'],observed=True).size()==42).all()
    return led,df


def curve(df,idx):
    output={};rep={};persons={};point={};repeats={}
    for arm in ['control','trained']:
        sub=df[df.target_membership==arm]
        mat=sub.groupby(['person_id','capacity_k'],observed=True).exact_match.mean().unstack().reindex(columns=GRID).sort_index()
        assert mat.notna().all().all()
        arr=mat.to_numpy(dtype=float);persons[arm]=list(mat.index)
        rep[arm]=arr[idx[arm]].mean(axis=1);point[arm]=arr.mean(axis=0)
        repeats[arm]=int(sub.groupby(['person_id','capacity_k'],observed=True).size().iloc[0])
    tau=rep['trained']-rep['control'];rows=[]
    for j,k in enumerate(GRID):
        cell={'k':int(k),'n_seeds':3};degen=False
        for arm in ['control','trained']:
            g=df[(df.target_membership==arm)&(df.capacity_k==k)];n=len(persons[arm]);f=g.field.nunique();neff=n*f/(1+(f-1)*.5)
            est=point[arm][j];deg=est==0 or est==1;degen|=deg
            ci=wilson(est,neff) if deg else interval(rep[arm][:,j])
            m=f*3;neff_repeat=n*m/(1+(m-1)*.5)
            cell[arm]={'estimate':est,'ci':ci,'interval_method':'Wilson assumed n_eff' if deg else 'person-clustered percentile bootstrap','n_persons':n,'n_targets':n*f,'n_attempts':len(g),'successes':int(g.exact_match.sum()),'n_eff_if_wilson':neff,'repeat_icc_sensitivity_n_eff':neff_repeat,'repeat_icc_sensitivity_ci':wilson(est,neff_repeat) if deg else None,'attempt_elapsed_hours':float(g.wallclock_s.sum()/3600),'accelerator_hours':None}
        d=cell['trained']['estimate'];c=cell['control']['estimate']
        cell['tau']=d-c;cell['tau_ci']=mover(d,c,cell['trained']['n_eff_if_wilson'],cell['control']['n_eff_if_wilson']) if degen else interval(tau[:,j]);cell['tau_interval_method']='Newcombe/MOVER, two Wilson intervals with assumed n_eff' if degen else 'person-clustered percentile bootstrap'
        rows.append(cell)
    return rows,rep,tau,point,persons


def hypotheses(rows,rep,tau,point):
    alpha=point['control'][1:];r=stats.rankdata(rep['control'][:,1:],axis=1);r-=r.mean(axis=1,keepdims=True)
    kr=stats.rankdata(POS);kr-=kr.mean();rho_rep=(r@kr)/np.sqrt((r*r).sum(axis=1)*(kr*kr).sum())
    rho=stats.spearmanr(POS,alpha).statistic;j=int(np.where(GRID==20)[0][0]);t=point['trained'][j]-point['control'][j]
    h1={'rho':rho,'ci':interval(rho_rep),'p_raw':(np.count_nonzero(rho_rep<=0)+1)/(B+1),'n_persons_control':25,'n_seeds':3,'rule':'H1 upward trend if person-bootstrap rho CI strictly above zero; monotonic every-adjacent-point behavior is not tested','isotonic_summary':[{'k':int(k),'observed_alpha':float(y),'isotonic_alpha':float(z)} for k,y,z in zip(POS,alpha,IsotonicRegression(increasing=True).fit_transform(POS,alpha))]}
    h3={'tau':t,'ci':rows[j]['tau_ci'],'p_raw':bootstrap_p(tau[:,j],t),'n_persons_per_arm':25,'n_seeds':3,'rule':'CI excludes 0 rejects the null; containing zero is inconclusive, not equivalence','seed_values':[]}
    maps=[]
    for tol in [.01,.05,.09,.10,.15,.20,.30,.50,.75,.90,1.0]:
        candidates=[x for x in rows[1:] if x['control']['ci'][1]<=tol and (x['tau_ci'][0]>0 or x['tau_ci'][1]<0)]
        detection=max(candidates,key=lambda x:x['trained']['estimate']) if candidates else None
        ratio_candidates=[x for x in candidates if x['control']['estimate']>0]
        certification=max(ratio_candidates,key=lambda x:x['trained']['estimate']/x['control']['estimate']) if ratio_candidates else None
        maps.append({'tolerance':tol,'below_preregistered_resolution':tol<.09,'floor_only_capacities':[x['k'] for x in rows[1:] if x['control']['ci'][1]<=tol],'joint_capacities':[x['k'] for x in candidates],'largest_joint_capacity':max([x['k'] for x in candidates],default=None),'detection_optimum_k':detection['k'] if detection else None,'likelihood_ratio_optimum_k':certification['k'] if certification else None,'positive_tau_capacities':[x['k'] for x in candidates if x['tau_ci'][0]>0]})
    sensitivity=[]
    for name,neff in [('target_only_icc_0.5',50/1.5),('all_repeats_icc_0.5',150/(1+5*.5))]:
        per_k=[]
        for x in rows[1:]:
            consistent_tau_ci=mover(x['trained']['estimate'],x['control']['estimate'],neff,neff)
            per_k.append({'k':x['k'],'control_wilson_ci':wilson(x['control']['estimate'],neff),'tau_mover_ci':consistent_tau_ci})
        sens_maps=[]
        for tol in [.01,.05,.09,.10,.15,.20,.30,.50,.75,.90,1.0]:
            eligible=[(x,s) for x,s in zip(rows[1:],per_k) if s['control_wilson_ci'][1]<=tol]
            sens_maps.append({
                'tolerance':tol,
                'floor_only_capacities':[x['k'] for x,s in eligible],
                'positive_tau_joint_capacities_using_primary_tau_ci':[x['k'] for x,s in eligible if x['tau_ci'][0]>0],
                'positive_tau_joint_capacities_using_consistent_mover':[x['k'] for x,s in eligible if s['tau_mover_ci'][0]>0],
                'any_direction_joint_capacities_using_consistent_mover':[x['k'] for x,s in eligible if s['tau_mover_ci'][0]>0 or s['tau_mover_ci'][1]<0],
            })
        sensitivity.append({'name':name,'n_eff':neff,'per_k':per_k,'mapping':sens_maps})
    h2={'p_raw':None,'holm_reserved_p':1.,'one_percent_verdict':'unresolved at achieved sample size','resolution_floor_preregistered':.09,'zero_count_wilson_upper':float(wilson(0,50/1.5)[1]),'minimum_people_per_arm_for_zero_wilson_upper_1pct':int(np.ceil(stats.norm.ppf(.975)**2*.99/.01*1.5/2)),'minimum_people_scope':'Zero observed hits only; same two-field ICC=.5 assumption, two-sided Wilson. This is not a power calculation for tau or a guarantee of a feasible point.','mapping':maps,'rule':'both alpha upper CI <= tolerance and tau CI excludes zero; retain sign; descriptive mapping cannot establish impossibility','global_test':'not defined by preregistration; not replaced by floor-only p','consistent_interval_sensitivity':{'label':'post-hoc method-consistency sensitivity; does not replace the disclosed hybrid main analysis','conventions':sensitivity,'conclusion':'The hybrid primary mapping makes k=4 floor-eligible at 5%-10% because its nonzero cell uses a percentile interval while k=1-3 use Wilson. Applying Wilson consistently removes that reversal under the conservative target-only effective n. No convention yields a positive-tau joint operating point; H2 remains unresolved, not refuted.'}}
    tpos=tau[:,1:];maxv=tpos.max(axis=1);ties=np.isclose(tpos,maxv[:,None],atol=1e-12,rtol=0)
    earliest=POS[np.argmax(ties,axis=1)];latest=POS[len(POS)-1-np.argmax(ties[:,::-1],axis=1)]
    observed=point['trained'][1:]-point['control'][1:];obsmax=POS[np.isclose(observed,observed.max(),atol=1e-12,rtol=0)]
    X=np.stack([np.ones(len(POS)),np.log(POS),np.log(POS)**2],axis=1);coef=observed@np.linalg.pinv(X).T;coefrep=tpos@np.linalg.pinv(X).T
    h5={'label':'(exploratory), underpowered','observed_maximizers':obsmax,'argmax_envelope_ci':[np.percentile(earliest,2.5),np.percentile(latest,97.5)],'first_argmax_ci':interval(earliest),'tied_maximum_replicates':int((ties.sum(axis=1)>1).sum()),'quadratic_logk_coefficient':coef[2],'quadratic_ci':interval(coefrep[:,2]),'quadratic_one_sided_p':(np.count_nonzero(coefrep[:,2]-coef[2]<=coef[2]+1e-12)+1)/(B+1),'quadratic_p_method':'Null-centered bootstrap left tail; disclosed post-result implementation, exploratory, unadjusted.','flatness':'no prespecified equivalence threshold; lack of significant curvature does not prove flatness'}
    return {'H1':h1,'H2':h2,'H3':h3,'H5':h5},rho_rep


def kmin(df):
    sub=df[df.capacity_k>0];rows=[]
    for (arm,p,f),g in sub.groupby(['target_membership','person_id','field'],sort=True,observed=True):
        hit=g.groupby('capacity_k',observed=True).exact_match.any().reindex(POS);yes=np.flatnonzero(hit.to_numpy())
        first=int(yes[0]) if len(yes) else None
        rows.append({'arm':arm,'person_id':p,'field':f,'H_bits':float(g.target_H_bits.iloc[0]),'lower':float(POS[first-1] if first else 0) if first is not None else 64.,'upper':float(POS[first]) if first is not None else np.inf,'nonmonotone':bool((~hit.iloc[first+1:]).any()) if first is not None else False})
    return pd.DataFrame(rows)


def aft(km,idx,nfits,validate_only=False):
    c=km[km.arm=='control'].sort_values(['person_id','field']);people=sorted(c.person_id.unique());h=c.H_bits.to_numpy();logh=np.log(h);center=logh.mean();x=logh-center;l=c.lower.to_numpy();u=c.upper.to_numpy();design=pd.DataFrame({'lower':np.maximum(l,1e-9),'upper':u,'log_h_centered':x})
    wf=WeibullAFTFitter().fit_interval_censoring(design,'lower','upper')
    ref=np.array([wf.params_.loc[('lambda_','Intercept')],wf.params_.loc[('lambda_','log_h_centered')],wf.params_.loc[('rho_','Intercept')]])
    fit,nll=weibull_fit(x,l,u,start=ref);assert np.allclose(fit,ref,atol=5e-4,rtol=5e-4),(fit,ref)
    assert abs(nll+wf.log_likelihood_)<1e-5
    validation=[{'kind':'full','max_parameter_difference':float(np.max(np.abs(fit-ref))),'log_likelihood_difference':nll+wf.log_likelihood_}]
    counts=np.stack([(idx['control']==j).sum(axis=1) for j in range(len(people))],axis=1)
    person_index=np.array([people.index(p) for p in c.person_id]);tcenter=h.mean();tx=h-tcenter
    tfit,tnll=normal_interval_fit(tx,l,u)
    gammas=[];intercepts=[];tobit=[];failed=[]
    t0=time.time()
    for i in range(nfits):
        w=counts[i][person_index]
        try:
            ff,nn=weibull_fit(x,l,u,weights=w,start=fit)
            if i<3:
                repeated=design.iloc[np.repeat(np.arange(len(c)),w)].reset_index(drop=True)
                check=WeibullAFTFitter().fit_interval_censoring(repeated,'lower','upper')
                cp=np.array([check.params_.loc[('lambda_','Intercept')],check.params_.loc[('lambda_','log_h_centered')],check.params_.loc[('rho_','Intercept')]])
                assert np.allclose(ff,cp,atol=1e-3,rtol=1e-3),(ff,cp)
                validation.append({'kind':f'bootstrap_{i}','max_parameter_difference':float(np.max(np.abs(ff-cp))),'log_likelihood_difference':nn+check.log_likelihood_})
            gammas.append(ff[1]);intercepts.append(ff[0]-ff[1]*center)
        except Exception as exc:
            failed.append({'replicate':i,'model':'Weibull','error':str(exc)});gammas.append(np.nan);intercepts.append(np.nan)
        try:
            tf,_=normal_interval_fit(tx,l,u,weights=w,start=tfit);tobit.append([tf[0]-tf[1]*tcenter,tf[1]])
        except Exception as exc:
            failed.append({'replicate':i,'model':'Tobit','error':str(exc)});tobit.append([np.nan,np.nan])
        if (i+1)%500==0:print(f'censored refits {i+1}/{nfits}; seconds={time.time()-t0:.1f}; failures={len(failed)}',flush=True)
    if failed:raise RuntimeError(f'Censored refit failures must be reconciled: {failed[:5]}')
    gs=np.array(gammas);ins=np.array(intercepts);ts=np.array(tobit)
    BOOT_ART.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(BOOT_ART/'censored_bootstrap.npz',gamma=gs,intercept=ins,tobit=ts)
    save(validation,OUT/'solver_validation.json')
    lf=LogNormalAFTFitter().fit_interval_censoring(design,'lower','upper')
    a,b,t=fit;inter=a-b*center
    result={'gamma':b,'gamma_ci':interval(gs),'p_raw':bootstrap_p(gs,b,1),'intercept_log_scale':inter,'intercept_ci':interval(ins),'beta_scale_exp_minus_intercept':np.exp(-inter),'beta_scale_ci':interval(np.exp(-ins)),'beta_units_warning':'When gamma differs from1, this scale is not a constant bits/token rate. Do not quote as beta forcing rate.','n_targets':len(c),'n_persons':len(people),'n_seeds':3,'bootstrap_replicates':nfits,'bootstrap_failures':failed,'right_censored_fraction':float(np.isinf(u).mean()),'nonmonotone_targets':int(c.nonmonotone.sum()),'secondary_tobit':{'intercept':tfit[0]-tfit[1]*tcenter,'slope_tokens_per_bit':tfit[1],'intercept_ci':interval(ts[:,0]),'slope_ci':interval(ts[:,1]),'n_persons':len(people),'label':'preregistered secondary specification; same conditional evidence limits'},'lognormal_distribution_sensitivity':{'gamma':lf.params_.loc[('mu_','log_h_centered')],'label':'(exploratory) distribution not preregistered; point diagnostic only'},'solver_validation':validation,'rule':'Reject proportionality if gamma CI excludes1; Holm uses disclosed centered-bootstrap p. CI containing1 does not establish equivalence.'}
    return result


def smd(d,c):
    d=np.asarray(d,float);c=np.asarray(c,float);scale=np.sqrt((d.var(ddof=1)+c.var(ddof=1))/2);diff=d.mean()-c.mean()
    return float(diff/scale) if scale>0 else (0. if diff==0 else np.nan)


def diagnostics(df,km,idx):
    raw=df[df.capacity_k==1].drop_duplicates(['target_membership','person_id','field']).copy();raw['char_len']=raw.target_string.str.len();balance=[]
    for f in ['ssn','email']:
        for col in ['char_len','target_len_tokens','target_H_bits']:
            d=raw[(raw.target_membership=='trained')&(raw.field==f)].sort_values('person_id')[col].to_numpy(float);c=raw[(raw.target_membership=='control')&(raw.field==f)].sort_values('person_id')[col].to_numpy(float)
            ds=d[idx['trained']];cs=c[idx['control']];den=np.sqrt((ds.var(axis=1,ddof=1)+cs.var(axis=1,ddof=1))/2);diff=ds.mean(axis=1)-cs.mean(axis=1);rr=np.divide(diff,den,out=np.zeros_like(diff),where=den>0)
            balance.append({'scope':'actual Cheaha attacked target marginals','field':f,'covariate':col,'smd':smd(d,c),'ci':interval(rr),'n_D':len(d),'n_C':len(c),'passes_abs_0_1':abs(smd(d,c))<.1})
    pairs=json.loads((ART/'recovered_colab/results/e17_matches_e3a_seed42.json').read_text());e17=[]
    selected=set(raw.loc[raw.target_membership=='trained','person_id'])
    for scope in ['all_matching','attacked_D_matching']:
        use=[p for p in pairs if scope=='all_matching' or p['trained']['person_id'] in selected]
        for f in ['ssn','email']:
            pp=[p for p in use if p['trained']['field']==f]
            for mode in ['pair_weighted','deduplicated_marginals']:
                ds=[p['trained'] for p in pp];cs=[p['control'] for p in pp]
                if mode=='deduplicated_marginals':
                    ds=list({x['person_id']:x for x in ds}.values());cs=list({x['person_id']:x for x in cs}.values())
                for col in ['char_len','tok_len','H_bits']:
                    e17.append({'source':'Colab seed42 only; missing Cheaha E17 not replaced','scope':scope,'variant':mode,'field':f,'covariate':col,'smd':smd([x[col] for x in ds],[x[col] for x in cs]),'n_D':len(ds),'n_C':len(cs)})
    c=km[km.arm=='control'].sort_values(['person_id','field']);h=c.H_bits.to_numpy();low=c.lower.to_numpy();upper=c.upper.to_numpy();people=sorted(c.person_id.unique());loc={p:np.flatnonzero(c.person_id.to_numpy()==p) for p in people};bootrows=np.array([np.concatenate([loc[people[j]] for j in draw]) for draw in idx['control']])
    beta=[]
    for f in ['pooled','ssn','email']:
        mask=np.ones(len(c),bool) if f=='pooled' else c.field.to_numpy()==f;ff=c[mask];lo_ratio=ff.H_bits.to_numpy()/ff.upper.to_numpy();hi_ratio=ff.H_bits.to_numpy()/np.maximum(ff.lower.to_numpy(),1e-100)
        draws=bootrows if f=='pooled' else np.array([row[mask[row]] for row in bootrows]);hl=h/upper;hh=h/np.maximum(low,1e-100)
        beta.append({'field':f,'n_persons':25,'n_targets':int(mask.sum()),'n_seeds':3,'conservative_median':np.median(lo_ratio),'conservative_ci':interval(np.median(hl[draws],axis=1)),'optimistic_median':np.median(hi_ratio),'optimistic_ci':interval(np.median(hh[draws],axis=1)),'conservative_fraction_log2V':np.median(lo_ratio)/LOGV,'label':'interval-grid ratio diagnostic; not a validated transferable constant'})
    complete=np.isfinite(upper);fit=stats.linregress(h[complete],upper[complete]);lin=[]
    for rr in bootrows:
        rr=rr[complete[rr]];f=stats.linregress(h[rr],upper[rr]);lin.append([f.intercept,f.slope])
    lin=np.array(lin);grand=h.mean();total=float(np.mean((h-grand)**2));within=float(sum(((g.H_bits-g.H_bits.mean())**2).sum() for _,g in c.groupby('field'))/len(c));between=total-within
    per_seed=[]
    for seed in SEEDS:
        one=kmin(df[df.seed==seed]);one=one[one.arm=='control'].sort_values(['person_id','field'])
        for field in ['ssn','email']:
            g=one[one.field==field].sort_values('person_id');v=g.upper.to_numpy();br=v[idx['control']]
            per_seed.append({'label':'(exploratory) single attack seed sensitivity','seed':seed,'field':field,'n_persons':len(g),'median_first_hit_k':float(np.median(v)),'median_ci':interval(np.median(br,axis=1)),'right_censored_targets':int(np.isinf(v).sum()),'nonmonotone_targets':int(g.nonmonotone.sum())})
    return {'per_seed_kmin':per_seed,'actual_marginal_balance':balance,'recovered_colab_e17_balance':e17,'direct_beta_brackets':beta,'complete_case_linear':{'intercept':fit.intercept,'intercept_ci':interval(lin[:,0]),'slope':fit.slope,'slope_ci':interval(lin[:,1]),'inverse_slope_bits_per_token':1/fit.slope,'label':'complete-case diagnostic only'},'H_variance_control':{'total':total,'within_field':within,'between_field':between,'within_fraction':within/total,'by_field':{f:{'n':len(g),'sd':float(g.H_bits.std()),'range':float(g.H_bits.max()-g.H_bits.min())} for f,g in c.groupby('field')}},'nonmonotone_by_arm':{a:{'n_targets':len(g),'count':int(g.nonmonotone.sum()),'fraction':float(g.nonmonotone.mean())} for a,g in km.groupby('arm')}}


def auc_exploratory(df,idx):
    wc=np.stack([(idx['control']==j).sum(axis=1) for j in range(25)],axis=1)/25
    wd=np.stack([(idx['trained']==j).sum(axis=1) for j in range(25)],axis=1)/25
    rows=[]
    for field in ['ssn','email','pooled']:
        for k in POS:
            sub=df[(df.capacity_k==k)&(True if field=='pooled' else df.field==field)];arrays={}
            for a in ['control','trained']:
                g=sub[sub.target_membership==a].sort_values(['person_id','field','seed']);arrays[a]=-g.final_target_nll.to_numpy().reshape(25,-1)
            ds=arrays['trained'];cs=arrays['control'];compare=(ds[:,None,:,None]>cs[None,:,None,:]).mean(axis=(2,3))+.5*(ds[:,None,:,None]==cs[None,:,None,:]).mean(axis=(2,3));rr=np.einsum('bi,ij,bj->b',wd,compare,wc,optimize=True)
            rows.append({'label':'(exploratory)','field':field,'k':int(k),'auc':float(compare.mean()),'ci':interval(rr),'n_persons_per_arm':25,'n_seeds':3,'multiple_comparison_note':'pointwise exploratory intervals, no confirmatory discovery claim'})
    return rows


def figures(R):
    import os
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/e3-mpl-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    dest=ART/'figures';dest.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.2),constrained_layout=True)
    rows=R['curves']['pooled'];x=np.array([r['k'] for r in rows])
    for arm,label,color in [('control','Control forcing floor','#ba462c'),('trained','Trained extraction rate','#266c98')]:
        y=np.array([r[arm]['estimate'] for r in rows]);ci=np.array([r[arm]['ci'] for r in rows]);axes[0].plot(x,y,'o-',label=label,color=color);axes[0].fill_between(x,ci[:,0],ci[:,1],alpha=.14,color=color)
    axes[0].axvline(1.49,color='gray',ls=':',label='Design reference k=1.49 only');axes[0].set_ylim(-.02,1.04);axes[0].set_ylabel('Exact-match probability');axes[0].legend(fontsize=8,loc='upper left')
    y=np.array([r['tau'] for r in rows]);ci=np.array([r['tau_ci'] for r in rows]);axes[1].errorbar(x,y,yerr=np.stack([y-ci[:,0],ci[:,1]-y]),fmt='o-',capsize=2,color='#555');axes[1].axhline(0,color='gray',lw=1);axes[1].set_ylabel('Trained minus control rate')
    for ax in axes:ax.set_xscale('symlog',linthresh=1);ax.set_xlim(-.12,72);ax.set_xticks([0,1,2,4,8,16,32,64]);ax.set_xticklabels([0,1,2,4,8,16,32,64]);ax.set_xlabel('Free prompt tokens k');ax.grid(alpha=.15)
    fig.savefig(dest/'capacity_and_signal.png');fig.savefig(dest/'capacity_and_signal.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.2),constrained_layout=True)
    for arm,ax in zip(['control','trained'],axes):
        for s in SEEDS:
            rr=[r for r in R['seed_rates'] if r['seed']==s and r['arm']==arm];ax.plot([r['k'] for r in rr],[r['rate'] for r in rr],'o-',label=str(s),alpha=.8)
        ax.set_xscale('symlog',linthresh=1);ax.set_xlim(-.12,72);ax.set_xticks([0,1,2,4,8,16,32,64]);ax.set_xticklabels([0,1,2,4,8,16,32,64]);ax.set_ylim(-.02,1.04);ax.set_title(arm.title());ax.set_xlabel('Free prompt tokens k');ax.set_ylabel('Exact-match rate');ax.legend(title='Attack seed');ax.grid(alpha=.15)
    fig.savefig(dest/'seed_spread.png');fig.savefig(dest/'seed_spread.pdf');plt.close(fig)
    fig,ax=plt.subplots(figsize=(6.5,4.2),constrained_layout=True)
    for field,color in [('ssn','#266c98'),('email','#ba462c')]:
        rr=[r for r in R['auc_exploratory'] if r['field']==field];xx=np.array([r['k'] for r in rr]);yy=np.array([r['auc'] for r in rr]);ci=np.array([r['ci'] for r in rr]);ax.plot(xx,yy,'o-',label=field,color=color);ax.fill_between(xx,ci[:,0],ci[:,1],alpha=.12,color=color)
    ax.axhline(.5,color='gray',ls='--');ax.set_xscale('log',base=2);ax.set_ylim(0,1);ax.set_xlabel('Free prompt tokens k');ax.set_ylabel('AUC of -NLL');ax.set_title('Exploratory, pointwise intervals');ax.legend();fig.savefig(dest/'auc_exploratory.png');fig.savefig(dest/'auc_exploratory.pdf');plt.close(fig)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--n-fit',type=int,default=B);args=ap.parse_args()
    led,df=load();rng=np.random.default_rng(BOOT_SEED);idx={'control':rng.integers(0,25,size=(B,25)),'trained':rng.integers(0,25,size=(B,25))}
    R={'status':'conditional_reanalysis_not_ready_for_closeout','created_at':datetime.now(timezone.utc).isoformat(),'n_boot':B,'bootstrap_seed':BOOT_SEED,'curves':{},'seed_rates':[],'analysis_run_ids':led['reanalysis']['analysis_run_ids']}
    for field in ['pooled','ssn','email']:
        sub=df if field=='pooled' else df[df.field==field];rows,rep,tau,point,persons=curve(sub,idx);R['curves'][field]=rows
        if field=='pooled':
            R['hypotheses'],rho_rep=hypotheses(rows,rep,tau,point)
            BOOT_ART.mkdir(parents=True,exist_ok=True)
            np.savez_compressed(BOOT_ART/'joint_bootstrap.npz',alpha=rep['control'],emr_d=rep['trained'],tau=tau,idx_c=idx['control'],idx_d=idx['trained'],rho=rho_rep)
    for (s,k,a),g in df.groupby(['seed','capacity_k','target_membership'],sort=True,observed=True):R['seed_rates'].append({'seed':int(s),'k':int(k),'arm':a,'rate':float(g.exact_match.mean()),'hits':int(g.exact_match.sum()),'attempts':len(g)})
    R['hypotheses']['H3']['seed_values']=[r for r in R['seed_rates'] if r['k']==20]
    km=kmin(df);km.to_csv(OUT/'kmin_recomputed.csv',index=False)
    R['diagnostics']=diagnostics(df,km,idx);R['auc_exploratory']=auc_exploratory(df,idx)
    save(R,OUT/'intermediate_results.json')
    print('Curve, balance and exploratory calculations complete; starting censored fits.',flush=True)
    R['hypotheses']['H4']=aft(km,idx,args.n_fit)
    if args.n_fit != B:
        save(R['hypotheses']['H4'],OUT/'solver_smoke.json')
        print('Solver validation only; no final results or ledger update.',flush=True)
        return
    ps={h:(R['hypotheses'][h].get('p_raw') if R['hypotheses'][h].get('p_raw') is not None else 1.) for h in ['H1','H2','H3','H4']};order=sorted(ps,key=ps.get);last=0.;holm={}
    for j,h in enumerate(order):last=max(last,min(1.,(4-j)*ps[h]));holm[h]={'p_raw_or_reserved':ps[h],'p_holm':last,'reject_at_0_05':last<.05,'H2_reserved_not_tested':h=='H2'}
    R['holm']=holm;R['compute']={'main_attempt_elapsed_hours':{a:float(g.wallclock_s.sum()/3600) for a,g in df.groupby('target_membership',observed=True)},'accelerator_hours':None,'budget_accelerator_hours':24,'failed_job_hours':None,'note':'Attempt-call elapsed only; not allocated GPU hours.'}
    save(R,OUT/'recomputed_results.json')
    led['reanalysis']['estimates']=clean(R);led['reanalysis']['status']='computed_conditionally_pending_provenance_and_review';save(led,STUDY/'results.json')
    figures(R)
    print(json.dumps(clean({'H1':R['hypotheses']['H1'],'H2':R['hypotheses']['H2']['one_percent_verdict'],'H3':R['hypotheses']['H3'],'H4':R['hypotheses']['H4'],'H5':R['hypotheses']['H5'],'holm':holm,'compute':R['compute']}),indent=2),flush=True)


if __name__=='__main__':main()
