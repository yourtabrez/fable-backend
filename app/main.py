import os
from dotenv import load_dotenv

load_dotenv()  # must run before any app imports that read env vars

from fastapi import FastAPI
from app.routes.story_routes import router as story_router

app = FastAPI(title="Fable Backend", version="6.0")

app.include_router(story_router)


@app.get("/")
def root():
    return {"status": "Fable backend running 🚀", "version": "6.0"}


# Required for Cloud Run
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)