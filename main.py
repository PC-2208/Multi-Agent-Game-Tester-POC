from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import os
from agents.ranker_agent import RankerAgent
from planner import generate_plan
from orchestrator import OrchestratorAgent

app = FastAPI()

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")

@app.get("/plan")
def get_plan():
    """Generate 20+ candidate test cases using the planner"""
    test_cases = generate_plan(20)
    return {"candidates": test_cases, "count": len(test_cases)}

@app.get("/rank")
def rank_plan():
    """Rank test cases and select top 10"""
    test_cases = generate_plan(20)
    
    ranker = RankerAgent()
    top_10 = ranker.rank_test_cases(test_cases, top_n=10)

    return {"top_10": top_10, "total_candidates": len(test_cases)}

@app.post("/execute")
async def execute_tests():
    """Execute the top 10 ranked test cases with multiple agents"""
    try:
        # Generate and rank test cases
        test_cases = generate_plan(20)
        ranker = RankerAgent()
        top_10 = ranker.rank_test_cases(test_cases, top_n=10)
        
        # Execute tests using orchestrator
        orchestrator = OrchestratorAgent(max_concurrent_executors=3)
        run_id = await orchestrator.run_tests_async(top_10)
        
        return {
            "message": "Test execution completed",
            "run_id": run_id,
            "tests_executed": len(top_10),
            "report_url": f"/reports/{run_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{run_id}")
def get_report(run_id: str):
    """Get test execution report"""
    report_path = f"runs/{run_id}/report.json"
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(report_path, media_type="application/json")

@app.get("/reports")
def list_reports():
    """List all available test reports"""
    if not os.path.exists("runs"):
        return {"reports": []}
    
    reports = []
    for run_dir in os.listdir("runs"):
        report_path = os.path.join("runs", run_dir, "report.json")
        if os.path.exists(report_path):
            reports.append({
                "run_id": run_dir,
                "report_path": report_path
            })
    
    return {"reports": reports}
