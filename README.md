# TI06 · Prototipos HolaMundo de acceso a BD

Julio Cesar Ruiz Alfaro · Base de Datos · Ingeniería de Software 3° E · Universidad de Colima

Tres lenguajes (JavaScript, Python y PHP) y tres programas por lenguaje sobre la base CPremier en MySQL.

| Programa | JavaScript | Python | PHP |
|---|---|---|---|
| HolaMundo01, conexión y SELECT | consola | consola | consola |
| HolaMundo02, usuario, contraseña y consulta | web con Express | escritorio con Tkinter | web con PDO |
| HolaMundo03 (extra), API REST con CRUD | Express | Flask | PDO sin framework |

El HolaMundo03 es la misma API escrita tres veces. La carpeta `/cliente` tiene una sola página web que puede usar
cualquiera de las tres con un botón, y `/pruebas` trae un script que comprueba que las tres responden igual.

Los nueve usan consultas parametrizadas y ninguno trae credenciales en el código.

| CRUD y bitácora HTTP | Diagrama ER leído de la base |
|---|---|
| ![Asignaciones](docs/img/01_asignaciones.png) | ![Diagrama ER](docs/img/02_diagrama_er.png) |
| **Inyección de SQL, lado a lado** | **Comparación de los tres back-ends** |
| ![Inyección de SQL](docs/img/03_inyeccion_sql.png) | ![Comparar back-ends](docs/img/04_comparar_backends.png) |

## Requisitos

Lo probé en Linux. En Windows y macOS los pasos son los mismos, con las diferencias que se marcan en cada paso.

| Qué | Versión mínima | Probado con | Notas |
|---|---|---|---|
| MySQL o MariaDB | MySQL 8 o MariaDB 10.5 | MariaDB 10.11 | Hace falta un usuario administrador para el paso 1 |
| Node.js | 22.9 | 22.22 | Solo para la carpeta `javascript` |
| Python | 3.10 | 3.14 | Solo para `python` y para la prueba de contrato |
| PHP | 8.3 | 8.3 | Solo para `php`, con las extensiones `pdo_mysql` y `mbstring` |

No hace falta instalar los tres lenguajes. Cada carpeta funciona por separado.

- En Linux, Tkinter se instala aparte (`sudo apt install python3-tk` o `sudo dnf install python3-tkinter`).
- En Windows, las extensiones de PHP se activan quitando el `;` de `extension=pdo_mysql` y `extension=mbstring`
  en `php.ini`. El comando `php -m` muestra las que están activas.
- Si `python` no existe en tu sistema, usa `python3` (Linux y macOS) o `py` (Windows).

Todos los comandos se escriben en una terminal abierta en la carpeta `prototipos`, salvo que el paso diga otra.

## 1. Preparar la base de datos

Entra al cliente de MySQL como administrador.

```bash
mysql -u root -p
```

Dentro del cliente, crea la base, carga las tablas y crea los dos usuarios. Cambia las contraseñas por las tuyas.

```sql
CREATE DATABASE cpremier;
USE cpremier;
SOURCE sql/cpremier.sql;

CREATE USER 'alumno'@'%' IDENTIFIED BY 'elige_una_contraseña';
GRANT SELECT ON cpremier.* TO 'alumno'@'%';

CREATE USER 'app'@'%' IDENTIFIED BY 'elige_otra_contraseña';
GRANT SELECT ON cpremier.* TO 'app'@'%';
GRANT INSERT, UPDATE, DELETE ON cpremier.asignacion TO 'app'@'%';
```

| Usuario | Permisos | Dónde se usa |
|---|---|---|
| `alumno` | Solo lectura | Para iniciar sesión en la pantalla de HolaMundo02 |
| `app` | Lectura, y escritura en `asignacion` | En el archivo `.env`, para HolaMundo01 y HolaMundo03 |

## 2. Configurar la conexión

En cada carpeta de lenguaje que vayas a usar, copia `.env.example` como `.env`.

```bash
cp javascript/.env.example javascript/.env      # Linux y macOS
copy javascript\.env.example javascript\.env    # Windows
```

Repite lo mismo con `python` y `php`. Luego abre cada `.env` y llénalo así.

```
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=cpremier
DB_USER=app
DB_PASSWORD=la_contraseña_de_app
```

HolaMundo02 solo toma de ahí el host, el puerto y la base, porque el usuario y la contraseña se piden en pantalla.

## 3. Ejecutar

Cada servidor ocupa su terminal mientras está encendido. Se apaga con `Ctrl + C`.

### JavaScript

```bash
cd javascript
npm install
npm run hola1                 # todos los trabajadores
npm run hola1 -- Fontanero    # filtrados por oficio
npm run hola2                 # abre http://localhost:3000
npm run hola3                 # API REST en http://localhost:3001
```

### Python

