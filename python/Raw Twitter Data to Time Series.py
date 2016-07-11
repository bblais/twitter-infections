
# coding: utf-8

# In[29]:

get_ipython().magic(u'pylab inline')


# In[30]:

from science import *
from Waitbar import Waitbar
import os,sys
import pandas as pd
import gzip
import json


# In[31]:

second=1
minute=60*second
hour=60*minute
day=24*hour


# In[32]:

class NumpyAwareJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            if obj.ndim == 1:
                return obj.tolist()
            else:
                return [self.default(obj[i]) for i in range(obj.shape[0])]
        return json.JSONEncoder.default(self, obj)


# In[33]:

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
    


# ## Load the Raw File

# In[34]:

#which_file='../data/raw_twitter_data'
which_file='../data/saved_twitter_data_jskaza'
if os.path.exists(which_file+".json"):  
    with open(which_file+".json",'r') as fid:
        data=json.load(fid)
elif os.path.exists(which_file+".json.gz"):  
    with gzip.open(which_file+".json.gz",'r') as fid:
        data=json.load(fid)        
else:
    raise ValueError,"only doing json this time"


# ## Sort

# In[35]:

keys=data.keys()
L=[len(data[key]['x']) for key in keys]
L,keys=zip(*sorted(zip(L,keys),reverse=True))
L[:10]


# In[36]:

data.keys()[:10]


# ## Find min/max times

# In[37]:

max_t=None
min_t=None
for key in data:
    mx=max(data[key]['x'])
    mn=min(data[key]['x'])
    
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


# In[38]:

time2str(max_t-min_t)


# ## Make some time series

# In[39]:

series_names=['time series days','time series minutes',
              'time series ten minutes','time series hours']


series=series_names[0]

if series=='time series days':
    window=day
elif series=='time series hours':
    window=hour
elif series=='time series minutes':
    window=minute
elif series=='time series ten minutes':
    window=10*minute
elif series=='time series ten seconds':
    window=second
else:
    raise ValueError,"window not found"
    
f=0.01


# ## Only do a subset for a demo?

# In[42]:

keys=keys[:5]


# In[43]:

n=16
nc=ceil(sqrt(n));
nr=ceil(n/nc);
count=0
all_series=[]

for key in keys:
    
    print "Doing Convolution on ",key,"..."
    
    
    for series in series_names:
        if series=='time series days':
            window=day
        elif series=='time series hours':
            window=hour
        elif series=='time series minutes':
            window=minute
        elif series=='time series ten minutes':
            window=10*minute
        else:
            raise ValueError,"window not found"
    

        y=array(data[key]['y'])
        t=array(data[key]['x'],dtype=int)

        t,y=array(t),array(y)

        t=t-min(t)

        t_full=arange(0,max(t)-min(t)+1)
        y_full=zeros(len(t_full))
        y_full[t]=y    


        t,y=t_full,y_full

        if len(y)<window:  # too short of a twitter activity
            continue


        yy=y/float(window)*float(hour)  # normalize to events per hour
        tt=t/float(window)

        if 'days' in series:
            tt=tt[::10]
            yy=yy[::10]
            yy=np.convolve(yy,ones(window/10),'same')
        else:
            yy=np.convolve(yy,ones(window),'same')

        
        try:
            idx_zero_before_max=where(yy[:argmax(yy)]==0)[0][-1]

            top=max(yy)
            idx_zero_before_max=where(yy[:argmax(yy)]<(f*top))[0][-1]
        except IndexError:  # no zero before min
            idx_zero_before_max=0

        try:
            idx_zero_after_max=where(yy[argmax(yy):]==0)[0][0]+argmax(yy)

            top=max(yy)
            idx_zero_after_max=where(yy[argmax(yy):]<(f*top))[0][0]+argmax(yy)
        except IndexError:  # no zero after max
            idx_zero_after_max=len(yy)-1


        t1,t2=tt[idx_zero_before_max],tt[idx_zero_after_max]

        t2=t2-t1
        t=tt-t1
        y=yy

        y=y[(t>0) & (t<t2)]
        t=t[(t>0) & (t<t2)]


        single_series={}
        single_series['filename']=which_file
        single_series['series']=series
        single_series['window']=window
        single_series['peak f']=f
        single_series['tag']=key
        single_series['t']=t
        single_series['y']=y

        all_series.append(single_series)

        
save_fname=which_file+"_subseries.json.gz"
print save_fname

with gzip.open(save_fname,'w') as fid:
    json.dump(all_series,fid,cls=NumpyAwareJSONEncoder)


# In[ ]:



