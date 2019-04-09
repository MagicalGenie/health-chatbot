import requests
import json

host = "http://localhost:5000/tensorsearch"

search_term = input("Input search term: ")
request = {
    "search_terms": [
        search_term
    ]
}
res = requests.post(host, json=request)

print(json.loads(res.json())[search_term][0][0])
