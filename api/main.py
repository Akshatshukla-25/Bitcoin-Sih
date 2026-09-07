from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Register all tab routers
app.include_router(overview.router)
app.include_router(alerts.router)
app.include_router(cases.router)
app.include_router(network.router)
app.include_router(models.router)
app.include_router(evaluation.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "system": "SIH26146 NTRO Forensic Engine",
        "mode": "100% Offline Air-Gapped",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="127.0.0.1", port=8000, reload=True)
