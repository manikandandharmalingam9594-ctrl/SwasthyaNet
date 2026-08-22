import subprocess
import time
import urllib.request
import sys

proc = subprocess.Popen([r".\venv\Scripts\uvicorn.exe", "main:app", "--port", "8002"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(5)
try:
    res = urllib.request.urlopen("http://127.0.0.1:8002/api/districts").read()
except Exception as e:
    pass
finally:
    proc.kill()
    out, err = proc.communicate()
    print("STDOUT:\n", out.decode('utf-8'))
    print("STDERR:\n", err.decode('utf-8'))
