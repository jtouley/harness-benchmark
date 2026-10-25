| Run | Tree | recorded stream_ok | gate stream verdict (after build) | match | fresh clone, run first | output check |
|---|---|---|---|---|---|---|
| P1-core-4 | 02b11a068ccd | False | FAIL: `make stream DURATION=400`: it connected 70 times with one Last-Event-ID and did not get past that position (71 connections, 17322 event frames). Each record th | yes | FAIL: `make stream DURATION=400` (in a fresh clone, run first): it connected 69 times with one Last-Event-ID and did not get past that position (7 | PASS |
| P1-core-5 | 6074d8954823 | False | FAIL: `make stream DURATION=400`: it connected 15 times with one Last-Event-ID and did not get past that position (16 connections, 16143 event frames). Each record th | yes | FAIL: `make stream DURATION=400` (in a fresh clone, run first): it connected 14 times with one Last-Event-ID and did not get past that position (1 | PASS |
| P1-core-6 | 998515aa1ef2 | True | PASS | yes | FAIL: `make stream DURATION=400` (in a fresh clone, run first): it exited 2; `make stream DURATION=400` (in a fresh clone, run first): the output  | PASS |
| P1-full-4 | c63c13f93c1e | False | FAIL: `make stream DURATION=400`: it connected 355 times with one Last-Event-ID and did not get past that position (356 connections, 23195 event frames). Each record  | yes | FAIL: `make stream DURATION=400` (in a fresh clone, run first): it connected 355 times with one Last-Event-ID and did not get past that position ( | PASS |
| P1-full-6 | 869bb81ce0b3 | True | PASS | yes | PASS | PASS |
| P2-core-4 | aa9a497ffcc9 | False | FAIL: `make stream DURATION=400`: it exited 2; `make stream DURATION=400`: it printed a Python traceback; `make stream DURATION=400`: it did not read to the end of it | yes | FAIL: `make stream DURATION=400` (in a fresh clone, run first): it exited 2; `make stream DURATION=400` (in a fresh clone, run first): it printed  | PASS |
| P2-core-5 | 1009b9a42790 | False | FAIL: `make stream DURATION=400`: it connected 16 times with one Last-Event-ID and did not get past that position (17 connections, 16161 event frames). Each record th | yes | FAIL: `make stream DURATION=400` (in a fresh clone, run first): it exited 2; `make stream DURATION=400` (in a fresh clone, run first): it read no  | PASS |
| P2-core-6 | 85fa612b8dc7 | True | PASS | yes | FAIL: `make stream DURATION=400` (in a fresh clone, run first): it exited 2 | PASS |
| P2-full-4 | e30c0cef38af | False | FAIL: `make stream DURATION=400`: it exited 2; `make stream DURATION=400`: it printed a Python traceback; `make stream DURATION=400`: it did not read to the end of it | yes | FAIL: `make stream DURATION=400` (in a fresh clone, run first): it exited 2; `make stream DURATION=400` (in a fresh clone, run first): it printed  | PASS |
| P2-full-5 | eafecd8cbeb7 | True | PASS | yes | PASS | PASS |
| P2-full-6 | 9ed8cdd0926e | True | PASS | yes | PASS | PASS |

stream verdict matches stream_ok on 11 of 11
