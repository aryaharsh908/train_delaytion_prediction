import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.simulation.orchestrator import SimulationOrchestrator
from app.api import trains, simulation, events, network, model, websocket, historical, ml_retrain, health, counterfactual
from app.db.init_db import init_db
from app.db.database import SessionLocal
from app.services.historical_collector import ResumableHistoricalCollector

orchestrator = SimulationOrchestrator()

trains.set_orchestrator(orchestrator)
simulation.set_orchestrator(orchestrator)
events.set_orchestrator(orchestrator)
network.set_orchestrator(orchestrator)
websocket.set_orchestrator(orchestrator)
counterfactual.set_orchestrator(orchestrator)
ml_retrain.set_orchestrator(orchestrator)

simulation_task = None

async def simulation_loop():
    while True:
        try:
            orchestrator.tick_simulation(delta_real_seconds=1.0)
            await websocket.broadcast_state()
        except Exception as e:
            print(f"Error in simulation loop: {e}")
        await asyncio.sleep(1.0)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulation_task
    print("Initializing SIH26028 Dynamic Train ETA Forecast System...")
    init_db()
    
    # Cleanup any zombie running background collection jobs
    db = SessionLocal()
    try:
        ResumableHistoricalCollector.cleanup_zombie_jobs(db)
    finally:
        db.close()

    # Train/load active ML model on startup
    orchestrator.eta_predictor.load_or_train()
    
    # Start simulation loop task
    simulation_task = asyncio.create_task(simulation_loop())
    yield
    print("Shutting down simulation loop...")
    if simulation_task:
        simulation_task.cancel()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trains.router, prefix=settings.API_V1_STR)
app.include_router(simulation.router, prefix=settings.API_V1_STR)
app.include_router(events.router, prefix=settings.API_V1_STR)
app.include_router(network.router, prefix=settings.API_V1_STR)
app.include_router(model.router, prefix=settings.API_V1_STR)
app.include_router(historical.router, prefix=settings.API_V1_STR)
app.include_router(ml_retrain.router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(counterfactual.router, prefix=settings.API_V1_STR)
app.include_router(websocket.router)

@app.get("/")
def root():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
