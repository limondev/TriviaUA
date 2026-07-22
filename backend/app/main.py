from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.game_ws import router as game_ws_router  # Імпортуємо
from app.core.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
app = FastAPI(title="TriviaUA API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для розробки дозволяємо запити з будь-яких джерел
    allow_credentials=True,
    allow_methods=["*"],  # Дозволяємо всі методи (POST, GET, OPTIONS тощо)
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(game_ws_router)

@app.get("/")
async def root():
    return {"message": "Ласкаво просимо до TriviaUA API!"}