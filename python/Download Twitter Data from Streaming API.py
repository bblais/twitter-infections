
# coding: utf-8

# In[14]:

import tweepy
from time import time
import os,sys
import json
import gzip

time_between_save=60*10  # 10 minutes
save_fname='../data/raw_twitter_data.json.gz'


# In[15]:

from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener


# In[16]:

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
    


# Put your twitter authentication creds in a json file , like:
# 
#     {"csecret": "xxxxxxxx", "ckey": "xxxxxxxxxx", "asecret": "xxxxxxxxxx", "atoken": "xxxxxxxxxx"}

# In[17]:

with open('../../auth.json') as fid:
    auth_data=json.load(fid)
    
ckey,csecret,atoken,asecret=[auth_data[key]
                             for key in ['ckey','csecret','atoken','asecret']]    


# In[18]:

global mydata,last_save_time,start_time,onedata




if os.path.exists(save_fname):
    print "Starting with %s..." % save_fname
    
    try:
        with gzip.open(save_fname,'r') as fid:
            mcmc_data=json.load(fid)
    except IOError:
        with open(save_fname,'r') as fid:
            mcmc_data=json.load(fid)
else:
    print "Starting Fresh..."
    mydata={}
    
start_time=None
last_save_time=-1000


# In[ ]:

class listener(StreamListener):

    def on_data(self, data):
        global mydata,last_save_time,start_time,onedata
        
        false=False
        true=True
        null=None        
        data=eval(data)  # change json to dictionary
        
        try:
            timestr=data['created_at']
        except KeyError:
            return True
            
        hashtags=[x['text'] for x in data['entities']['hashtags']]
        
        onedata=data
        
        if not hashtags:
            return True

        with open("../data/raw_tweet_lines.txt","a") as fid:
            line="%s,%s,%s\n" % (timestr,str(data['geo']),str(hashtags))
            fid.write(line)
                      
        print line
        
        dt=to_datetime(timestr)
        dt = dt.replace(tzinfo=None)        
        dt=unix_time(dt)
            
        for tag in hashtags:
            if tag not in mydata:                
                mydata[tag]={'x':[],'y':[],}
        
            try:
                idx=mydata[tag]['x'].index(dt)
                mydata[tag]['y'][idx]+=1
            except ValueError:                
                mydata[tag]['x'].append(dt)
                mydata[tag]['y'].append(1)
        
            mydata[tag]['geo']=data['geo']
            
        print dt,data['geo'],hashtags
        
        if time()>(last_save_time+time_between_save):
            last_save_time=time()
            
            if '.gz' in save_fname:
                with gzip.open(save_fname,'w') as fid:
                    json.dump(mydata,fid)    
            else:
                with open(save_fname,'w') as fid:
                    json.dump(mydata,fid)
                    
            print "All data Saved..."
        
        return True

    def on_error(self, status):
        print "on_error called: ",status
        sys.stdout.flush()


def start_listening():
    L=listener()
    twitterStream = Stream(auth, L)
    twitterStream.filter(track=["#"])


# In[ ]:

auth = OAuthHandler(ckey, csecret)
auth.set_access_token(atoken, asecret)
start_listening()


# In[ ]:



