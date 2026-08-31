import uvicorn
from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title="Todo App API",
    version="0.1.0",
)

@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "data": settings.database.host,
    }

if __name__ == "__main__":
    uvicorn.run(
        app="app.main:app", 
        host="127.0.0.1", 
        port=8000, 
        reload=True
    )