from fastapi import FastAPI
from app.routes.predict import router as predict_router
from app.routes.health import router as health_router

app = FastAPI(title="ML Prediction Service")

app.include_router(predict_router, prefix="/predict")
app.include_router(health_router, prefix="/health")