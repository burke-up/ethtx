import os
import requests

os.environ["http_proxy"] = "http://192.168.10.100:10809"
os.environ["https_proxy"] = "http://192.168.10.100:10809"

res = requests.get("http://ip.sb")
print(res)