```bash
cd python
python -m venv .venv
source .venv/bin/activate     # en Windows es .venv\Scripts\activate
pip install -r requirements.txt
python holamundo01.py
python holamundo01.py Fontanero
python holamundo02.py         # abre la ventana de escritorio
python holamundo03_api.py     # API REST en http://localhost:3002
```

### PHP

```bash
cd php
php holamundo01.php
php holamundo01.php Fontanero
php -S localhost:8080 holamundo02.php        # abre http://localhost:8080
php -S localhost:3003 holamundo03_api.php    # API REST en http://localhost:3003
```

## Qué hace cada programa

- **HolaMundo01** se conecta, corre un SELECT de trabajadores con el nombre de su supervisor y lo imprime como tabla.
  Acepta un oficio como argumento, que se envía como parámetro de la consulta.
- **HolaMundo02** pide usuario y contraseña y valida el acceso intentando abrir la conexión con esos datos. Si MySQL
  los rechaza, muestra el aviso (las versiones web responden con HTTP 401). Si los acepta, muestra las asignaciones con
  días y monto, y un buscador por trabajador.

## HolaMundo03, un cliente y tres back-ends

Enciende una, dos o las tres APIs y abre cualquiera de ellas en el navegador,
por ejemplo http://localhost:3001. La página permite:

- Cambiar de back-end con los botones Node.js, Python y PHP. La pantalla sigue igual porque las tres APIs
  exponen los mismos endpoints y devuelven el mismo JSON.
- Hacer el CRUD completo de asignaciones (alta, cambio de días, baja y búsqueda), con totales al momento.
- Ver el diagrama entidad-relación de la base. La API lo lee de `information_schema` y las tablas se pueden arrastrar.
- Comparar los tres back-ends. Mide el tiempo de respuesta de cada uno y revisa que devuelvan el mismo JSON.
- Cambiar entre tema claro y oscuro.
- Ver en la bitácora cada solicitud HTTP con su método, ruta, código y tiempo.
- Probar la inyección de SQL. El mismo texto se manda a una consulta concatenada y a una parametrizada.

| Método y ruta | Qué hace | Códigos |
|---|---|---|
| GET /api/info | Lenguaje, framework y driver del back-end | 200 |
| GET /api/trabajadores, GET /api/edificios | Catálogos para el formulario | 200 |
| GET /api/esquema | Columnas y llaves foráneas, leídas de information_schema | 200 |
| GET /api/asignaciones?buscar= | Lista con monto, filtrada por trabajador | 200 |
| POST /api/asignaciones | Crea una asignación | 201, 400, 409 |
| PUT /api/asignaciones/{trabajador}/{edificio}/{fecha} | Cambia los días | 200, 400, 404 |
| DELETE /api/asignaciones/{trabajador}/{edificio}/{fecha} | Borra | 204, 404 |
| GET /api/demo/inyeccion?modo=&oficio= | Demostración de inyección | 200 |

### Prueba de contrato

Con las tres APIs encendidas, desde la carpeta `prototipos`. No necesita instalar nada, solo Python.

```bash
python pruebas/probar_apis.py
```

Corre 15 comprobaciones en cada back-end y verifica que los tres devuelvan el mismo JSON en la lista y en el
esquema. Crea una asignación de prueba y la borra al terminar.

La ruta `/api/demo/inyeccion` con `modo=concatenada` es vulnerable a propósito, solo hace un SELECT y existe para
enseñar el problema. La API no pide inicio de sesión y escucha solo en `localhost`.

## Problemas comunes

| Mensaje | Causa | Solución |
|---|---|---|
| `Falta DB_USER` | No existe el `.env` en esa carpeta | Repetir el paso 2 |
| `Access denied for user` | Usuario o contraseña incorrectos | Revisar el `.env` o lo que se escribió en pantalla |
| `ECONNREFUSED` o `Can't connect` | El servidor de BD está apagado o el puerto es otro | Encender MySQL y revisar `DB_HOST` y `DB_PORT` |
| `EADDRINUSE` o `Address already in use` | El puerto ya lo ocupa otro programa | Cerrar el otro programa o la terminal anterior |
| `could not find driver` | PHP sin `pdo_mysql` | Activar la extensión en `php.ini` |
| `No module named tkinter` | Falta Tkinter en Linux | Instalar el paquete que aparece en Requisitos |
| El cliente web marca un back-end sin conexión | Esa API no está encendida | Encenderla o elegir otro back-end |

## Seguridad

- Consultas parametrizadas en todos los casos (`?` en mysql2, `%s` en PyMySQL, `:nombre` en PDO).
- Sin credenciales en el código. El archivo `.env` no se entrega.
- En las versiones web la contraseña queda en la sesión del servidor, la cookie es `HttpOnly` y la salida HTML se escapa.
- Son prototipos de clase. Para producción faltaría HTTPS, protección CSRF y un almacén de sesiones persistente.
