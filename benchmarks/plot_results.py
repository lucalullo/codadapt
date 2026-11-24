"""Recreate figures from recorded aggregate measurements; never fit or load models."""
from pathlib import Path
import csv
import os
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'figures'
OUT.mkdir(exist_ok=True)
DATA = ROOT / 'data'
COLORS = {'CodAdapt 2.1.0':'#166B80','Logistic / Ridge':'#9CA6B5','Random Forest':'#7B8CA7','HistGradientBoosting':'#8C9C91','XGBoost':'#BF936D','LightGBM':'#9C91B7','CatBoost':'#738C9B'}
ALGORITHMS = list(COLORS)
SHORT = ['Linear','RF','HistGB','XGBoost','LightGBM','CatBoost']
TASK_COLORS = {'binary':'#16728A','multiclass':'#C18A36','regression':'#438A6B'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,'axes.labelsize':10,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white','axes.facecolor':'white','text.color':'#203241','axes.labelcolor':'#203241','xtick.color':'#415467','ytick.color':'#415467','svg.hashsalt':'codadapt220-review','svg.fonttype':'none'})

def rows(name):
    with (DATA / name).open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save(fig,name):
    fig.savefig(OUT / (name+'.svg'),format='svg',bbox_inches='tight',metadata={'Date':None,'Creator':'CodAdapt recorded-data plotter'})
    plt.close(fig)

def title(fig,heading,subtitle):
    fig.text(.04,.98,heading,fontsize=17,fontweight='bold',va='top')
    fig.text(.04,.936,subtitle,fontsize=10,color='#586C7C',va='top')

measurements=rows('measurements.csv')
pairs=rows('paired_comparisons.csv')
datasets=rows('datasets.csv')
lookup={(r['dataset'],r['algorithm']):r for r in measurements}
for task,metric,axislabel in [('binary','roc_auc','ROC-AUC ↑'),('multiclass','balanced_accuracy','Balanced accuracy ↑'),('regression','rmse','RMSE ↓ (dataset-specific units)')]:
    names=[r['dataset'] for r in datasets if r['task']==task]
    nr=math.ceil(len(names)/2)
    fig,axes=plt.subplots(nr,2,figsize=(12,nr*3.15+1.0),squeeze=False)
    title(fig,task.title()+' | observed predictive quality','CodAdapt 2.1.0 vs frozen comparators • numerical observations, not confirmed superiority')
    for ax,name in zip(axes.flat,names):
        available=[(a,lookup[(name,a)][metric]) for a in ALGORITHMS if (name,a) in lookup]
        values=[float(v) for a,v in available]
        y=np.arange(len(available))
        ax.barh(y,values,color=[COLORS[a] for a,v in available],height=.66)
        ax.set_yticks(y,[a if a!='HistGradientBoosting' else 'HistGB' for a,v in available],fontsize=8.5)
        ax.invert_yaxis();ax.set_title(name,loc='left',fontweight='bold');ax.set_xlabel(axislabel,fontsize=9)
        mx=max(values); ax.set_xlim(0,1.13 if task!='regression' else mx*1.25)
        ax.xaxis.set_major_locator(MaxNLocator(5));ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
        for yi,(a,v) in enumerate(available):
            x=float(v); txt=f'{x:.4g}'
            ax.text(x+(1 if task!='regression' else mx)*.018,yi,txt,va='center',fontsize=8)
    for ax in list(axes.flat)[len(names):]:ax.axis('off')
    fig.subplots_adjust(left=.19,right=.97,top=.865,bottom=.065,wspace=.62,hspace=.70)
    save(fig,'quality_'+task)

# Cost grids show original displayed-value ratios, with a symmetric log2 color scale.
comparators=ALGORITHMS[1:]
allnames=[r['dataset'] for r in datasets]
pairmap={(p['dataset'],p['competitor']):p for p in pairs}
cmap=LinearSegmentedColormap.from_list('cost',['#146C88','#EAF0F3','#B66B37']);cmap.set_bad('#DDE2E8')
for metric,label,better in [('fit_prep_s','Training + preparation (s)','lower'),('b1_ms','Single-row raw-input latency (ms)','lower'),('b3000_ms','Batch 3,000 raw-input latency (ms)','lower'),('train_rss_mib','Training peak process RSS (MiB)','lower'),('model_bytes','Serialized model footprint (bytes)','lower'),('load_ms','Hash + deserialization load time (ms)','lower'),('rows_per_s','Batch throughput (rows/s)','higher')]:
    values=np.full((len(allnames),6),np.nan)
    for i,n in enumerate(allnames):
        for j,a in enumerate(comparators):
            r=pairmap.get((n,a),{}).get(metric+'_ratio','')
            if r not in ('','ND',None) and float(r)>0:values[i,j]=float(r)
    ratio=np.log2(values) * (1 if better=='lower' else -1)
    fig,ax=plt.subplots(figsize=(12,8.3));title(fig,label,'CodAdapt 2.1.0 / comparator • blue favors CodAdapt • numerical, machine-specific observations')
    im=ax.imshow(np.ma.masked_invalid(ratio),cmap=cmap,norm=TwoSlopeNorm(vmin=-4,vcenter=0,vmax=4),aspect='auto')
    ax.set_xticks(range(6),SHORT);ax.set_yticks(range(len(allnames)),allnames,fontsize=9)
    for i in range(len(allnames)):
        for j in range(6):
            v=values[i,j];txt='ND' if not np.isfinite(v) else (f'{v:.2f}×' if .1<=v<100 else f'{v:.2g}×')
            ax.text(j,i,txt,ha='center',va='center',fontsize=8.8,color='white' if np.isfinite(ratio[i,j]) and abs(ratio[i,j])>2.7 else '#203241')
    ax.set_xticks(np.arange(-.5,6,1),minor=True);ax.set_yticks(np.arange(-.5,len(allnames),1),minor=True);ax.grid(which='minor',color='white',lw=.9);ax.tick_params(which='minor',bottom=False,left=False)
    for spine in ax.spines.values():spine.set_visible(False)
    cb=fig.colorbar(im,ax=ax,pad=.02,shrink=.80,ticks=[-4,-2,0,2,4]);cb.ax.set_yticklabels(['≥16× advantage','4× advantage','1×','4× disadvantage','≥16× disadvantage']);cb.ax.tick_params(labelsize=8)
    fig.text(.26,.035,'Ratios are derived from printed measurements. Color clips at 16×; labels retain displayed ratio. ND = unavailable.',fontsize=9,color='#586C7C')
    fig.subplots_adjust(left=.27,right=.91,top=.87,bottom=.09);save(fig,metric)

fig,ax=plt.subplots(figsize=(9.5,6.0));title(fig,'Quality–resource trade-offs','83 observed pairs • loss and model-byte ratios • 15 joint favorable points highlighted')
for task in TASK_COLORS:
    ps=[p for p in pairs if p['task']==task and p['status']!='missing']
    x=[float(p['model_bytes_ratio']) for p in ps]
    y=[float(p['rmse_ratio'] if task=='regression' else p['logloss_ratio']) for p in ps]
    ax.scatter(x,y,s=40,color=TASK_COLORS[task],alpha=.8,edgecolor='white',linewidth=.5,label=task.title())
    h=[p for p in ps if p['joint_favorable_point']=='yes']
    if h:ax.scatter([float(p['model_bytes_ratio']) for p in h],[float(p['rmse_ratio'] if task=='regression' else p['logloss_ratio']) for p in h],s=95,facecolors='none',edgecolors='#203241',linewidth=1.1)
ax.set_xscale('log');ax.set_yscale('log');ax.axvline(.5,color='#758999',linestyle='--',lw=1);ax.axhline(1.05,color='#758999',linestyle='--',lw=1);ax.grid(which='major',alpha=.2)
ax.set_xlabel('Serialized model bytes ratio (CodAdapt / comparator)');ax.set_ylabel('Loss ratio (CodAdapt / comparator)')
handles,labels=ax.get_legend_handles_labels();handles.append(Line2D([0],[0],marker='o',markersize=9,color='#203241',linestyle='none',markerfacecolor='none'));labels.append('Joint pointwise screen');ax.legend(handles,labels,loc='upper left',fontsize=9,frameon=True)
fig.text(.04,.018,'Lower is better on both axes. Loss = log loss or RMSE. Highlighting includes five additional cost conditions; not certified Pareto dominance.',fontsize=8.2,color='#586C7C');fig.subplots_adjust(left=.15,right=.97,top=.83,bottom=.17);save(fig,'quality_resource')

fig,ax=plt.subplots(figsize=(11,5.6));title(fig,'Technical 2.2.0 request paths','Three synthetic fixtures • separate measurements, not fresh comparative training')
t=rows('technical_paths.csv');x=np.arange(len(t));w=.24
for j,(key,label,color) in enumerate([('combined_vs_three_calls','Combined / 3 separate 2.1 calls','#267D92'),('combined_vs_fused','Combined / efficient fused 2.1','#BA8A54'),('prepared_vs_fused','Prepared repeat / fused 2.1','#51916D')]):ax.bar(x+(j-1)*w,[float(r[key]) for r in t],width=w,label=label,color=color)
ax.axhline(1,color='#748595',ls='--');ax.set_xticks(x,[r['task']+'\nB'+r['batch'] for r in t],fontsize=8);ax.set_ylabel('Latency ratio (lower is better)');ax.set_ylim(0,1.25);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.15),ncol=3,fontsize=8.5,frameon=False);fig.subplots_adjust(left=.09,right=.98,top=.83,bottom=.25);save(fig,'technical_paths')

