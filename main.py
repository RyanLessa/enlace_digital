from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from enlace_digital.drivers.routes import router

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(prefix="/v1", router=router)


@app.get("/")
def read_root():
    return {"Hello": "World"}
