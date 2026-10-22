# from contextlib import asynccontextmanager

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware

# from app.api.chat import router as chat_router

# from sqlalchemy import text
# from app.database import engine
# from app.models import init_database
# from rag.reranker import get_reranker


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     init_database()

#     # Load the reranker model before the first request.
#     get_reranker()
#     yield


# app = FastAPI(
#     title="KLOC AI",
#     description="AI-powered KLOC knowledge and business assistant",
#     version="0.1.0",
#     lifespan=lifespan,
# )


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "http://localhost:3000",
#         "http://127.0.0.1:3000",
#         "http://localhost:3001",
#         "http://127.0.0.1:3001",
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



# app.include_router(chat_router)


# @app.get("/")
# def root():
#     return {"message": "KLOC AI backend is running"}


# @app.get("/health")
# def health():
#     return {"status": "healthy"}


# @app.get("/db-test")
# def database_test():
#     with engine.connect() as connection:
#         result = connection.execute(text("SELECT version();"))
#         version = result.scalar()

#     return {
#         "database": "connected",
#         "version": version,
#     }


# @app.get("/vector-test")
# def vector_test():
#     with engine.connect() as connection:
#         result = connection.execute(text("""
#             SELECT extname, extversion
#             FROM pg_extension
#             WHERE extname = 'vector';
#         """))

#         row = result.fetchone()

#     if row is None:
#         return {"vector": "not installed"}

#     return {
#         "extension": row[0],
#         "version": row[1],
#     }






from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.chat import router as chat_router
from app.database import engine
from app.models import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup.
    init_database()

    # Reranker loading is deferred to avoid consuming
    # additional memory during application startup.
    yield


app = FastAPI(
    title="KLOC AI",
    description="AI-powered KLOC knowledge and business assistant",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "https://kloc-chatboat-5mf3yj947-chows-projects-9a220fb0.vercel.app",
        "https://kloc-chatboat.vercel.app/"
        # Add your deployed Vercel frontend URL here.
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/")
def root():
    return {"message": "KLOC AI backend is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/db-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version();"))
        version = result.scalar()

    return {
        "database": "connected",
        "version": version,
    }


@app.get("/vector-test")
def vector_test():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT extname, extversion
                FROM pg_extension
                WHERE extname = 'vector';
            """)
        )
        row = result.fetchone()

    if row is None:
        return {"vector": "not installed"}

    return {
        "extension": row[0],
        "version": row[1],
    }
