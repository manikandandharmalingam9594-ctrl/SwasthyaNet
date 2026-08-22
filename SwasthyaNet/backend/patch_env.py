import os
env_file = ".env"
if not os.path.exists(env_file):
    with open(env_file, "w") as f:
        pass
with open(env_file, "r") as f:
    content = f.read()
if "JWT_SECRET" not in content:
    with open(env_file, "a") as f:
        f.write('\nJWT_SECRET="supersecretjwtkey123"\n')
        print("Added JWT_SECRET to .env")
