from io import StringIO
import sys

def ejecutar_carga_cat():
    """
    Wrapper para ejecutar la carga de datos de Catalunya.
    Captura la salida y devuelve un diccionario con los resultados.
    """
    # Importar el extractor
    from backend.extractores.extractor_cat import procesar_datos_cat
    
    # Capturar stdout para obtener los logs
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    contadores = {
        'insertados': 0,
        'descartados': 0,
        'cp': 0,
        'coordenadas': 0,
        'nombre': 0,
        'provincia': 0,
        'datos': 0
    }
    
    try:
        # Ejecutar el procesamiento
        procesar_datos_cat()
        
        # Obtener la salida capturada
        output = captured_output.getvalue()
        
        # Parsear los contadores del output
        for line in output.split('\n'):
            if 'Se han insertado :' in line and 'correctamente' in line:
                try:
                    contadores['insertados'] = int(line.split(':')[1].split('correctamente')[0].strip())
                except:
                    pass
            elif 'Se han descartado :' in line and '.' in line:
                try:
                    num = line.split(':')[1].split('.')[0].strip()
                    if num.isdigit():
                        contadores['descartados'] = int(num)
                except:
                    pass
        
        return {
            'success': True,
            'insertados': contadores['insertados'],
            'descartados': contadores['descartados'],
            'log': output
        }
    
    except Exception as e:
        output = captured_output.getvalue()
        return {
            'success': False,
            'error': str(e),
            'insertados': 0,
            'descartados': 0,
            'log': output
        }
    
    finally:
        sys.stdout = old_stdout
