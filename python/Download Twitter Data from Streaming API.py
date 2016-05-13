
# coding: utf-8

# In[1]:

import tweepy
from time import time
import pandas as pd
import os,sys
import json

time_between_save=60*10  # 10 minutes
save_fname='../data/test_data.json'


# In[2]:

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener


# In[3]:

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
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.total_seconds()
    


# In[5]:

get_ipython().magic(u'pinfo json.dump')


# In[ ]:



