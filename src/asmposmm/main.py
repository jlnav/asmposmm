from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uuid

from gest_api.vocs import VOCS
from libensemble.gen_classes.aposmm import APOSMM

app = FastAPI(title="ASMPOSMM", description="As-a-Service Module for Parallel Optimization to Solve Multiple Minima")

sessions: Dict[str, APOSMM] = {}

class VOCSModel(BaseModel):
    variables: Dict[str, List[float]]
    objectives: Dict[str, str]

class InitializeRequest(BaseModel):
    VOCS: VOCSModel
    max_active_runs: int
    initial_sample_size: int
    sample_points: Optional[int] = None
    localopt_method: Optional[str] = "scipy_Nelder-Mead"
    rk_const: Optional[float] = None
    xtol_abs: Optional[float] = 1e-6
    ftol_abs: Optional[float] = 1e-6
    mu: Optional[float] = 0.1
    nu: Optional[float] = 0.1
    dist_to_bound_multiple: Optional[float] = 0.1

class SuggestRequest(BaseModel):
    session_id: str
    num_points: int

class IngestRequest(BaseModel):
    session_id: str
    results: List[Dict[str, Any]]

class SessionRequest(BaseModel):
    session_id: str

def clean_and_convert(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    import numpy as np
    import math
    cleaned = []
    for item in data_list:
        new_item = {}
        for k, v in item.items():
            if k.endswith("_on_cube"):
                continue
            if isinstance(v, np.ndarray):
                v_list = v.tolist()
                # Assuming 1D array for simplicity based on APOSMM history
                new_item[k] = [None if isinstance(x, float) and (math.isinf(x) or math.isnan(x)) else x for x in v_list]
            elif isinstance(v, np.generic):
                v_item = v.item()
                if isinstance(v_item, float) and (math.isinf(v_item) or math.isnan(v_item)):
                    new_item[k] = None
                else:
                    new_item[k] = v_item
            else:
                if isinstance(v, float) and (math.isinf(v) or math.isnan(v)):
                    new_item[k] = None
                else:
                    new_item[k] = v
        cleaned.append(new_item)
    return cleaned

@app.get("/")
async def root():
    return {"message": "ASMPOSMM is running. There are {} sessions.".format(len(sessions))}

@app.post("/initialize")
async def initialize(req: InitializeRequest):
    session_id = str(uuid.uuid4())
    
    # Construct VOCS with on_cube variables
    vocs_dict = {
        "variables": req.VOCS.variables.copy(),
        "objectives": req.VOCS.objectives.copy()
    }
    
    for var_name in req.VOCS.variables.keys():
        vocs_dict["variables"][f"{var_name}_on_cube"] = [0.0, 1.0]
        
    vocs = VOCS(**vocs_dict)
    
    variables_mapping = {
        "x": list(req.VOCS.variables.keys()),
        "x_on_cube": [f"{v}_on_cube" for v in req.VOCS.variables.keys()],
        "f": list(req.VOCS.objectives.keys())
    }
    
    try:
        gen = APOSMM(
            vocs=vocs,
            max_active_runs=req.max_active_runs,
            initial_sample_size=req.initial_sample_size,
            variables_mapping=variables_mapping,
            localopt_method=req.localopt_method,
            rk_const=req.rk_const,
            xtol_abs=req.xtol_abs,
            ftol_abs=req.ftol_abs,
            mu=req.mu,
            nu=req.nu,
            dist_to_bound_multiple=req.dist_to_bound_multiple
        )
        sessions[session_id] = gen
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to initialize APOSMM: {str(e)}")
        
    return {
        "status": "success",
        "message": "Initialization successful",
        "session_id": session_id
    }

@app.post("/suggest")
async def suggest(req: SuggestRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    gen = sessions[req.session_id]
    try:
        suggestions = gen.suggest(req.num_points)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")
        
    return {
        "status": "success",
        "message": "Suggestions generated successfully",
        "suggestions": clean_and_convert(suggestions)
    }

@app.post("/ingest")
async def ingest(req: IngestRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    gen = sessions[req.session_id]
    
    # Pre-process results to add *_on_cube variables
    for res in req.results:
        for var_name, var_obj in gen.vocs.variables.items():
            if var_name.endswith("_on_cube"):
                continue
            if var_name in res:
                val = res[var_name]
                lb, ub = var_obj.domain[0], var_obj.domain[1]
                if isinstance(val, list):
                    res[f"{var_name}_on_cube"] = [(v - lb) / (ub - lb) for v in val]
                else:
                    res[f"{var_name}_on_cube"] = (val - lb) / (ub - lb)
                    
    try:
        gen.ingest(req.results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest results: {str(e)}")
        
    return {
        "status": "success",
        "message": "Results ingested successfully"
    }

@app.post("/finalize")
async def finalize(req: SessionRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    gen = sessions[req.session_id]
    try:
        gen.finalize()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finalize session: {str(e)}")
        
    return {
        "status": "success",
        "message": "Session finalized successfully"
    }

@app.post("/export")
async def export(req: SessionRequest):
    if req.session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    gen = sessions[req.session_id]
    try:
        from libensemble.utils.misc import np_to_list_dicts
        local_H_array, _, _ = gen.export(vocs_field_names=True, as_dicts=False)
        if local_H_array is None:
            local_H = []
        else:
            local_H = np_to_list_dicts(local_H_array)
            
        minima = [h for h in local_H if h.get("local_min", False)]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export results: {str(e)}")
        
    return {
        "status": "success",
        "message": "Results exported successfully",
        "minima": clean_and_convert(minima),
        "history": clean_and_convert(local_H)
    }
