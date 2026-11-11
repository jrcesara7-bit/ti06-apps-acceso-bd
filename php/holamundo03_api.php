<?php
// HolaMundo03 en PHP. API REST de asignaciones de CPremier con PDO, sin framework.
// Expone los mismos endpoints y el mismo JSON que las versiones de Node.js y Python,
// para que un solo cliente web pueda usar cualquiera de las tres.
// Uso:  php -S localhost:3003 holamundo03_api.php   y abrir http://localhost:3003
declare(strict_types=1);
require __DIR__ . '/config.php';

// CORS. Permite que la página servida por otro back-end (otro puerto) llame a esta API.
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

$metodo = $_SERVER['REQUEST_METHOD'];
$ruta = rawurldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
if ($metodo === 'OPTIONS') {
    http_response_code(204);
    exit;
}
if ($ruta === '/') {   // el cliente web es el mismo archivo para los tres lenguajes
    header('Content-Type: text/html; charset=utf-8');
    readfile(__DIR__ . '/../cliente/index.html');
    exit;
}

// Termina la petición con un código HTTP y un cuerpo JSON.
function responder(int $codigo, mixed $datos = null): never
{
    http_response_code($codigo);
    if ($datos !== null) {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode($datos, JSON_UNESCAPED_UNICODE);
    }
    exit;
}

// Revisa los datos antes de tocar la base. Devuelve un mensaje si algo está mal, o null si todo bien.
function validar(array $d, bool $soloDias = false): ?string
{
    $dias = $d['num_dias'] ?? null;
    if (!is_int($dias) || $dias < 1 || $dias > 365) return 'num_dias debe ser un entero entre 1 y 365';
    if ($soloDias) return null;
    if (!is_int($d['id_trabajador'] ?? null) || !is_int($d['id_edificio'] ?? null)) return 'id_trabajador e id_edificio deben ser enteros';
    if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', (string) ($d['fecha_inicio'] ?? ''))) return 'fecha_inicio debe tener el formato AAAA-MM-DD';
    return null;
}

const LISTA = "
    SELECT a.id_trabajador, a.id_edificio, CAST(a.fecha_inicio AS CHAR) AS fecha_inicio, a.num_dias,
           t.nombre AS trabajador, t.oficio, e.dir_edificio AS edificio,
           a.num_dias * 8 * t.tarifa_hr AS monto
    FROM asignacion a
    JOIN trabajador t ON t.id_trabajador = a.id_trabajador
    JOIN edificio e ON e.id_edificio = a.id_edificio
    WHERE t.nombre LIKE ?
    ORDER BY a.fecha_inicio, t.nombre";
const LLAVE = 'id_trabajador = ? AND id_edificio = ? AND fecha_inicio = ?';

$cuerpo = json_decode(file_get_contents('php://input') ?: '', true);
$cuerpo = is_array($cuerpo) ? $cuerpo : [];

