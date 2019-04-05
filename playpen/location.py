import requests
import json

loc = requests.get("http://ipinfo.io")
print(loc.json()['city'])