import json, urllib.request
payload={'content':'<h1>title</h1><title>title</title><meta name= description content=desc>'}
req=urllib.request.Request('http://127.0.0.1:8000/api/audit', data=json.dumps(payload).encode('utf-8'), headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req) as res:
    print(res.status)
    print(res.read().decode('utf-8'))
