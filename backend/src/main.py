from fastapi import FastAPI

from api.auth import router as auth_router

app = FastAPI(title="AI Learning Platform")

app.include_router(auth_router)


@app.get("/ping")
def ping():
    return {"status": "ok"}


