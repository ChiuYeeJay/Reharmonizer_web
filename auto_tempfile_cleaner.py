import os
import time
import shutil

CHECK_INTERVAL = 10
REMOVAL_THRESH = 60

assert os.path.exists("tempfiles")
os.chdir("tempfiles")

f = open("cleaner_log.txt", "w")
f.close()

while True:
    print(f"cleaning!!!\t{time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime())}")
    f = open("cleaner_log.txt", "a")
    for item in os.listdir():
        if not os.path.isdir(item):
            continue
        if time.time()-os.path.getctime(item) >= REMOVAL_THRESH:
            shutil.rmtree(item)
            f.write(item + "\t" + time.strftime("%Y-%m-%d %H:%M:%S %z", time.localtime()) + "\n")
            f.flush()
    f.close()
    time.sleep(CHECK_INTERVAL)