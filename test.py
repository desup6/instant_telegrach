from hashlib import md5
from time import time
start = time()
for x in range(1000000):
    a = md5(str(x).encode())

print(time()-start)
