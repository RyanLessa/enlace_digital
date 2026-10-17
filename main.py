from fastapi import FastAPI

from enlace_digital.drivers.routes import router

app = FastAPI()
app.include_router(prefix="/v1", router=router)

@app.get("/")
def read_root():
    return {"Hello": "World"}
