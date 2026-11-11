<?php
// HolaMundo01 en PHP. Se conecta a MySQL con PDO, ejecuta un SELECT y muestra los registros en consola.
// Uso:  php holamundo01.php              lista a todos los trabajadores
//       php holamundo01.php Fontanero    filtra por oficio (el valor viaja como parámetro)
declare(strict_types=1);
require __DIR__ . '/config.php';

$usuario = cfg('DB_USER');
if (!$usuario) {
    fwrite(STDERR, "Falta DB_USER. Copia .env.example como .env y llena tus datos.\n");
    exit(1);
}
$oficio = $argv[1] ?? '%';

try {
    $pdo = conectar($usuario, cfg('DB_PASSWORD', ''));
    printf("Conectado a %s en %s:%s como %s\n", cfg('DB_NAME', 'cpremier'), cfg('DB_HOST', '127.0.0.1'),
        cfg('DB_PORT', '3306'), $usuario);
    // prepare() separa el SQL de los datos. El valor de :oficio no puede alterar la consulta.
    $consulta = $pdo->prepare(
        'SELECT t.id_trabajador, t.nombre, t.oficio, t.tarifa_hr, s.nombre AS supervisor
         FROM trabajador t
         LEFT JOIN trabajador s ON s.id_trabajador = t.id_supv
         WHERE t.oficio LIKE :oficio
         ORDER BY t.nombre');
    $consulta->execute(['oficio' => $oficio]);
    $filas = $consulta->fetchAll();
} catch (PDOException $error) {
    fwrite(STDERR, 'No se pudo consultar la base: ' . $error->getMessage() . "\n");
    exit(1);
}

// Tabla alineada, con el ancho de cada columna calculado según los datos.
$columnas = $filas ? array_keys($filas[0]) : [];
$anchos = [];
foreach ($columnas as $c) {
    $anchos[$c] = max(mb_strlen($c), ...array_map(fn($f) => mb_strlen((string) $f[$c]), $filas));
}
$linea = '+' . implode('+', array_map(fn($a) => str_repeat('-', $a + 2), $anchos)) . "+\n";
$renglon = fn(array $v) => '|' . implode('|', array_map(
    fn($c) => ' ' . mb_str_pad((string) $v[$c], $anchos[$c]) . ' ', $columnas)) . "|\n";
if ($filas) {
    echo $linea, $renglon(array_combine($columnas, $columnas)), $linea;
    foreach ($filas as $fila) {
        echo $renglon($fila);
    }
    echo $linea;
}
echo count($filas), " registro(s)\n";
$pdo = null;   // cierra la conexión
