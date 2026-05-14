from fastapi import FastAPI

from app.database import Base, engine

from app.routes.vendor_routes import router as vendor_router
from app.routes.bill_routes import router as bill_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Kanani Fabrication Works API"
)


@app.get("/")
def home():
    return {
        "message": "Kanani Fabrication Works FastAPI Running"
    }


app.include_router(vendor_router)
app.include_router(bill_router)