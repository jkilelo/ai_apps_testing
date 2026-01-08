import requests
import json

def test_ui_automator():
    url = "http://localhost:8000/run-ui-automator"
    data = {"instruction": "Plan a trip to Tokyo"}
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ui_automator()
