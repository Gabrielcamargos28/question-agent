import urllib.request
import json
import urllib.error

def run_test_payload(payload, description):
    print(f"--- Testing: {description} ---")
    url = 'http://localhost:8081/questao/criar-questao'
    headers = {'Content-Type': 'application/json'}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            print(f"Status: {response.status}")
            print(f"Response: {response.read().decode('utf-8')}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
    print("\n")

payload_int = {
    "corpo": "Teste",
    "alternativas": [],
    "alternativaCorreta": 0,
    "area": 6
}

payload_obj = {
    "corpo": "Teste",
    "alternativas": [],
    "alternativaCorreta": 0,
    "area": {"id": 6}
}

if __name__ == '__main__':
    run_test_payload(payload_int, "area as integer (current)")
    run_test_payload(payload_obj, "area as object {'id': 6}")
