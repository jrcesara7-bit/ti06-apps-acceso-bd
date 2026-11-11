<?php
// Lee los datos de conexión de variables de entorno o de un archivo .env. Nada va escrito en el código.
declare(strict_types=1);

$archivo = __DIR__ . '/.env';
$env = is_file($archivo) ? (parse_ini_file($archivo, false, INI_SCANNER_RAW) ?: []) : [];

function cfg(string $clave, ?string $defecto = null): ?string
{
    global $env;
    $valor = getenv($clave);
    return $valor !== false ? $valor : ($env[$clave] ?? $defecto);
}

// Abre la conexión con PDO. Si las credenciales son incorrectas lanza una PDOException.
function conectar(string $usuario, string $clave): PDO
{
    $dsn = sprintf('mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
        cfg('DB_HOST', '127.0.0.1'), cfg('DB_PORT', '3306'), cfg('DB_NAME', 'cpremier'));
    return new PDO($dsn, $usuario, $clave, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,   // sentencias preparadas reales en el servidor
    ]);
}
