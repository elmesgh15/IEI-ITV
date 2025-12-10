"""
Script para ejecutar el servidor FastAPI de forma independiente.
Útil para desarrollo y pruebas.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,  # Auto-reload en desarrollo
        log_level="info"
    )
