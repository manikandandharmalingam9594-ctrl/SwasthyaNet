import subprocess
import time
import urllib.request
import sys

proc = subprocess.Popen([r".\venv\Scripts\uvicorn.exe", "main:app", "--port", "8000"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(6)
try:
    print("Testing /api/districts...")
    req = urllib.request.Request("http://127.0.0.1:8000/api/districts")
    res = urllib.request.urlopen(req)
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Response:", e.read().decode('utf-8'))
except Exception as e:
    print("Error:", str(e))
finally:
    proc.kill()
    out, _ = proc.communicate()
    print("Server output:\n", out.decode('utf-8'))
