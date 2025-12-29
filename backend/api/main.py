from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from zombie import router as zombie_router
from rightsizing import router as rightsizing_router
from compliance import router as compliance_router
from history import router as history_router
from insights import router as insights_router
from resolutions import router as resolutions_router
from postmortem_api import router as postmortem_router
from test_redaction_endpoint import router as test_router

app = FastAPI(
    title="CloudSense API",
    description="Unified AWS Cost Optimization Platform",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(zombie_router)
app.include_router(rightsizing_router)
app.include_router(compliance_router)
app.include_router(history_router)
app.include_router(insights_router)
app.include_router(resolutions_router)
app.include_router(postmortem_router)
app.include_router(test_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to CloudSense API",
        "services": [
            "Zombie Resource Hunter",
            "Right-Sizing Recommendation Engine",
            "Compliance-as-Code Validator",
            "Post-Mortem Generator"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
