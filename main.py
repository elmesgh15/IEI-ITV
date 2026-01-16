# main.py
import sys
import threading
import time
from PySide6.QtWidgets import QApplication
from frontend.main_window import MainWindow

def iniciar_servidor_main():
    """Inicia el servidor FastAPI principal en el puerto 8000"""
    import uvicorn
    from backend.server import app
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    server.run()

def iniciar_wrapper_cv():
    """Inicia el wrapper de Valencia en el puerto 8001"""
    import uvicorn
    from backend.wrapper_server_cv import app
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8001, log_level="info")
    server = uvicorn.Server(config)
    server.run()

def iniciar_wrapper_gal():
    """Inicia el wrapper de Galicia en el puerto 8002"""
    import uvicorn
    from backend.wrapper_server_gal import app
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8002, log_level="info")
    server = uvicorn.Server(config)
    server.run()

def iniciar_wrapper_cat():
    """Inicia el wrapper de Cataluña en el puerto 8003"""
    import uvicorn
    from backend.wrapper_server_cat import app
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8003, log_level="info")
    server = uvicorn.Server(config)
    server.run()

if __name__ == "__main__":
    # Iniciar servidores en hilos separados
    threads = [
        threading.Thread(target=iniciar_servidor_main, daemon=True),
        threading.Thread(target=iniciar_wrapper_cv, daemon=True),
        threading.Thread(target=iniciar_wrapper_gal, daemon=True),
        threading.Thread(target=iniciar_wrapper_cat, daemon=True)
    ]
    
    for t in threads:
        t.start()
    
    # Esperar un momento para que los servidores se inicien
    print("Iniciando servidores FastAPI...")
    time.sleep(3)
    print("Servidores iniciados:")
    print("- Main API: http://127.0.0.1:8000")
    print("- Wrapper CV: http://127.0.0.1:8001")
    print("- Wrapper GAL: http://127.0.0.1:8002")
    print("- Wrapper CAT: http://127.0.0.1:8003")
    
    # Iniciar aplicación Qt
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())