fig,ax=plt.subplots(figsize=(10,6.4));title(fig,'Optional snapshot compression','14 archived models • serialized byte ratio and observed load-time ratio')
c=rows('compression.csv');y=np.arange(len(c));ax.barh(y,[float(r['byte_ratio']) for r in c],color='#267D92',height=.63,label='Compressed / raw bytes');ax.scatter([float(r['load_ratio']) for r in c],y,marker='D',s=30,color='#C18A36',label='Compressed / raw load time');ax.axvline(1,color='#748595',ls='--');ax.set_yticks(y,[r['dataset'] for r in c],fontsize=9);ax.invert_yaxis();ax.set_xlabel('Ratio (lower is better)');ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);ax.legend(loc='lower right',frameon=False,fontsize=9);fig.subplots_adjust(left=.29,right=.96,top=.84,bottom=.12);save(fig,'compression')
fig,ax=plt.subplots(figsize=(9,5.4));title(fig,'Separate serving and trace companion','Three synthetic schemas • standalone component not bundled with this source archive')
s=rows('serving_trace.csv');x=np.arange(len(s));w=.25
for j,(k,label,color) in enumerate([('predict_us','Predict','#267D92'),('full_trace_us','Full trace','#A0ACB8'),('compact_trace_us','Compact trace','#C18A36')]):ax.bar(x+(j-1)*w,[float(r[k]) for r in s],width=w,label=label,color=color)
ax.set_xticks(x,[r['task'].title() for r in s]);ax.set_ylabel('Median single-row time (μs)');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True);ax.legend(frameon=False);fig.subplots_adjust(left=.11,right=.96,top=.82,bottom=.12);save(fig,'serving_trace')
