import sys, pathlib, time
sys.path.insert(0, sys.argv[1])
from pipeline.stream_consumer import StreamConsumer, read_column
lake = pathlib.Path(sys.argv[2]); dur=float(sys.argv[3]); n=int(sys.argv[4])
prev=-1
for i in range(n):
    StreamConsumer(lake_dir=lake, url="http://localhost:8099/v2/stream/recentchange", duration=dur).run()
    c=len(read_column(lake/"stream_raw","event_id"))
    print(i, c, flush=True)
    if c==prev: break
    prev=c
