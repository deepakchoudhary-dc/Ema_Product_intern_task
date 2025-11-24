"""
FastAPI REST API for Claims Processing System
B2B Integration Endpoints
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import json
from pathlib import Path
from workflow import AutoInsuranceWorkflow, ClaimInfo, ClaimDecision, FNOLSummary, TriageDecision, FraudSignal
import uvicorn

app = FastAPI(
    title="Ema Agentic Claims API",
    description="B2B API for autonomous claims processing",
    version="1.0.0"
)

# Request/Response Models
class ClaimSubmissionRequest(BaseModel):
    claim_data: Dict[str, Any]
    use_agentic_mode: bool = True
    
class ClaimSubmissionResponse(BaseModel):
    claim_number: str
    status: str
    decision: Optional[Dict[str, Any]] = None
    fnol_summary: Optional[Dict[str, Any]] = None
    triage: Optional[Dict[str, Any]] = None
    fraud_signal: Optional[Dict[str, Any]] = None
    processing_time_ms: Optional[float] = None

class BatchClaimRequest(BaseModel):
    claims: List[Dict[str, Any]]
    use_agentic_mode: bool = True
    
class BatchClaimResponse(BaseModel):
    total_claims: int
    processed: int
    failed: int
    results: List[ClaimSubmissionResponse]

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    agentic_mode_available: bool

# In-memory storage for demo (replace with database in production)
processed_claims: Dict[str, Dict[str, Any]] = {}

def get_workflow(use_agentic: bool = True):
    """Initialize workflow with optional agentic mode"""
    import os
    llm = None
    if use_agentic and os.getenv("GEMINI_API_KEY"):
        from workflow import GeminiStructuredClient
        llm = GeminiStructuredClient(api_key=os.getenv("GEMINI_API_KEY"))
    
    return AutoInsuranceWorkflow(
        policy_retriever=None,
        llm=llm if llm and hasattr(llm, 'available') and llm.available else None,
        verbose=False,
        timeout=30.0
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import os
    return HealthResponse(
        status="healthy",
        service="Ema Agentic Claims API",
        version="1.0.0",
        agentic_mode_available=bool(os.getenv("GEMINI_API_KEY"))
    )

@app.post("/api/v1/claims/process", response_model=ClaimSubmissionResponse)
async def process_claim(request: ClaimSubmissionRequest):
    """Process a single claim through the agentic workflow"""
    import time
    start_time = time.time()
    
    try:
        # Validate claim data
        claim_info = ClaimInfo.model_validate(request.claim_data)
        
        # Create temp file for workflow
        temp_path = Path(f"/tmp/claim_{claim_info.claim_number}.json")
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(json.dumps(request.claim_data))
        
        # Run workflow
        workflow = get_workflow(request.use_agentic_mode)
        result = await workflow.run(claim_json_path=str(temp_path))
        
        # Clean up temp file
        temp_path.unlink(missing_ok=True)
        
        processing_time = (time.time() - start_time) * 1000
        
        # Store result
        processed_claims[claim_info.claim_number] = {
            "decision": result["decision"].model_dump() if result.get("decision") else None,
            "fnol_summary": result["fnol_summary"].model_dump() if result.get("fnol_summary") else None,
            "triage": result["triage"].model_dump() if result.get("triage") else None,
            "fraud_signal": result["fraud_signal"].model_dump() if result.get("fraud_signal") else None,
            "processing_time_ms": processing_time
        }
        
        return ClaimSubmissionResponse(
            claim_number=claim_info.claim_number,
            status="processed",
            decision=processed_claims[claim_info.claim_number]["decision"],
            fnol_summary=processed_claims[claim_info.claim_number]["fnol_summary"],
            triage=processed_claims[claim_info.claim_number]["triage"],
            fraud_signal=processed_claims[claim_info.claim_number]["fraud_signal"],
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing claim: {str(e)}")

@app.post("/api/v1/claims/batch", response_model=BatchClaimResponse)
async def process_batch(request: BatchClaimRequest):
    """Process multiple claims in parallel"""
    results = []
    processed = 0
    failed = 0
    
    # Process claims in parallel
    tasks = []
    for claim_data in request.claims:
        task = process_claim(ClaimSubmissionRequest(
            claim_data=claim_data,
            use_agentic_mode=request.use_agentic_mode
        ))
        tasks.append(task)
    
    # Gather results
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in batch_results:
        if isinstance(result, Exception):
            failed += 1
            results.append(ClaimSubmissionResponse(
                claim_number="UNKNOWN",
                status="failed"
            ))
        else:
            processed += 1
            results.append(result)
    
    return BatchClaimResponse(
        total_claims=len(request.claims),
        processed=processed,
        failed=failed,
        results=results
    )

@app.get("/api/v1/claims/{claim_number}")
async def get_claim_status(claim_number: str):
    """Retrieve processed claim result"""
    if claim_number not in processed_claims:
        raise HTTPException(status_code=404, detail=f"Claim {claim_number} not found")
    
    return JSONResponse(content=processed_claims[claim_number])

@app.get("/api/v1/claims")
async def list_claims(limit: int = 100, offset: int = 0):
    """List all processed claims"""
    claim_list = list(processed_claims.items())[offset:offset + limit]
    return JSONResponse(content={
        "total": len(processed_claims),
        "limit": limit,
        "offset": offset,
        "claims": [{"claim_number": k, **v} for k, v in claim_list]
    })

@app.post("/api/v1/claims/{claim_number}/override")
async def override_decision(claim_number: str, override_data: Dict[str, Any]):
    """Allow adjuster to override agent recommendation (Human-in-the-Loop)"""
    if claim_number not in processed_claims:
        raise HTTPException(status_code=404, detail=f"Claim {claim_number} not found")
    
    # Store override
    processed_claims[claim_number]["override"] = {
        "original_decision": processed_claims[claim_number]["decision"],
        "override_decision": override_data,
        "timestamp": time.time()
    }
    
    # Update decision
    processed_claims[claim_number]["decision"] = override_data
    processed_claims[claim_number]["decision"]["overridden"] = True
    
    return JSONResponse(content={
        "claim_number": claim_number,
        "status": "overridden",
        "decision": processed_claims[claim_number]["decision"]
    })

@app.get("/api/v1/metrics")
async def get_metrics():
    """Get processing metrics and KPIs"""
    if not processed_claims:
        return JSONResponse(content={
            "total_claims_processed": 0,
            "avg_processing_time_ms": 0,
            "fraud_referral_rate": 0,
            "coverage_approval_rate": 0
        })
    
    total = len(processed_claims)
    avg_time = sum(c.get("processing_time_ms", 0) for c in processed_claims.values()) / total
    
    fraud_referrals = sum(1 for c in processed_claims.values() 
                         if c.get("fraud_signal", {}).get("risk_score", 0) > 0.5)
    fraud_rate = (fraud_referrals / total) * 100 if total > 0 else 0
    
    approved = sum(1 for c in processed_claims.values() 
                  if c.get("decision", {}).get("covered", False))
    approval_rate = (approved / total) * 100 if total > 0 else 0
    
    return JSONResponse(content={
        "total_claims_processed": total,
        "avg_processing_time_ms": round(avg_time, 2),
        "fraud_referral_rate": round(fraud_rate, 2),
        "coverage_approval_rate": round(approval_rate, 2),
        "manual_overrides": sum(1 for c in processed_claims.values() if "override" in c)
    })

if __name__ == "__main__":
    import time
    uvicorn.run(app, host="0.0.0.0", port=8000)
