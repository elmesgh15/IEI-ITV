import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.wrappers.wrapper_cat import router as cat_router

app = FastAPI(title="API Wrapper Cataluña", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cat_router, prefix="/api/wrapper/cat", tags=["wrapper-catalunya"])

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8003)
