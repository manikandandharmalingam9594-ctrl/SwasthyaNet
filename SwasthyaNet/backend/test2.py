import subprocess
import time
import urllib.request

proc = subprocess.Popen([r".\venv\Scripts\uvicorn.exe", "main:app", "--port", "8001"])
time.sleep(5)
try:
    res = urllib.request.urlopen("http://127.0.0.1:8001/api/districts").read()
    print("Success:", res)
except Exception as e:
    print("Error:", e)
finally:
    proc.kill()
