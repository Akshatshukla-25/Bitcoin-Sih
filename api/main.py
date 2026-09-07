from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from api.data_loader import ArtifactLoadError, load_data_bundle
from api.routers import overview, alerts, cases, network, models, evaluation

app = FastAPI(
    title="SIH26146 NTRO Bitcoin AML Forensic API",
    description="Offline Air-Gapped Forensic Intelligence API for Bitcoin Transaction Traffic Monitoring",
    version="1.0.0"
)

# CORS configuration for local Next.js dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.exception_handler(ArtifactLoadError)
def handle_artifact_error(_request: Request, exc: ArtifactLoadError):
    return JSONResponse(status_code=503, content={"detail": str(exc), "status": "not_ready"})


# Register all tab routers
app.include_router(overview.router)
app.include_router(alerts.router)
app.include_router(cases.router)
app.include_router(network.router)
app.include_router(models.router)
app.include_router(evaluation.router)

@app.get("/api/health")
def health_check():
    data = load_data_bundle()
    return {
        "status": "ready",
        "system": "SIH26146 NTRO Forensic Engine",
        "mode": "Offline local artifact serving",
        "version": "1.0.0",
        "entities": len(data["scored_df"]),
        "transactions": len(data["transactions"]),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
