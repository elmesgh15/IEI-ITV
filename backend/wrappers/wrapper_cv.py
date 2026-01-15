from fastapi import APIRouter
from backend.models import WrapperResponse

router = APIRouter()

@router.post("/cargar", response_model=WrapperResponse)
def ejecutar_carga_cv():

    from backend.extractores.extractor_cv import procesar_datos_cv
    
    try:

        resultado = procesar_datos_cv()
        
        return {
            'success': True,
            'insertados': resultado.get('insertados', 0),
            'descartados': resultado.get('descartados', 0),
            'log': str(resultado.get('log', '') or '')
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'insertados': 0,
            'descartados': 0,
            'log': str(e)
        }
