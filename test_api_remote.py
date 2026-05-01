import argparse
import urllib.request
import urllib.error
import json
import sys

def post_json(url, data):
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'), 
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.read().decode()}")
        sys.exit(1)

def get_json(url):
    try:
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Could not connect to {url}. Make sure the server is running. Error: {e.reason}")
        sys.exit(1)

def test_api(base_url):
    print(f"Connecting to API at {base_url}")
    
    # Check if root is running
    res = get_json(base_url)
    print("Root response:", res)

    print("\nTesting /initialize")
    init_data = {
        "VOCS": {
            "variables": { "x": [-3.0, 3.0], "y": [-2.0, 2.0] },
            "objectives": { "f": "minimize" }
        },
        "max_active_runs": 5,
        "initial_sample_size": 2,
        "sample_points": 10,
        "localopt_method": "scipy_Nelder-Mead",
        "rk_const": 0.1,
        "xtol_abs": 1e-6,
        "ftol_abs": 1e-6,
        "mu": 0.1,
        "nu": 0.1,
        "dist_to_bound_multiple": 0.1
    }
    res = post_json(f"{base_url}/initialize", init_data)
    assert res["status"] == "success", f"Failed initialize: {res}"
    session_id = res["session_id"]
    print(f"Session ID: {session_id}")

    print("\nTesting /suggest")
    suggest_data = {
        "session_id": session_id,
        "num_points": 2
    }
    res = post_json(f"{base_url}/suggest", suggest_data)
    assert res["status"] == "success", f"Failed suggest: {res}"
    suggestions = res["suggestions"]
    print("Suggestions:", suggestions)

    print("\nTesting /ingest")
    # Provide f values for the suggestions
    for i, s in enumerate(suggestions):
        s["f"] = float(i + 1) * 0.1
    
    ingest_data = {
        "session_id": session_id,
        "results": suggestions
    }
    res = post_json(f"{base_url}/ingest", ingest_data)
    assert res["status"] == "success", f"Failed ingest: {res}"

    print("\nTesting /finalize")
    finalize_data = {
        "session_id": session_id
    }
    res = post_json(f"{base_url}/finalize", finalize_data)
    assert res["status"] == "success", f"Failed finalize: {res}"

    print("\nTesting /export")
    export_data = {
        "session_id": session_id
    }
    res = post_json(f"{base_url}/export", export_data)
    assert res["status"] == "success", f"Failed export: {res}"
    print("Export:", res)

    print("\nAll tests passed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test ASMPOSMM API remotely")
    parser.add_argument("ip", help="IP address or hostname of the server (e.g. 192.168.1.100)")
    parser.add_argument("--port", type=int, default=8000, help="Port the server is running on")
    args = parser.parse_args()

    base_url = f"http://{args.ip}:{args.port}"
    test_api(base_url)
