import http.client, json, time, collections, sys, pickle
conn=http.client.HTTPConnection('localhost',8099,timeout=10)
conn.request('GET','/v2/stream/recentchange',headers={'Accept':'text/event-stream'})
r=conn.getresponse()
evs=[]; data=[]; t0=time.time(); bad=0
while time.time()-t0<200:
    try: line=r.readline()
    except Exception as e: print('exc',e); break
    if not line: print('EOF'); break
    line=line.decode().rstrip('\r\n')
    if line=='':
        if data:
            try: evs.append(json.loads('\n'.join(data)))
            except ValueError: bad+=1
        data=[]
    elif line.startswith('data:'): data.append(line[5:].lstrip(' '))
print('events',len(evs),'bad',bad,'secs',time.time()-t0)
pickle.dump(evs,open('replay.pkl','wb'))
