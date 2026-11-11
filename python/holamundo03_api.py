"""HolaMundo03 en Python. API REST de asignaciones de CPremier con Flask y PyMySQL.

Expone los mismos endpoints y el mismo JSON que las versiones de Node.js y PHP,
para que un solo cliente web pueda usar cualquiera de las tres.
Uso:  python holamundo03_api.py   y abrir http://localhost:3002
"""
import json
import os
import platform
import re
from pathlib import Path

import pymysql
from flask import Flask, jsonify, request, send_file

import config

app = Flask(__name__)
CLIENTE = Path(__file__).resolve().parent.parent / 'cliente' / 'index.html'

LISTA = """
    SELECT a.id_trabajador, a.id_edificio, CAST(a.fecha_inicio AS CHAR) AS fecha_inicio, a.num_dias,
           t.nombre AS trabajador, t.oficio, e.dir_edificio AS edificio,
           a.num_dias * 8 * t.tarifa_hr AS monto
    FROM asignacion a
    JOIN trabajador t ON t.id_trabajador = a.id_trabajador
    JOIN edificio e ON e.id_edificio = a.id_edificio
    WHERE t.nombre LIKE %s
    ORDER BY a.fecha_inicio, t.nombre"""


def consultar(sql, parametros=(), escribir=False):
    """Abre una conexión, ejecuta el SQL con sus parámetros y la cierra. Devuelve filas o filas afectadas."""
    conexion = pymysql.connect(host=config.HOST, port=config.PUERTO, user=config.USUARIO, password=config.CLAVE or '',
                               database=config.BASE, cursorclass=pymysql.cursors.DictCursor)
    try:
        with conexion.cursor() as cursor:
            afectadas = cursor.execute(sql, parametros)
            if escribir:
                conexion.commit()   # PyMySQL no confirma solo, hay que hacer commit
                return afectadas
            return cursor.fetchall()
    finally:
        conexion.close()


def validar(datos, solo_dias=False):
    """Revisa los datos antes de tocar la base. Devuelve un mensaje si algo está mal, o None si todo bien."""
    dias = datos.get('num_dias')
    if type(dias) is not int or not 1 <= dias <= 365:
        return 'num_dias debe ser un entero entre 1 y 365'
    if solo_dias:
        return None
    if type(datos.get('id_trabajador')) is not int or type(datos.get('id_edificio')) is not int:
        return 'id_trabajador e id_edificio deben ser enteros'
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(datos.get('fecha_inicio') or '')):
        return 'fecha_inicio debe tener el formato AAAA-MM-DD'
    return None


@app.after_request
def cors(respuesta):
    """CORS. Permite que la página servida por otro back-end (otro puerto) llame a esta API."""
    respuesta.headers['Access-Control-Allow-Origin'] = '*'
    respuesta.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    respuesta.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return respuesta


@app.errorhandler(pymysql.MySQLError)
def error_de_base(error):
    """Convierte un error de MySQL en una respuesta HTTP con sentido."""
    codigo = error.args[0]
    if codigo == 1062:
        return jsonify(error='Esa asignación ya existe'), 409
    if codigo == 1452:
        return jsonify(error='El trabajador o el edificio no existe'), 400
    if codigo == 1292:
        return jsonify(error='La fecha no es válida'), 400
    app.logger.error(error)
    return jsonify(error='Error interno al consultar la base'), 500


@app.errorhandler(404)
def no_encontrada(_error):
    return jsonify(error='Ruta no encontrada'), 404


@app.get('/')
def cliente():
    return send_file(CLIENTE)   # el cliente web es el mismo archivo para los tres lenguajes


@app.get('/api/info')
def info():
    return jsonify(lenguaje='Python', entorno=f'Python {platform.python_version()}', driver='PyMySQL', framework='Flask')


@app.get('/api/trabajadores')
def trabajadores():
    return jsonify(consultar('SELECT id_trabajador, nombre, oficio FROM trabajador ORDER BY nombre'))


@app.get('/api/edificios')
def edificios():
    return jsonify(consultar('SELECT id_edificio, dir_edificio FROM edificio ORDER BY dir_edificio'))


SQL_COLUMNAS = """
    SELECT TABLE_NAME AS tabla, COLUMN_NAME AS columna, COLUMN_TYPE AS tipo, COLUMN_KEY AS llave
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
    ORDER BY TABLE_NAME, ORDINAL_POSITION"""
