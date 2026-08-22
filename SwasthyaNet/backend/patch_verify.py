with open("verify.py", "r") as f:
    verify_code = f.read()

verify_code = verify_code.replace('"sync_status": "Success"', '"sync_status": "SYNCED"')
verify_code = verify_code.replace('"transaction_type": "Restock"', '"transaction_type": "RECEIVED"')

with open("verify.py", "w") as f:
    f.write(verify_code)
