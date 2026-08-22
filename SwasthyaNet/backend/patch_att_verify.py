with open("verify.py", "r") as f:
    verify_code = f.read()

verify_code = verify_code.replace('"attendance_date": "2026-08-16"', '"attendance_date": "2026-08-17"')

with open("verify.py", "w") as f:
    f.write(verify_code)
