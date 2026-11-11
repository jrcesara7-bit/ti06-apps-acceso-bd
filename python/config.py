"""Lee los datos de conexión de variables de entorno o de un archivo .env. Nada va escrito en el código."""
import os
from pathlib import Path


def cargar_env(ruta=Path(__file__).with_name('.env')):
    """Carga pares CLAVE=valor de un .env sencillo, sin pisar lo que ya esté en el entorno."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding='utf-8').splitlines():
        linea = linea.strip()
        if linea and not linea.startswith('#') and '=' in linea:
            clave, valor = linea.split('=', 1)
            os.environ.setdefault(clave.strip(), valor.strip())


cargar_env()
HOST = os.environ.get('DB_HOST', '127.0.0.1')
PUERTO = int(os.environ.get('DB_PORT', '3306'))
BASE = os.environ.get('DB_NAME', 'cpremier')
USUARIO = os.environ.get('DB_USER')
CLAVE = os.environ.get('DB_PASSWORD')
