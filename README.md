ASMPOSMM
--------

(awesome-opossum)
As-a-Service Module for Parallel Optimization to Solve Multiple Minima

json fields
-----------

- VOCS:
    - variables: dict
        Keys: str
        Values: list of floats [min, max]
    - objectives: dict
        Keys: str
        Values: str ("minimize" or "maximize")
- max_active_runs: int
- initial_sample_size: int
- sample_points: int
- localopt_method: str
- rk_const: float
- xtol_abs: float
- ftol_abs: float
- mu: float
- nu: float
- dist_to_bound_multiple: float

API methods:
----------
- /initialize
    POST
    {
        "VOCS": {
            "variables": { "x": [-3, 3], "y": [-2, 2] },
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
    Response:
    {
        "status": "success",
        "message": "Initialization successful"
        "session_id": "<uuid>"
    }
- /suggest
    GET
    {
        "session_id": "<uuid>",
        "num_points": 2
    }
    Response:
    {
        "status": "success",
        "message": "Suggestions generated successfully"
        "suggestions": [
            { "x": [0.1, 0.2], "y": [0.3, 0.4], "_id": 0 },
            { "x": [0.5, 0.6], "y": [0.7, 0.8], "_id": 1 }
        ]
    }
- /ingest
    POST
    {
        "session_id": "<uuid>",
        "results": [
            { "x": [0.1, 0.2], "y": [0.3, 0.4], "_id": 0, "f": [0.1] },
            { "x": [0.5, 0.6], "y": [0.7, 0.8], "_id": 1, "f": [0.2] }
        ]
    }
    Response:
    {
        "status": "success",
        "message": "Results ingested successfully"
    }
- /finalize
    POST
    {
        "session_id": "<uuid>"
    }
    Response:
    {
        "status": "success",
        "message": "Session finalized successfully"
    }
- /export
    POST
    {
        "session_id": "<uuid>"
    }
    Response:
    {
        "status": "success",
        "message": "Results exported successfully"
        "minima": [
            { "x": [0.1, 0.2], "f": [0.1] },
        ]
        "history": [
            {"_id": 0, "x": [0.1, 0.2], "y": [0.3, 0.4], "f": [0.1]},
            {"_id": 1, "x": [0.5, 0.6], "y": [0.7, 0.8], "f": [0.2]}
        ]
    }