try {
    $pdo = conectar((string) cfg('DB_USER', ''), (string) cfg('DB_PASSWORD', ''));

    if ($metodo === 'GET' && $ruta === '/api/info') {
        responder(200, ['lenguaje' => 'PHP', 'entorno' => 'PHP ' . PHP_VERSION, 'driver' => 'pdo_mysql', 'framework' => 'Ninguno, PDO directo']);
    }
    if ($metodo === 'GET' && $ruta === '/api/trabajadores') {
        responder(200, $pdo->query('SELECT id_trabajador, nombre, oficio FROM trabajador ORDER BY nombre')->fetchAll());
    }
    if ($metodo === 'GET' && $ruta === '/api/edificios') {
        responder(200, $pdo->query('SELECT id_edificio, dir_edificio FROM edificio ORDER BY dir_edificio')->fetchAll());
    }

    // Esquema de la base, leído del catálogo information_schema. Con esto el cliente dibuja el diagrama ER.
    if ($metodo === 'GET' && $ruta === '/api/esquema') {
        $columnas = $pdo->query(
            'SELECT TABLE_NAME AS tabla, COLUMN_NAME AS columna, COLUMN_TYPE AS tipo, COLUMN_KEY AS llave
             FROM information_schema.COLUMNS
             WHERE TABLE_SCHEMA = DATABASE()
             ORDER BY TABLE_NAME, ORDINAL_POSITION')->fetchAll();
        $relaciones = $pdo->query(
            'SELECT TABLE_NAME AS tabla, COLUMN_NAME AS columna,
                    REFERENCED_TABLE_NAME AS ref_tabla, REFERENCED_COLUMN_NAME AS ref_columna
             FROM information_schema.KEY_COLUMN_USAGE
             WHERE TABLE_SCHEMA = DATABASE() AND REFERENCED_TABLE_NAME IS NOT NULL
             ORDER BY TABLE_NAME, COLUMN_NAME')->fetchAll();
        responder(200, ['columnas' => $columnas, 'relaciones' => $relaciones]);
    }

    // READ
    if ($metodo === 'GET' && $ruta === '/api/asignaciones') {
        $c = $pdo->prepare(LISTA);
        $c->execute(['%' . ($_GET['buscar'] ?? '') . '%']);
        $filas = array_map(fn($f) => ['monto' => (float) $f['monto']] + $f, $c->fetchAll());   // DECIMAL llega como texto
        responder(200, $filas);
    }

    // CREATE
    if ($metodo === 'POST' && $ruta === '/api/asignaciones') {
        if ($error = validar($cuerpo)) responder(400, ['error' => $error]);
        $datos = [$cuerpo['id_trabajador'], $cuerpo['id_edificio'], $cuerpo['fecha_inicio'], $cuerpo['num_dias']];
        $pdo->prepare('INSERT INTO asignacion (id_trabajador, id_edificio, fecha_inicio, num_dias) VALUES (?, ?, ?, ?)')->execute($datos);
        responder(201, array_combine(['id_trabajador', 'id_edificio', 'fecha_inicio', 'num_dias'], $datos));
    }

    // UPDATE y DELETE. La llave de la asignación va en la URL, por ejemplo /api/asignaciones/1412/111/2024-10-01
    if (preg_match('#^/api/asignaciones/(\d+)/(\d+)/([^/]+)$#', $ruta, $m)) {
        $llave = [(int) $m[1], (int) $m[2], $m[3]];
        if ($metodo === 'PUT') {
            if ($error = validar($cuerpo, true)) responder(400, ['error' => $error]);
            // Primero se comprueba que exista, porque MySQL reporta 0 filas cambiadas si el valor nuevo es igual al anterior.
            $existe = $pdo->prepare('SELECT 1 FROM asignacion WHERE ' . LLAVE);
            $existe->execute($llave);
            if (!$existe->fetch()) responder(404, ['error' => 'No existe esa asignación']);
            $pdo->prepare('UPDATE asignacion SET num_dias = ? WHERE ' . LLAVE)->execute([$cuerpo['num_dias'], ...$llave]);
            responder(200, ['num_dias' => $cuerpo['num_dias']]);
        }
        if ($metodo === 'DELETE') {
            $c = $pdo->prepare('DELETE FROM asignacion WHERE ' . LLAVE);
            $c->execute($llave);
            if ($c->rowCount() === 0) responder(404, ['error' => 'No existe esa asignación']);
            responder(204);
        }
    }

    // Demostración de inyección de SQL. El modo "concatenada" es vulnerable A PROPÓSITO y solo hace un SELECT.
    // Nunca se debe escribir así una consulta real.
    if ($metodo === 'GET' && $ruta === '/api/demo/inyeccion') {
        $oficio = (string) ($_GET['oficio'] ?? '');
        $base = 'SELECT nombre, oficio, tarifa_hr FROM trabajador WHERE oficio = ';
        if (($_GET['modo'] ?? '') === 'concatenada') {
            $sql = $base . "'" . $oficio . "'";                 // el texto del usuario se vuelve parte del SQL
            try {
                $filas = $pdo->query($sql)->fetchAll();
            } catch (PDOException $ex) {
                $filas = [['error_sql' => $ex->errorInfo[2] ?? $ex->getMessage()]];
            }
            responder(200, ['modo' => 'concatenada', 'sql' => $sql, 'filas' => $filas]);
        }
        $c = $pdo->prepare($base . '?');                        // el valor viaja aparte
        $c->execute([$oficio]);
        responder(200, ['modo' => 'parametrizada',
            'sql' => $base . '?   ← parámetro: ' . json_encode($oficio, JSON_UNESCAPED_UNICODE), 'filas' => $c->fetchAll()]);
    }

    responder(404, ['error' => 'Ruta no encontrada']);
} catch (PDOException $ex) {
    // Convierte un error de MySQL en una respuesta HTTP con sentido.
    $codigo = $ex->errorInfo[1] ?? 0;
    if ($codigo === 1062) responder(409, ['error' => 'Esa asignación ya existe']);
    if ($codigo === 1452) responder(400, ['error' => 'El trabajador o el edificio no existe']);
    if ($codigo === 1292) responder(400, ['error' => 'La fecha no es válida']);
    error_log($ex->getMessage());
    responder(500, ['error' => 'Error interno al consultar la base']);
}
