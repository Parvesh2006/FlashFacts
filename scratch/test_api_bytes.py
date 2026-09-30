import urllib.request, json
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/ask', 
                             data=b'{"question": "Give me important TNPSC Group 4 current affairs"}', 
                             headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    body = response.read()
    text = body.decode('utf-8', errors='replace')
    idx = text.find('TNPSC')
    print('Raw bytes around TNPSC:', body[idx-10:idx+30])
    print('Decoded text around TNPSC:', text[idx-10:idx+30])
