from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, enrollment, glyphs, generate

# In production, use Alembic migrations instead of create_all.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Handwriting Synthesis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # the Next.js frontend, dev origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(enrollment.router)
app.include_router(glyphs.router)
app.include_router(generate.router)


@app.get("/health")
def health():
    return {"status": "ok"}
