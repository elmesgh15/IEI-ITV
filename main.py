# main.py
import sys
import threading
import time
from PySide6.QtWidgets import QApplication
from frontend.main_window import MainWindow

def iniciar_servidor():
    """Inicia el servidor FastAPI en un hilo separado"""
    import uvicorn
    from backend.server import app
    
    # Configuración del servidor
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    # Iniciar servidor FastAPI en un hilo separado
    server_thread = threading.Thread(target=iniciar_servidor, daemon=True)
    server_thread.start()
    
    # Esperar un momento para que el servidor se inicie
    print("Iniciando servidor FastAPI...")
    time.sleep(2)
    print("Servidor iniciado en http://127.0.0.1:8000")
    
    # Iniciar aplicación Qt
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())
