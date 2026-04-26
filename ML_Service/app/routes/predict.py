from fastapi import APIRouter
from app.services.inference import run_prediction

router = APIRouter()

@router.get("/")
def predict():
    return {
        "success": True,
        "data": run_prediction()
    }