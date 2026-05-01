from fastapi.testclient import TestClient
from asmposmm.main import app

client = TestClient(app)

def test_api():
    print("Testing /initialize")
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
    res = client.post("/initialize", json=init_data)
    assert res.status_code == 200, f"Failed initialize: {res.text}"
    session_id = res.json()["session_id"]
    print(f"Session ID: {session_id}")

    print("Testing /suggest")
    suggest_data = {
        "session_id": session_id,
        "num_points": 2
    }
    res = client.post("/suggest", json=suggest_data)
    assert res.status_code == 200, f"Failed suggest: {res.text}"
    suggestions = res.json()["suggestions"]
    print("Suggestions:", suggestions)

    print("Testing /ingest")
    # Provide f values for the suggestions
    for i, s in enumerate(suggestions):
        s["f"] = float(i + 1) * 0.1
    
    ingest_data = {
        "session_id": session_id,
        "results": suggestions
    }
    res = client.post("/ingest", json=ingest_data)
    assert res.status_code == 200, f"Failed ingest: {res.text}"

    print("Testing /finalize")
    finalize_data = {
        "session_id": session_id
    }
    res = client.post("/finalize", json=finalize_data)
    assert res.status_code == 200, f"Failed finalize: {res.text}"

    print("Testing /export")
    export_data = {
        "session_id": session_id
    }
    res = client.post("/export", json=export_data)
    assert res.status_code == 200, f"Failed export: {res.text}"
    print("Export:", res.json())

    print("All tests passed!")

if __name__ == "__main__":
    test_api()
