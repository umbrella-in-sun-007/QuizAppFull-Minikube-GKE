# GCP Insights & Status Report
Generated on: Tuesday 02 December 2025 05:27:39 PM IST

## 1. Cloud SQL Status
```
ipAddresses:
- ipAddress: 35.223.142.162
  type: PRIMARY
- ipAddress: 34.68.216.37
  type: OUTGOING
settings:
  dataDiskSizeGb: '10'
  tier: db-custom-2-7680
state: RUNNABLE
```

## 2. GKE Cluster Status
```
NAME             LOCATION     STATUS   CURRENT_NODE_COUNT
quizapp-cluster  us-central1  RUNNING  3
```

## 3. Cloud Storage Buckets
```
NAME                                 LOCATION     STORAGE_CLASS
data-rainfall-476920-v0-sql-backups  US-CENTRAL1
quizapp-media-476920                 US-CENTRAL1
```

## 4. Recent Error Logs (Last 20)
```
TIMESTAMP                       SEVERITY  TEXT_PAYLOAD                                                                                          MESSAGE
2025-12-02T11:35:59.309855051Z  ERROR     [2025-12-02 11:35:59 +0000] [388] [INFO] Booting worker with pid: 388
2025-12-02T11:35:58.152397890Z  ERROR     [2025-12-02 17:05:58 +0530] [354] [INFO] Worker exiting (pid: 354)
2025-12-02T11:35:57.145632249Z  ERROR     [2025-12-02 17:05:57 +0530] [354] [INFO] Autorestarting worker after current request.
2025-12-02T11:35:51.064533360Z  ERROR     [2025-12-02 11:35:51 +0000] [378] [INFO] Booting worker with pid: 378
2025-12-02T11:35:51.052034551Z  ERROR     [2025-12-02 11:35:51 +0000] [8] [WARNING] Worker with pid 367 was terminated due to signal 9
2025-12-02T11:35:50.041153422Z  ERROR     SystemExit: 1
2025-12-02T11:35:50.040782664Z  ERROR         sys.exit(1)
2025-12-02T11:35:50.040302187Z  ERROR       File "/usr/local/lib/python3.12/site-packages/gunicorn/workers/base.py", line 203, in handle_abort
2025-12-02T11:35:50.040292630Z  ERROR            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
2025-12-02T11:35:50.034692517Z  ERROR     Traceback (most recent call last):
                                            File "/usr/local/lib/python3.12/threading.py", line 1594, in _shutdown
                                              atexit_call()
                                            File "/usr/local/lib/python3.12/concurrent/futures/thread.py", line 31, in _python_exit
                                              t.join()
                                            File "/usr/local/lib/python3.12/threading.py", line 1149, in join
                                              self._wait_for_tstate_lock()
                                            File "/usr/local/lib/python3.12/threading.py", line 1169, in _wait_for_tstate_lock
                                              if lock.acquire(block, timeout):
2025-12-02T11:35:50.034279667Z  ERROR     Exception ignored in: <module 'threading' from '/usr/local/lib/python3.12/threading.py'>
2025-12-02T11:35:50.032754602Z  ERROR     [2025-12-02 11:35:50 +0000] [8] [CRITICAL] WORKER TIMEOUT (pid:367)
2025-12-02T11:35:20.049796711Z  ERROR     [2025-12-02 17:05:20 +0530] [367] [INFO] Worker exiting (pid: 367)
2025-12-02T11:34:49.542308067Z  ERROR     [2025-12-02 17:04:49 +0530] [367] [INFO] Autorestarting worker after current request.
2025-12-02T11:29:23.907104585Z  ERROR     [2025-12-02 11:29:23 +0000] [43] [INFO] Booting worker with pid: 43
2025-12-02T11:29:22.976639758Z  ERROR     [2025-12-02 16:59:22 +0530] [8] [INFO] Worker exiting (pid: 8)
2025-12-02T11:29:22.953189189Z  ERROR     [2025-12-02 16:59:22 +0530] [8] [INFO] Autorestarting worker after current request.
2025-12-02T11:21:13.883085351Z  ERROR     [2025-12-02 11:21:13 +0000] [31] [INFO] Booting worker with pid: 31
2025-12-02T11:21:12.947210365Z  ERROR     [2025-12-02 16:51:12 +0530] [9] [INFO] Worker exiting (pid: 9)
2025-12-02T11:21:12.510136820Z  ERROR     [2025-12-02 16:51:12 +0530] [9] [INFO] Autorestarting worker after current request.
```