SQL_RELACIONES = """
    SELECT TABLE_NAME AS tabla, COLUMN_NAME AS columna,
           REFERENCED_TABLE_NAME AS ref_tabla, REFERENCED_COLUMN_NAME AS ref_columna
    FROM information_schema.KEY_COLUMN_USAGE
    WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL
    ORDER BY TABLE_NAME, COLUMN_NAME"""


@app.get('/api/esquema')
def esquema():
    """Esquema de la base, leído del catálogo information_schema. Con esto el cliente dibuja el diagrama ER."""
    return jsonify(columnas=consultar(SQL_COLUMNAS), relaciones=consultar(SQL_RELACIONES))


@app.get('/api/asignaciones')   # READ
def listar():
    filas = consultar(LISTA, (f"%{request.args.get('buscar', '')}%",))
    for fila in filas:
        fila['monto'] = float(fila['monto'])   # Decimal no se puede mandar como JSON
    return jsonify(filas)


@app.post('/api/asignaciones')   # CREATE
def crear():
    datos = request.get_json(silent=True) or {}
    error = validar(datos)
    if error:
        return jsonify(error=error), 400
    campos = ('id_trabajador', 'id_edificio', 'fecha_inicio', 'num_dias')
    consultar('INSERT INTO asignacion (id_trabajador, id_edificio, fecha_inicio, num_dias) VALUES (%s, %s, %s, %s)',
              tuple(datos[c] for c in campos), escribir=True)
    return jsonify({c: datos[c] for c in campos}), 201


@app.put('/api/asignaciones/<int:t>/<int:e>/<f>')   # UPDATE. La llave va en la URL y el dato nuevo en el cuerpo.
def actualizar(t, e, f):
    datos = request.get_json(silent=True) or {}
    error = validar(datos, solo_dias=True)
    if error:
        return jsonify(error=error), 400
    # Primero se comprueba que exista, porque MySQL reporta 0 filas cambiadas si el valor nuevo es igual al anterior.
    llave = 'id_trabajador = %s AND id_edificio = %s AND fecha_inicio = %s'
    if not consultar(f'SELECT 1 FROM asignacion WHERE {llave}', (t, e, f)):
        return jsonify(error='No existe esa asignación'), 404
    consultar(f'UPDATE asignacion SET num_dias = %s WHERE {llave}', (datos['num_dias'], t, e, f), escribir=True)
    return jsonify(num_dias=datos['num_dias'])


@app.delete('/api/asignaciones/<int:t>/<int:e>/<f>')   # DELETE
def borrar(t, e, f):
    afectadas = consultar('DELETE FROM asignacion WHERE id_trabajador = %s AND id_edificio = %s AND fecha_inicio = %s',
                          (t, e, f), escribir=True)
    if afectadas == 0:
        return jsonify(error='No existe esa asignación'), 404
    return '', 204


@app.get('/api/demo/inyeccion')
def demo_inyeccion():
    """Demostración de inyección de SQL. El modo "concatenada" es vulnerable A PROPÓSITO y solo hace un SELECT.

    Nunca se debe escribir así una consulta real.
    """
    oficio = request.args.get('oficio', '')
    base = 'SELECT nombre, oficio, tarifa_hr FROM trabajador WHERE oficio = '
    if request.args.get('modo') == 'concatenada':
        sql = f"{base}'{oficio}'"                       # el texto del usuario se vuelve parte del SQL
        try:
            # En PyMySQL el % es especial, así que se duplica para mandar el texto tal cual.
            filas = consultar(sql.replace('%', '%%'))
        except pymysql.MySQLError as error:
            filas = [{'error_sql': str(error.args[-1])}]
        modo = 'concatenada'
    else:
        filas = consultar(base + '%s', (oficio,))        # el valor viaja aparte
        sql = f'{base}?   ← parámetro: {json.dumps(oficio, ensure_ascii=False)}'
        modo = 'parametrizada'
    for fila in filas:
        if 'tarifa_hr' in fila:
            fila['tarifa_hr'] = str(fila['tarifa_hr'])
    return jsonify(modo=modo, sql=sql, filas=filas)


if __name__ == '__main__':
    if not config.USUARIO:
        raise SystemExit('Falta DB_USER. Copia .env.example como .env y llena tus datos.')
    app.run(host='127.0.0.1', port=int(os.environ.get('API_PORT', '3002')))
