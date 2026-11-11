"""Prueba de contrato. Corre las mismas 15 comprobaciones contra los tres back-ends y compara sus respuestas.

Solo usa la biblioteca estándar. Crea una asignación de prueba y la borra al final.
Uso:  python probar_apis.py
"""
import json
import urllib.error
import urllib.request

BACKENDS = {'Node.js': 'http://127.0.0.1:3001', 'Python': 'http://127.0.0.1:3002', 'PHP': 'http://127.0.0.1:3003'}
NUEVA = {'id_trabajador': 1235, 'id_edificio': 111, 'fecha_inicio': '2025-01-15', 'num_dias': 3}
LLAVE = '/api/asignaciones/1235/111/2025-01-15'


def llamar(base, metodo, ruta, cuerpo=None):
    """Devuelve (código HTTP, JSON o None)."""
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pedido = urllib.request.Request(base + ruta, data=datos, method=metodo, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(pedido, timeout=10) as r:
            texto = r.read().decode()
            return r.status, json.loads(texto) if texto else None
    except urllib.error.HTTPError as e:
        texto = e.read().decode()
        return e.code, json.loads(texto) if texto else None


def probar(base):
    """Lista de (descripción, esperado, obtenido) para un back-end."""
    inyeccion = "/api/demo/inyeccion?oficio=x%27%20OR%20%271%27%3D%271&modo="
    casos = [
        ('GET lista completa', 200, llamar(base, 'GET', '/api/asignaciones')[0]),
        ('GET esquema de la base', 200, llamar(base, 'GET', '/api/esquema')[0]),
        ('GET ruta inexistente', 404, llamar(base, 'GET', '/api/nada')[0]),
        ('POST con días inválidos', 400, llamar(base, 'POST', '/api/asignaciones', {**NUEVA, 'num_dias': 0})[0]),
        ('POST con fecha imposible', 400, llamar(base, 'POST', '/api/asignaciones', {**NUEVA, 'fecha_inicio': '2025-13-45'})[0]),
        ('POST con trabajador que no existe', 400, llamar(base, 'POST', '/api/asignaciones', {**NUEVA, 'id_trabajador': 9999})[0]),
        ('POST correcto', 201, llamar(base, 'POST', '/api/asignaciones', NUEVA)[0]),
        ('POST repetido', 409, llamar(base, 'POST', '/api/asignaciones', NUEVA)[0]),
        ('PUT cambia los días', 200, llamar(base, 'PUT', LLAVE, {'num_dias': 9})[0]),
        ('PUT con el mismo valor', 200, llamar(base, 'PUT', LLAVE, {'num_dias': 9})[0]),
        ('PUT a una que no existe', 404, llamar(base, 'PUT', '/api/asignaciones/1235/111/1999-01-01', {'num_dias': 9})[0]),
        ('DELETE correcto', 204, llamar(base, 'DELETE', LLAVE)[0]),
        ('DELETE repetido', 404, llamar(base, 'DELETE', LLAVE)[0]),
        ('Inyección concatenada devuelve todo', 7, len(llamar(base, 'GET', inyeccion + 'concatenada')[1]['filas'])),
        ('Inyección parametrizada no devuelve nada', 0, len(llamar(base, 'GET', inyeccion + 'parametrizada')[1]['filas'])),
    ]
    return casos


def main():
    fallas, listas = 0, {}
    for nombre, base in BACKENDS.items():
        print(f'\n== {nombre} ({base})')
        try:
            casos = probar(base)
        except (urllib.error.URLError, OSError) as error:
            print(f'   sin respuesta: {error}')
            fallas += 1
            continue
        for descripcion, esperado, obtenido in casos:
            bien = esperado == obtenido
            fallas += not bien
            print(f"   {'OK   ' if bien else 'FALLA'} {descripcion:<42} esperado {esperado}, obtenido {obtenido}")
        listas[nombre] = [llamar(base, 'GET', '/api/asignaciones')[1], llamar(base, 'GET', '/api/esquema')[1]]
    iguales = len(listas) == len(BACKENDS) and all(l == listas['Node.js'] for l in listas.values())
    fallas += not iguales
    print(f"\n{'OK   ' if iguales else 'FALLA'} Los tres back-ends devuelven exactamente el mismo JSON en la lista y en el esquema")
    print('Resultado:', 'todo correcto' if fallas == 0 else f'{fallas} falla(s)')
    raise SystemExit(1 if fallas else 0)


if __name__ == '__main__':
    main()
