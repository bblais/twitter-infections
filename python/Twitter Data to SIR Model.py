
# coding: utf-8

# In[13]:

get_ipython().magic(u'pylab inline')


# In[14]:

from Waitbar import Waitbar
import os,sys
import pandas as pd
import gzip
import json


# In[15]:

from pyndamics import *
from pyndamics.emcee import *


# In[16]:

class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            if obj.ndim == 1:
                return obj.tolist()
            else:
                return [self.default(obj[i]) for i in range(obj.shape[0])]
        return json.JSONEncoder.default(self, obj)


# In[17]:

from pytz import timezone
from datetime import datetime,timedelta

def to_datetime(datestring,tzstr='utc'):
    created_at = datetime.strptime(datestring, '%a %b %d %H:%M:%S +0000 %Y')
    
    if 'utc' in tzstr.lower():
        tz = timezone('UTC')
        return tz.localize(created_at)

    if 'eastern' in tzstr.lower() or 'est'==tzstr.lower():
        tz = timezone('US/Eastern')
        return tz.localize(created_at)
    
def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()
    


# In[18]:

which_file='../data/saved_twitter_data_jskaza'
#which_file='saved_twitter_data_bblais'
if os.path.exists(which_file+".json"):  
    with open(which_file+".json",'r') as fid:
        mydata=json.load(fid)
elif os.path.exists(which_file+".json.gz"):  
    with gzip.open(which_file+".json.gz",'r') as fid:
        mydata=json.load(fid)        
else:
    raise ValueError,"only doing json this time"


# In[19]:

keys=mydata.keys()
L=[len(mydata[key]['x']) for key in keys]


# In[20]:

L,keys=zip(*sorted(zip(L,keys),reverse=True))
L[:10]


# In[21]:

max_t=None
min_t=None
for key in mydata:
    mx=max(mydata[key]['x'])
    mn=min(mydata[key]['x'])
    
    if max_t is None:
        max_t=mx
    elif max_t<mx:
        max_t=mx
        
        
    if min_t is None:
        min_t=mn
    elif min_t>mn:
        min_t=mn

# so we can use them as index vars
max_t=int(max_t)
min_t=int(min_t)


# In[22]:

time2str(max_t-min_t)


# In[23]:

window=60*2*100
min_count=5


# In[ ]:

save_fname='../data/mcmc_data_nyc_hours.json'
if os.path.exists(save_fname):  
    with open(save_fname,'r') as fid:
        mcmc_data=json.load(fid)
else:
    mcmc_data={}

if not which_file in mcmc_data:
    mcmc_data[which_file]={}
    

fit_data=mcmc_data[which_file]

n=16
nc=ceil(sqrt(n));
nr=ceil(n/nc);
count=0
for key in keys:
    
    if count%n==0:
        figure(figsize=(20,20))
    
    timeit(reset=True)
    
    if key in fit_data and 'posteriors' in fit_data[key]:
        count+=1
        print "Skipping ",key,"...already done."
        continue
        
    print "Doing Convolution on ",key,"..."
        
    y=array(mydata[key]['y'])
    t=array(mydata[key]['x'],dtype=int)
    t=t-min_t
    
    t_full=arange(0,max_t-min_t+1)
    y_full=zeros(len(t_full))
    y_full[t]=y    
    
    t,y=t_full,y_full
    
    yy=y
    tt=t
    
    yy=np.convolve(yy,ones(window),'same')
    if max(yy)<min_count:
        continue


    try:
        idx_zero_before_max=where(yy[:argmax(yy)]==0)[0][-1]
    except IndexError:  # no zero before min
        idx_zero_before_max=0
    
    try:
        idx_zero_after_max=where(yy[argmax(yy):]==0)[0][0]+argmax(yy)
    except IndexError:  # no zero after max
        idx_zero_after_max=len(yy)-1
        
    
    t1,t2=tt[idx_zero_before_max],tt[idx_zero_after_max]
        
        
    print "Doing MCMC on ",key,"..."
    
    t2=t2-t1
    t=tt-t1
    y=yy

    y=y[(t>0) & (t<t2)]
    t=t[(t>0) & (t<t2)]
    
    
    
    fit_data[key]={}
    fit_data[key]['t']=t
    fit_data[key]['y']=y
    

    S0=500.0  # not so huge initial population
    sim=Simulation()
    sim.add("S'=-beta*S/S0*I",S0,plot=False)
    sim.add("I'=beta*S/S0*I-gamma*I",1,plot=False)  # start with a small infection
    sim.add("R'=gamma*I",0,plot=False)
    sim.params(S0=S0, beta=1/400.0,gamma=1/600.0)
    sim.add_data(t=t,I=y,plot=False)   # offset the time of the increase
    sim.run(0,max(t)*2)
    
    model=MCMCModel(sim, 
                    beta=Uniform(0,.5),
                    gamma=Uniform(0,.5),
                    )
    model.verbose=False
    model.run_mcmc(500)
    model.set_initial_values('samples')
    model.run_mcmc(500)
    
    fit_data[key]['best_estimates']=model.best_estimates()    
    fit_data[key]['percentiles']=model.percentiles([2.5,50,97.5])  
    
    posteriors={}
    for paramkey in model.keys:
        b1,b2=model.percentiles([.5,99.5])[paramkey]
        bins=linspace(b1,b2,500)
        i=model.index[paramkey]
        x,px=histogram(model.samples[:,i],bins=bins,plot=False)    
        posteriors[paramkey]={'x':x,'px':px}
    fit_data[key]['posteriors']=posteriors
    
    subplot(nr,nc,(count%n)+1)
    I=sim['I']
    t=sim['t']
    Ic=sim.get_component('I')

    td=Ic.data['t']
    Id=Ic.data['value']

    plot(t,I,'-')
    plot(td,Id,'-o')    
    
    title(key[:40])
    
    with open(save_fname,'w') as fid:
        json.dump(mcmc_data,fid,cls=NumpyAwareJSONEncoder)    
    
    print timeit()
    
    count+=1


# In[ ]:



